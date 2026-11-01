import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import discord

from ..discord_client import DiscordRuntime
from ..errors import DiscordToolError, translate_errors

GuildChannel = discord.abc.GuildChannel | discord.Thread
MessageChannel = discord.TextChannel | discord.Thread | discord.VoiceChannel | discord.StageChannel


class DiscordAccess:
    def __init__(self, runtime: DiscordRuntime) -> None:
        self.runtime = runtime
        self.settings = runtime.settings
        self.client = runtime.client

    @asynccontextmanager
    async def operation(self) -> AsyncIterator[None]:
        async with translate_errors():
            await self.runtime.wait_ready()
            async with asyncio.timeout(self.settings.discord_operation_timeout):
                yield

    def check_guild(self, guild_id: int) -> None:
        allowed = self.settings.discord_allowed_guild_ids
        if allowed is not None and str(guild_id) not in allowed:
            raise DiscordToolError("ACCESS_DENIED", "Guild is outside DISCORD_ALLOWED_GUILD_IDS.")

    async def guild(self, guild_id: str | None) -> discord.Guild:
        selected = guild_id or self.settings.discord_guild_id
        if selected is None:
            raise DiscordToolError("INVALID_PARAMETER", "Provide guild_id or DISCORD_GUILD_ID.")
        ident = int(selected)
        self.check_guild(ident)
        return self.client.get_guild(ident) or await self.client.fetch_guild(ident)

    async def channel(self, channel_id: str) -> GuildChannel:
        ident = int(channel_id)
        channel = self.client.get_channel(ident) or await self.client.fetch_channel(ident)
        if not isinstance(channel, (discord.abc.GuildChannel, discord.Thread)):
            raise DiscordToolError(
                "ACCESS_DENIED", "Only guild channels and threads are supported."
            )
        self.check_guild(channel.guild.id)
        return channel

    async def message_channel(self, channel_id: str) -> MessageChannel:
        channel = await self.channel(channel_id)
        if not isinstance(
            channel,
            (discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel),
        ):
            raise DiscordToolError("INVALID_PARAMETER", "Channel does not support messages.")
        return channel

    async def member(self, guild: discord.Guild, member_id: int) -> discord.Member:
        return guild.get_member(member_id) or await guild.fetch_member(member_id)

    async def message(self, channel: MessageChannel, message_id: str) -> discord.Message:
        ident = int(message_id)
        cached = next(
            (
                m
                for m in self.client.cached_messages
                if m.id == ident and m.channel.id == channel.id
            ),
            None,
        )
        return cached or await channel.fetch_message(ident)

    def bot_id(self) -> int:
        if self.client.user is None:
            raise DiscordToolError("DISCORD_UNAVAILABLE", "Bot identity is not available.")
        return self.client.user.id

    async def require_manage_messages(self, channel: MessageChannel) -> None:
        member = await self.member(channel.guild, self.bot_id())
        if not channel.permissions_for(member).manage_messages:
            raise DiscordToolError("ACCESS_DENIED", "Bot requires Manage Messages permission.")
