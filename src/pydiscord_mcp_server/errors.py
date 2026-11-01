"""Safe, stable error codes for failed MCP tool calls."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiohttp
import discord
from mcp.server.mcpserver.exceptions import ToolError


class DiscordToolError(ToolError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@asynccontextmanager
async def translate_errors() -> AsyncIterator[None]:
    try:
        yield
    except DiscordToolError:
        raise
    except discord.Forbidden:
        raise DiscordToolError("ACCESS_DENIED", "Discord refused access or permissions.") from None
    except discord.NotFound:
        raise DiscordToolError(
            "NOT_FOUND", "Discord resource does not exist or is inaccessible."
        ) from None
    except TimeoutError:
        raise DiscordToolError(
            "TIMEOUT", "Discord operation timed out; check before retrying writes."
        ) from None
    except discord.HTTPException as exc:
        if exc.status == 400:
            raise DiscordToolError(
                "INVALID_PARAMETER", "Discord rejected the request parameters."
            ) from None
        raise DiscordToolError(
            "DISCORD_UNAVAILABLE", "Discord HTTP request failed; retry later."
        ) from None
    except (aiohttp.ClientError, OSError, discord.ConnectionClosed, discord.ClientException):
        raise DiscordToolError(
            "DISCORD_UNAVAILABLE", "Discord connection is unavailable."
        ) from None
