import pytest
from conftest import async_items
from mcp import Client

from pydiscord_mcp_server.errors import DiscordToolError
from pydiscord_mcp_server.models.polls import PollOption
from pydiscord_mcp_server.server import create_application
from pydiscord_mcp_server.services import polls
from pydiscord_mcp_server.services.serialization import message_info


async def test_native_poll_payload_and_serialization(scene):
    scene.text.send.return_value = scene.poll_message
    app = create_application(scene.access.settings, scene.access.runtime)
    async with Client(app.mcp) as client:
        result = await client.call_tool(
            "create_poll",
            {
                "channel_id": "200",
                "question": "Shall we deploy?",
                "answers": [{"text": "Yes", "emoji": "👍"}, {"text": "No"}],
                "duration_hours": 72,
                "allow_multiselect": True,
            },
        )
    assert not result.is_error
    native = scene.text.send.call_args.kwargs["poll"]
    assert native.question == "Shall we deploy?"
    assert native.duration.total_seconds() == 72 * 3600
    assert native.multiple is True
    assert [a.text for a in native.answers] == ["Yes", "No"]
    assert str(native.answers[0].emoji) == "👍"
    assert scene.text.send.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}
    assert result.structured_content["poll"]["answers"][0]["votes"] == 2
    assert result.structured_content["poll"]["finalized"] is False


@pytest.mark.parametrize(
    "invalid",
    [
        {"question": "x" * 301},
        {"question": "  "},
        {"answers": [{"text": "Only one"}]},
        {"answers": [{"text": str(i)} for i in range(11)]},
        {"answers": [{"text": "x" * 56}, {"text": "B"}]},
        {"answers": [{"text": " "}, {"text": "B"}]},
        {"duration_hours": 0},
        {"duration_hours": 769},
        {"duration_hours": 1.5},
        {"allow_multiselect": "false"},
    ],
)
async def test_invalid_poll_cannot_send(scene, invalid):
    app = create_application(scene.access.settings, scene.access.runtime)
    args = {"channel_id": "200", "question": "Q", "answers": [{"text": "A"}, {"text": "B"}]}
    async with Client(app.mcp) as client:
        result = await client.call_tool("create_poll", {**args, **invalid})
    assert result.is_error
    scene.text.send.assert_not_awaited()


def test_unknown_poll_counts_are_not_zero(scene):
    scene.poll.total_votes = None
    data = message_info(scene.poll_message)
    assert data.poll.total_votes is None
    assert data.poll.answers[0].votes is None


async def test_get_poll_refreshes_rest_instead_of_cache(scene):
    scene.access.client.cached_messages = [scene.poll_message]
    result = await polls.get_poll(scene.access, "200", "310")
    scene.text.fetch_message.assert_awaited_once_with(310)
    assert result.poll.question == "Shall we deploy?"


async def test_end_poll_ownership_and_nonpoll_rejection(scene):
    scene.poll_message.author.id = 901
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await polls.end_poll(scene.access, "200", "310")
    scene.poll_message.end_poll.assert_not_awaited()
    with pytest.raises(DiscordToolError, match="INVALID_PARAMETER"):
        await polls.get_poll(scene.access, "200", "300")


async def test_poll_voter_pagination(scene):
    scene.answer.voters.side_effect = lambda **kwargs: async_items([scene.member, scene.member])
    result = await polls.get_poll_answer_voters(scene.access, "200", "310", 1, 1, "900")
    assert result.next_cursor == "901"
    assert len(result.items) == 1
    assert scene.answer.voters.call_args.kwargs["after"].id == 900
    assert scene.answer.voters.call_args.kwargs["limit"] == 2
    with pytest.raises(DiscordToolError, match="NOT_FOUND"):
        await polls.get_poll_answer_voters(scene.access, "200", "310", 999, 25, None)


async def test_poll_guild_allowlist_before_send(scene):
    scene.access.settings.discord_allowed_guild_ids = ["999"]
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await polls.create_poll(
            scene.access, "200", "Q", [PollOption(text="A"), PollOption(text="B")], 24, False
        )
    scene.text.send.assert_not_awaited()
