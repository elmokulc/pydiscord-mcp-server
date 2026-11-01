from types import SimpleNamespace

import discord
import pytest
from conftest import async_items, make_message

from pydiscord_mcp_server.errors import DiscordToolError
from pydiscord_mcp_server.services import messages, search


async def test_history_after_returns_oldest_first_with_correct_cursor(scene):
    scene.text.history.side_effect = lambda **kwargs: async_items(
        [make_message(n, scene.text) for n in [301, 302, 303]]
    )
    page = await messages.read_messages(scene.access, "200", 2, None, "300")
    assert [m.id for m in page.items] == ["301", "302"]
    assert page.next_cursor == "302" and page.cursor_parameter == "after"
    assert page.order == "oldest_first"
    assert scene.text.history.call_args.kwargs["oldest_first"] is True


async def test_around_is_bounded_without_directional_cursor(scene):
    page = await messages.read_messages(scene.access, "200", 1, None, None, "312")
    assert len(page.items) == 1 and page.next_cursor is None
    assert page.cursor_parameter is None


async def test_history_rejects_multiple_boundaries_before_reading(scene):
    with pytest.raises(DiscordToolError, match="Choose only one"):
        await messages.read_messages(scene.access, "200", 10, "300", "301")
    scene.text.history.assert_not_called()


async def test_search_reports_scan_scope_and_resumes_after_last_scanned(scene):
    samples = [make_message(n, scene.text) for n in [305, 304, 303, 302]]
    for m in samples:
        m.content = "other"
    samples[1].content = "MATCH"
    scene.text.history.side_effect = lambda **kwargs: async_items(samples[: kwargs["limit"]])
    result = await search.search_messages(scene.access, "200", "match", 1, 3, "306")
    assert [m.id for m in result.items] == ["304"]
    assert result.scanned == 2 and result.scan_limit == 3 and result.next_cursor == "304"
    assert not result.exhausted
    assert scene.text.history.call_args.kwargs["before"].id == 306
    result = await search.search_messages(scene.access, "200", "missing", 10, 2, None)
    assert result.scanned == 2 and result.items == [] and result.next_cursor == "304"
    assert not result.exhausted


@pytest.mark.parametrize(
    "query", ["rOsTeR", "CAFÉ", "tanks", "alice", "raid-helper", "SIGN UP", "bonus"]
)
async def test_search_finds_embed_only_bot_messages(scene, query):
    samples = [make_message(n, scene.text) for n in [305, 304, 303]]
    for message in samples:
        message.content = ""
    embed = discord.Embed(title="Guild roster", description="Raid team at the café")
    embed.add_field(name="Tanks", value="Alice")
    embed.set_author(name="Raid-Helper")
    embed.set_footer(text="Sign up here")
    samples[1].embeds = [embed, discord.Embed(description="Bonus")]
    scene.text.history.side_effect = lambda **kwargs: async_items(samples[: kwargs["limit"]])
    result = await search.search_messages(scene.access, "200", query, 1, 3, None)
    assert [message.id for message in result.items] == ["304"]
    assert result.items[0].content == ""
    assert result.items[0].embeds[0].title == "Guild roster"
    assert result.scanned == 2 and result.next_cursor == "304" and not result.exhausted


async def test_replies_ignore_unrelated_references_and_resume_in_after(scene):
    samples = [make_message(n, scene.text) for n in [301, 302, 303]]
    samples[0].reference = SimpleNamespace(
        message_id=999, channel_id=200, guild_id=100, resolved=None
    )
    samples[1].reference = SimpleNamespace(
        message_id=300, channel_id=200, guild_id=100, resolved=None
    )
    scene.text.history.side_effect = lambda **kwargs: async_items(samples)
    result = await search.get_message_replies(scene.access, "200", "300", 1, 100, None)
    assert [m.id for m in result.items] == ["302"]
    assert (
        result.scanned == 2 and result.next_cursor == "302" and result.cursor_parameter == "after"
    )
    assert scene.text.history.call_args.kwargs["oldest_first"] is True
    await search.get_message_replies(scene.access, "200", "300", 1, 100, "302")
    assert scene.text.history.call_args.kwargs["after"].id == 302
