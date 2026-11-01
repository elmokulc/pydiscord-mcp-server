import asyncio
import json
from pathlib import Path
from types import MethodType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import httpx
import pytest
from conftest import make_channel, make_guild, make_message
from mcp import Client
from test_lifecycle import connected_runtime

from pydiscord_mcp_server.server import create_application
from pydiscord_mcp_server.tools.channels import register_tools

REFERENCE = json.loads((Path(__file__).parent / "fixtures/reference_tools.json").read_text())
TOOLS = set(REFERENCE["tools"]) | {
    "list_guilds",
    "get_guild_info",
    "get_member",
    "create_poll",
    "get_poll",
    "end_poll",
    "get_poll_answer_voters",
}


async def test_get_channel_info_mcp_example(access):
    from mcp.server import MCPServer

    access.client.fetch_channel.return_value = make_channel()
    mcp = MCPServer("test-channel-info")
    register_tools(mcp, access)
    async with Client(mcp) as client:
        result = await client.call_tool("get_channel_info", {"channel_id": "200"})
        assert not result.is_error
        assert result.structured_content["id"] == "200"
        assert result.structured_content["guild_id"] == "100"
    access.client.fetch_channel.assert_awaited_once_with(200)


@pytest.mark.parametrize(
    "invalid",
    [
        {"content": ""},
        {"content": "x" * 2001},
        {"allow_mentions": "false"},
        {"allow_mentions": 1},
        {"channel_id": "18446744073709551616"},
    ],
)
async def test_invalid_write_arguments_never_reach_discord(access, invalid):
    application = create_application(access.settings, access.runtime)
    async with Client(application.mcp) as client:
        result = await client.call_tool(
            "send_message", {"channel_id": "200", "content": "hello", **invalid}
        )
        assert result.is_error
    access.client.get_channel.assert_not_called()
    access.client.fetch_channel.assert_not_awaited()


async def test_registered_tools_and_structured_call(access):
    application = create_application(access.settings, access.runtime)
    access.client.guilds = [make_guild()]
    async with Client(application.mcp) as client:
        result = await client.list_tools()
        assert {t.name for t in result.tools} == TOOLS
        assert len(result.tools) == 88
        assert all(t.output_schema is not None and t.annotations is not None for t in result.tools)
        tool = next(t for t in result.tools if t.name == "get_channel_info")
        assert tool.annotations.read_only_hint is True
        assert tool.output_schema
        listing = await client.call_tool("list_guilds", {})
        assert not listing.is_error
        assert listing.structured_content["items"][0]["id"] == "100"
        invalid = await client.call_tool("read_messages", {"channel_id": "200", "limit": 101})
        assert invalid.is_error
        numeric_id = await client.call_tool("get_channel_info", {"channel_id": 200})
        assert numeric_id.is_error
        access.client.fetch_channel.assert_not_awaited()


async def test_mcp_failure_flag_and_send_default_mentions(access):
    application = create_application(access.settings, access.runtime)
    channel = make_channel()
    access.client.get_channel.return_value = channel
    channel.send.return_value = make_message()
    async with Client(application.mcp) as client:
        result = await client.call_tool("send_message", {"channel_id": "200", "content": "hello"})
        assert not result.is_error
        assert channel.send.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}
        access.settings.discord_allowed_guild_ids = ["101"]
        result = await client.call_tool("get_channel_info", {"channel_id": "200"})
        assert result.is_error
        assert "ACCESS_DENIED" in result.content[0].text


@pytest.mark.parametrize("private", [False, True], ids=["guild", "dm"])
@pytest.mark.parametrize("reply_id", [None, "299"], ids=["plain", "reply"])
@pytest.mark.parametrize("allow_mentions", [False, True])
async def test_http_send_uses_discord_message_preparation(scene, private, reply_id, allow_mentions):
    channel = scene.dm if private else scene.text
    message = scene.dm_message if private else make_message(channel=channel)
    reference = discord.MessageReference(
        message_id=299, channel_id=channel.id, guild_id=None if private else scene.guild.id
    )
    target = make_message(299, channel)
    target.to_reference.return_value = reference
    channel.fetch_message.side_effect = None
    channel.fetch_message.return_value = target

    # Exercise discord.py's real validation/serialization; only the HTTP boundary is mocked.
    send_http = AsyncMock(return_value={"id": str(message.id)})
    channel._state = SimpleNamespace(
        allowed_mentions=None,
        http=SimpleNamespace(send_message=send_http),
        create_message=MagicMock(return_value=message),
    )
    channel._get_channel = AsyncMock(return_value=channel)
    channel.send = MethodType(discord.abc.Messageable.send, channel)
    application = create_application(scene.access.settings, scene.access.runtime)
    arguments = {"content": "hello", "allow_mentions": allow_mentions}
    arguments.update({"user_id": "901"} if private else {"channel_id": "200"})
    if reply_id is not None:
        arguments["reply_to_message_id"] = reply_id

    async with (
        application.mcp.session_manager.run(),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application.app), base_url="http://localhost:8085"
        ) as client,
    ):
        response = await client.post(
            "/mcp",
            headers={"Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "send_private_message" if private else "send_message",
                    "arguments": arguments,
                },
            },
        )
    assert response.status_code == 200
    result = response.json()["result"]
    assert not result.get("isError", False), result
    assert result["structuredContent"]["id"] == str(message.id)
    send_http.assert_awaited_once()
    assert send_http.call_args.args == (channel.id,)
    payload = send_http.call_args.kwargs["params"].payload
    assert payload["content"] == "hello"
    mentions = payload["allowed_mentions"]
    assert set(mentions["parse"]) == ({"everyone", "users", "roles"} if allow_mentions else set())
    assert mentions.get("replied_user", False) is allow_mentions
    if reply_id is None:
        assert "message_reference" not in payload
        channel.fetch_message.assert_not_awaited()
    else:
        assert payload["message_reference"]["message_id"] == 299
        channel.fetch_message.assert_awaited_once_with(299)


async def test_two_clients_share_one_runtime(settings):
    runtime = connected_runtime(settings)
    runtime.client.guilds = [make_guild()]
    application = create_application(settings, runtime)
    async with application.app.router.lifespan_context(application.app):
        async with Client(application.mcp) as first, Client(application.mcp) as second:
            results = await asyncio.gather(
                first.call_tool("list_guilds", {}), second.call_tool("list_guilds", {})
            )
            assert all(not result.is_error for result in results)
            runtime.client.start.assert_awaited_once()
    runtime.client.close.assert_awaited_once()


async def test_http_health_and_stateless_mcp(settings):
    runtime = connected_runtime(settings)
    runtime.client.guilds = [make_guild()]
    application = create_application(settings, runtime)
    headers = {"Accept": "application/json, text/event-stream"}
    async with (
        application.app.router.lifespan_context(application.app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application.app), base_url="http://localhost:8085"
        ) as client,
    ):
        assert (await client.get("/health/live")).status_code == 200
        assert (await client.get("/health/ready")).status_code == 200
        initialize = await client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest", "version": "1"},
                },
            },
        )
        assert initialize.status_code == 200, initialize.text
        assert "mcp-session-id" not in initialize.headers
        headers["MCP-Protocol-Version"] = "2025-11-25"
        for ident in [2, 3]:
            result = await client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": ident,
                    "method": "tools/call",
                    "params": {"name": "list_guilds", "arguments": {}},
                },
            )
            assert result.status_code == 200, result.text
            assert result.json()["result"]["structuredContent"]["items"][0]["id"] == "100"
        runtime.client.gateway_connected = False
        assert (await client.get("/health/ready")).status_code == 503
        assert (await client.get("/health/live")).status_code == 200
        refused = await client.post(
            "/mcp", headers={**headers, "Host": "attacker.example"}, json={}
        )
        assert refused.status_code == 421
        runtime.client.start.assert_awaited_once()
    runtime.client.close.assert_awaited_once()
