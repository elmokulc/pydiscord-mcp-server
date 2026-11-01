import asyncio
from types import SimpleNamespace

import discord
import pytest

from pydiscord_mcp_server.errors import DiscordToolError, translate_errors


@pytest.mark.parametrize(
    "error,code",
    [
        (
            discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "sensitive"),
            "ACCESS_DENIED",
        ),
        (
            discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "sensitive"),
            "NOT_FOUND",
        ),
        (
            discord.HTTPException(SimpleNamespace(status=400, reason="Bad Request"), "sensitive"),
            "INVALID_PARAMETER",
        ),
        (
            discord.HTTPException(SimpleNamespace(status=503, reason="Unavailable"), "sensitive"),
            "DISCORD_UNAVAILABLE",
        ),
        (OSError("sensitive"), "DISCORD_UNAVAILABLE"),
        (TimeoutError("sensitive"), "TIMEOUT"),
    ],
)
async def test_discord_error_translation(error, code):
    with pytest.raises(DiscordToolError) as caught:
        async with translate_errors():
            raise error
    assert caught.value.code == code
    assert "sensitive" not in str(caught.value)


async def test_cancellation_is_not_swallowed():
    with pytest.raises(asyncio.CancelledError):
        async with translate_errors():
            raise asyncio.CancelledError()


async def test_operation_timeout(access):
    access.settings.discord_operation_timeout = 0.01
    with pytest.raises(DiscordToolError, match="TIMEOUT"):
        async with access.operation():
            await asyncio.Event().wait()
