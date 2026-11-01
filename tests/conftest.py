import socket
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from pydiscord_mcp_server.config import Settings
from pydiscord_mcp_server.discord_client import BotClient, DiscordRuntime
from pydiscord_mcp_server.services.access import DiscordAccess


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("Tests must not open network connections")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.fixture
def settings():
    return Settings(discord_token="fake-test-token", _env_file=None)


def make_guild(ident=100):
    guild = MagicMock(spec=discord.Guild)
    guild.id = ident
    guild.name = "Test guild"
    guild.owner_id = 900
    guild.member_count = 12
    guild.description = None
    guild.channels = []
    guild.get_member.return_value = None
    return guild


def make_channel(ident=200, guild=None, kind=discord.TextChannel):
    channel = MagicMock(spec=kind)
    channel.id = ident
    channel.guild = guild or make_guild()
    channel.name = "test-channel"
    channel.type = (
        discord.ChannelType.public_thread if kind is discord.Thread else discord.ChannelType.text
    )
    channel.category_id = None
    channel.topic = None
    channel.position = 0
    channel.nsfw = False
    channel.slowmode_delay = 0
    if kind in (discord.VoiceChannel, discord.StageChannel):
        channel.bitrate = 64000
        channel.user_limit = 0
        channel.rtc_region = None
    if kind is discord.Thread:
        channel.parent_id = 200
        channel.archived = True
        channel.locked = False
        channel.archive_timestamp = datetime(2026, 10, 1, tzinfo=UTC)
        channel.owner_id = 900
        channel.message_count = 3
        channel.member_count = 2
    return channel


def make_message(ident=300, channel=None, author_id=900):
    message = MagicMock(spec=discord.Message)
    message.id = ident
    message.channel = channel or make_channel()
    message.guild = message.channel.guild
    message.author = SimpleNamespace(
        id=author_id,
        name="bot",
        display_name="Bot",
        bot=author_id == 900,
    )
    message.created_at = datetime(2026, 10, 1, tzinfo=UTC)
    message.edited_at = None
    message.content = "Bonjour @everyone"
    message.attachments = []
    message.embeds = []
    message.stickers = []
    message.components = []
    message.type = discord.MessageType.default
    message.pinned = False
    message.is_system.return_value = False
    message.mentions = []
    message.role_mentions = []
    message.channel_mentions = []
    message.mention_everyone = False
    message.reference = None
    message.poll = None
    message.jump_url = f"https://discord.com/channels/100/{message.channel.id}/{ident}"
    return message


def make_client():
    client = MagicMock(spec=BotClient)
    client.gateway_connected = True
    client.is_ready.return_value = True
    client.user = SimpleNamespace(id=900)
    client.guilds = []
    client.cached_messages = []
    client.get_channel.return_value = None
    client.get_guild.return_value = None
    return client


@pytest.fixture
def access(settings):
    runtime = DiscordRuntime(settings, client=make_client())
    runtime.wait_ready = AsyncMock()
    return DiscordAccess(runtime)


async def async_items(items):
    for item in items:
        yield item


@pytest.fixture
def scene(access):
    from scene import build_scene

    return build_scene(access)
