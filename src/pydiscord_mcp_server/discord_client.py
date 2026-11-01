"""One supervised Discord connection for the entire ASGI process."""

import asyncio
import logging
from contextlib import suppress

import discord

from .config import Settings
from .errors import DiscordToolError

logger = logging.getLogger(__name__)


class BotClient(discord.Client):
    gateway_connected: bool = False

    async def on_ready(self) -> None:
        self.gateway_connected = True
        logger.info("Discord bot ready")

    async def on_resumed(self) -> None:
        self.gateway_connected = True
        logger.info("Discord gateway resumed")

    async def on_disconnect(self) -> None:
        self.gateway_connected = False
        logger.warning("Discord disconnected; readiness disabled during reconnection")


def create_client(settings: Settings) -> BotClient:
    intents = discord.Intents.none()
    intents.guilds = True
    intents.guild_messages = True
    intents.guild_reactions = True
    intents.message_content = settings.discord_intent_message_content
    intents.members = settings.discord_intent_members
    return BotClient(
        intents=intents,
        allowed_mentions=discord.AllowedMentions.none(),
        max_messages=1000,
        chunk_guilds_at_startup=False,
    )


class DiscordRuntime:
    def __init__(self, settings: Settings, client: BotClient | None = None) -> None:
        self.settings = settings
        self.client = client if client is not None else create_client(settings)
        self.task: asyncio.Task[None] | None = None
        self.failed = asyncio.Event()
        self.stopping = False

    @property
    def ready(self) -> bool:
        return (
            self.task is not None
            and not self.task.done()
            and not self.stopping
            and self.client.is_ready()
            and self.client.gateway_connected
        )

    def _connection_finished(self, task: asyncio.Task[None]) -> None:
        # Retrieve the exception, but never log its text (it could contain sensitive data).
        exception = None if task.cancelled() else task.exception()
        if not self.stopping:
            self.failed.set()
            logger.critical(
                "Discord connection task terminated (%s)",
                type(exception).__name__ if exception else "unexpected exit",
            )

    async def start(self) -> None:
        if self.task is not None:
            raise RuntimeError("Discord runtime can only be started once")
        self.task = asyncio.create_task(
            self.client.start(self.settings.discord_token.get_secret_value(), reconnect=True),
            name="discord-connection",
        )
        self.task.add_done_callback(self._connection_finished)
        try:
            await self.wait_ready()
        except BaseException:
            await self.close()
            raise

    async def wait_ready(self) -> None:
        async with asyncio.timeout(self.settings.discord_ready_timeout):
            while not self.ready:
                if self.stopping or self.task is None or self.task.done():
                    raise DiscordToolError("DISCORD_UNAVAILABLE", "Discord bot is not connected.")
                await asyncio.sleep(0.05)

    async def close(self) -> None:
        if self.stopping:
            return
        self.stopping = True
        try:
            async with asyncio.timeout(self.settings.discord_shutdown_timeout):
                await self.client.close()
        except TimeoutError:
            logger.warning("Discord close timed out; cancelling connection task")
        finally:
            if self.task is not None:
                self.task.cancel()
                with suppress(asyncio.CancelledError, Exception):
                    async with asyncio.timeout(self.settings.discord_shutdown_timeout):
                        await self.task
