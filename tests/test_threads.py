from datetime import UTC, datetime

import discord
import pytest
from conftest import async_items, make_channel

from pydiscord_mcp_server.errors import DiscordToolError
from pydiscord_mcp_server.services.threads import ThreadCursor, decode_cursor, list_threads


@pytest.mark.parametrize("mode", ["archived_public", "archived_private", "archived_joined_private"])
async def test_archived_pagination(access, mode):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    thread_list = [make_channel(n, kind=discord.Thread) for n in [303, 302, 301]]
    thread_list[1].archive_timestamp = datetime(2026, 9, 30, tzinfo=UTC)
    channel.archived_threads.side_effect = lambda **kwargs: async_items(thread_list)
    page = await list_threads(access, "200", mode, 2, None)
    assert len(page.items) == 2
    assert page.next_cursor
    marker = decode_cursor(page.next_cursor, "200", mode)
    assert marker == ("302" if mode == "archived_joined_private" else "2026-09-30T00:00:00+00:00")
    await list_threads(access, "200", mode, 2, page.next_cursor)
    kwargs = channel.archived_threads.call_args.kwargs
    assert kwargs["limit"] == 3
    assert kwargs["joined"] is (mode == "archived_joined_private")
    assert kwargs["private"] is (mode != "archived_public")
    if mode == "archived_joined_private":
        assert kwargs["before"].id == 302
    else:
        assert kwargs["before"] == thread_list[1].archive_timestamp


async def test_active_thread_parent_filter_and_pagination(access):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    threads = [make_channel(n, kind=discord.Thread) for n in [301, 303, 302]]
    other = make_channel(304, kind=discord.Thread)
    other.parent_id = 999
    channel.guild.active_threads.return_value = [*threads, other]
    page = await list_threads(access, "200", "active", 2, None)
    assert [t.id for t in page.items] == ["303", "302"]
    next_page = await list_threads(access, "200", "active", 2, page.next_cursor)
    assert [t.id for t in next_page.items] == ["301"]
    assert next_page.next_cursor is None


async def test_forum_public_archives(access):
    channel = make_channel(kind=discord.ForumChannel)
    access.client.get_channel.return_value = channel
    channel.archived_threads.side_effect = lambda **kwargs: async_items([])
    assert (await list_threads(access, "200", "archived_public", 10, None)).items == []
    with pytest.raises(DiscordToolError, match="INVALID_PARAMETER"):
        await list_threads(access, "200", "archived_private", 10, None)


@pytest.mark.parametrize(
    "cursor",
    [
        "bad!",
        "e30=",
        ThreadCursor(channel_id="201", mode="active", before="300").encode(),
        ThreadCursor(channel_id="200", mode="archived_public", before="2026-10-01").encode(),
    ],
)
def test_invalid_cursor(cursor):
    with pytest.raises(DiscordToolError, match="INVALID_PARAMETER"):
        decode_cursor(cursor, "200", "active")


def test_cursor_timezone_required():
    cursor = ThreadCursor(channel_id="200", mode="archived_public", before="2026-10-01").encode()
    with pytest.raises(DiscordToolError, match="INVALID_PARAMETER"):
        decode_cursor(cursor, "200", "archived_public")
