from types import SimpleNamespace
from unittest.mock import MagicMock

import discord
import pytest
from conftest import make_channel, make_guild, make_message

from pydiscord_mcp_server.errors import DiscordToolError
from pydiscord_mcp_server.services import channels, guilds, members, messages, threads


async def test_channel_cache_and_api_fallback(access):
    channel = make_channel()
    access.client.fetch_channel.return_value = channel
    result = await channels.get_channel_info(access, "200")
    assert result.id == "200"
    access.client.fetch_channel.assert_awaited_once_with(200)
    access.client.get_channel.return_value = channel
    await channels.get_channel_info(access, "200")
    access.client.fetch_channel.assert_awaited_once()


async def test_archived_thread_direct_id(access):
    thread = make_channel(201, kind=discord.Thread)
    access.client.fetch_channel.return_value = thread
    result = await threads.get_thread_info(access, "201")
    assert result.archived is True
    assert result.parent_id == "200"


@pytest.mark.parametrize("cached", [True, False])
@pytest.mark.parametrize("kind", [discord.TextChannel, discord.Thread])
async def test_direct_channel_allowlist_before_message_operation(access, cached, kind):
    access.settings.discord_allowed_guild_ids = ["101"]
    channel = make_channel(kind=kind)
    if cached:
        access.client.get_channel.return_value = channel
    else:
        access.client.fetch_channel.return_value = channel
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await messages.get_message(access, "200", "300")
    channel.fetch_message.assert_not_awaited()


async def test_dm_rejected(access):
    access.client.fetch_channel.return_value = MagicMock(spec=discord.DMChannel)
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await access.channel("200")


async def test_default_guild_is_not_access_restriction(access):
    access.settings.discord_guild_id = "100"
    access.client.fetch_guild.return_value = make_guild(101)
    assert (await access.guild("101")).id == 101
    access.settings.discord_allowed_guild_ids = ["100"]
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await access.guild("101")


async def test_missing_default_guild(access):
    with pytest.raises(DiscordToolError, match="INVALID_PARAMETER"):
        await access.guild(None)


async def test_guild_and_channel_pagination(access):
    access.client.guilds = [make_guild(n) for n in [103, 101, 102]]
    access.settings.discord_allowed_guild_ids = ["101", "102"]
    page = await guilds.list_guilds(access, 1, None)
    assert [g.id for g in page.items] == ["101"]
    assert page.next_cursor == "101"
    assert (await guilds.list_guilds(access, 1, page.next_cursor)).items[0].id == "102"
    access.settings.discord_allowed_guild_ids = []
    assert (await guilds.list_guilds(access, 10, None)).items == []
    access.settings.discord_allowed_guild_ids = None
    guild = make_guild()
    access.client.get_guild.return_value = guild
    guild.fetch_channels.return_value = [make_channel(202), make_channel(201)]
    channels_page = await channels.list_channels(access, "100", 1, None)
    assert channels_page.next_cursor == "201"
    assert channels_page.items[0].id == "201"
    guild.fetch_channels.assert_awaited_once()


async def test_message_cache_is_channel_scoped(access):
    channel = make_channel()
    cached = make_message(channel=channel)
    access.client.cached_messages = [cached]
    assert await access.message(channel, "300") is cached
    channel.fetch_message.assert_not_awaited()
    other_channel = make_channel(201)
    await access.message(other_channel, "300")
    other_channel.fetch_message.assert_awaited_once_with(300)


async def test_member_cache_and_rest(access):
    guild = make_guild()
    member = SimpleNamespace(
        id=901,
        name="alice",
        display_name="Alice",
        bot=False,
        guild=guild,
        nick=None,
        joined_at=None,
        roles=[SimpleNamespace(id=100)],
    )
    access.client.get_guild.return_value = guild
    guild.fetch_member.return_value = member
    result = await members.get_member(access, "901", "100")
    assert result.role_ids == ["100"]
    guild.fetch_member.assert_awaited_once_with(901)
    guild.get_member.return_value = member
    await members.get_member(access, "901", "100")
    guild.fetch_member.assert_awaited_once()


async def test_member_search_intent_and_scope(access):
    with pytest.raises(DiscordToolError, match="INTENT_MEMBERS"):
        await members.search_members(access, "ali", "100", 2)
    access.settings.discord_intent_members = True
    guild = make_guild()
    access.client.get_guild.return_value = guild
    guild.query_members.return_value = []
    result = await members.search_members(access, "ali", "100", 2)
    guild.query_members.assert_awaited_once_with(query="ali", limit=5, cache=False)
    assert result.exhaustive is False
    with pytest.raises(DiscordToolError, match="INVALID_PARAMETER"):
        await members.search_members(access, "  ", "100", 2)
