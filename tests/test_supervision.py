import asyncio
from unittest.mock import MagicMock

import pytest
from conftest import make_client

from pydiscord_mcp_server.__main__ import serve
from pydiscord_mcp_server.discord_client import DiscordRuntime
from pydiscord_mcp_server.errors import DiscordToolError
from pydiscord_mcp_server.server import create_application


async def test_failed_start_closes_only_once(settings):
    client = make_client()
    client.is_ready.return_value = False
    client.start.side_effect = RuntimeError("fake failure")
    runtime = DiscordRuntime(settings, client)
    application = create_application(settings, runtime)
    with pytest.raises(DiscordToolError):
        async with application.app.router.lifespan_context(application.app):
            pytest.fail("Startup must not succeed")
    client.close.assert_awaited_once()


async def test_fatal_bot_exit_stops_http_server(settings, monkeypatch):
    trigger = asyncio.Event()
    client = make_client()
    client.is_ready.return_value = False

    async def connect(*args, **kwargs):
        client.is_ready.return_value = True
        await trigger.wait()
        raise RuntimeError("fatal failure")

    client.start.side_effect = connect
    application = create_application(settings, DiscordRuntime(settings, client))
    monkeypatch.setattr("pydiscord_mcp_server.__main__.create_application", lambda _: application)

    class FakeServer:
        started = False

        def __init__(self):
            self.exiting = asyncio.Event()

        @property
        def should_exit(self):
            return self.exiting.is_set()

        @should_exit.setter
        def should_exit(self, value):
            if value:
                self.exiting.set()

        async def serve(self):
            async with application.app.router.lifespan_context(application.app):
                self.started = True
                trigger.set()
                await self.exiting.wait()

    server = FakeServer()
    monkeypatch.setattr(
        "pydiscord_mcp_server.__main__.uvicorn.Server", MagicMock(return_value=server)
    )
    assert await asyncio.wait_for(serve(settings), timeout=2) == 1
    assert server.should_exit
    client.close.assert_awaited_once()
