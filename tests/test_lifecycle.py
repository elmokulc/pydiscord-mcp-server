import asyncio

import pytest
from conftest import make_client

from pydiscord_mcp_server.discord_client import DiscordRuntime, create_client
from pydiscord_mcp_server.errors import DiscordToolError


def connected_runtime(settings):
    client = make_client()
    client.is_ready.return_value = False

    async def connect(token, *, reconnect):
        assert token == "fake-test-token"
        assert reconnect is True
        client.is_ready.return_value = True
        await asyncio.Event().wait()

    client.start.side_effect = connect
    return DiscordRuntime(settings, client)


async def test_start_once_and_close(settings):
    runtime = connected_runtime(settings)
    await runtime.start()
    assert runtime.ready
    with pytest.raises(RuntimeError, match="once"):
        await runtime.start()
    runtime.client.start.assert_awaited_once()
    await runtime.close()
    runtime.client.close.assert_awaited_once()
    assert not runtime.ready
    assert runtime.task.done()
    assert not runtime.failed.is_set()


async def test_start_failure_observed_and_secret_not_logged(settings, caplog):
    client = make_client()
    client.is_ready.return_value = False
    client.start.side_effect = RuntimeError("sensitive-token-value")
    runtime = DiscordRuntime(settings, client)
    with pytest.raises(DiscordToolError, match="DISCORD_UNAVAILABLE"):
        await runtime.start()
    assert runtime.failed.is_set()
    assert not runtime.ready
    assert "sensitive-token-value" not in caplog.text
    assert "RuntimeError" in caplog.text
    client.close.assert_awaited_once()


async def test_start_timeout_closes_client(settings):
    settings.discord_ready_timeout = 0.01
    runtime = connected_runtime(settings)
    runtime.client.gateway_connected = False
    with pytest.raises(TimeoutError):
        await runtime.start()
    assert runtime.task.done()
    runtime.client.close.assert_awaited_once()


async def test_disconnect_readiness_and_reconnect_wait(settings):
    runtime = connected_runtime(settings)
    await runtime.start()
    settings.discord_ready_timeout = 0.01
    runtime.client.gateway_connected = False
    assert not runtime.ready
    with pytest.raises(TimeoutError):
        await runtime.wait_ready()
    runtime.client.gateway_connected = True
    await runtime.wait_ready()
    await runtime.close()


async def test_late_fatal_connection_failure(settings):
    trigger = asyncio.Event()
    client = make_client()

    async def fail_later(*args, **kwargs):
        await trigger.wait()
        raise RuntimeError("failure")

    client.start.side_effect = fail_later
    runtime = DiscordRuntime(settings, client)
    await runtime.start()
    trigger.set()
    await asyncio.wait_for(runtime.failed.wait(), timeout=1)
    assert not runtime.ready
    await runtime.close()


async def test_bot_intents_and_gateway_events(settings):
    client = create_client(settings)
    assert not client.intents.members
    assert not client.intents.message_content
    assert not client.intents.dm_messages
    assert client.allowed_mentions.to_dict() == {"parse": []}
    await client.on_ready()
    assert client.gateway_connected
    await client.on_disconnect()
    assert not client.gateway_connected
    await client.on_resumed()
    assert client.gateway_connected
