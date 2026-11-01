from types import SimpleNamespace

import discord
import pytest
from conftest import async_items, make_channel, make_message

from pydiscord_mcp_server.errors import DiscordToolError
from pydiscord_mcp_server.services import messages
from pydiscord_mcp_server.services.serialization import message_info


def test_message_serialization():
    message = make_message(1234567890123456789)
    message.attachments = [
        SimpleNamespace(
            id=501,
            filename="test.txt",
            url="https://cdn.example/test.txt",
            proxy_url="https://proxy.example/test.txt",
            size=42,
            content_type="text/plain",
            description="Attachment",
        )
    ]
    message.reference = SimpleNamespace(message_id=299, channel_id=200, guild_id=100)
    result = message_info(message).model_dump(mode="json")
    assert result["id"] == "1234567890123456789"
    assert result["author"]["id"] == "900"
    assert result["created_at"].endswith("Z")
    assert result["content"] == "Bonjour @everyone"
    assert result["attachments"][0]["id"] == "501"
    assert result["reference"]["message_id"] == "299"
    assert result["url"].endswith("1234567890123456789")


async def test_read_messages_pagination(access):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    channel.history.side_effect = lambda **kwargs: async_items(
        [make_message(n, channel) for n in [303, 302, 301]]
    )
    page = await messages.read_messages(access, "200", 2, "304")
    assert [m.id for m in page.items] == ["303", "302"]
    assert page.next_cursor == "302"
    args = channel.history.call_args.kwargs
    assert args["limit"] == 3 and args["before"].id == 304 and args["oldest_first"] is False


@pytest.mark.parametrize("allow_mentions", [False, True])
async def test_send_mentions_and_reply(access, allow_mentions):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    channel.send.return_value = make_message(channel=channel)
    reply = make_message(299, channel)
    channel.fetch_message.return_value = reply
    await messages.send_message(access, "200", "@everyone", "299", allow_mentions)
    kwargs = channel.send.call_args.kwargs
    allowed = kwargs["allowed_mentions"]
    assert allowed.everyone is allow_mentions
    assert allowed.users is allow_mentions
    assert allowed.roles is allow_mentions
    assert allowed.replied_user is allow_mentions
    assert kwargs["reference"] is reply.to_reference.return_value
    reply.to_reference.assert_called_once_with(fail_if_not_exists=True)


async def test_send_without_reply_omits_reference(access):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    channel.send.return_value = make_message(channel=channel)
    await messages.send_message(access, "200", "Hello", None, False)
    assert "reference" not in channel.send.call_args.kwargs
    channel.fetch_message.assert_not_awaited()


async def test_edit_only_own_messages_and_default_mentions(access):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    message = make_message(author_id=901)
    channel.fetch_message.return_value = message
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await messages.edit_message(access, "200", "300", "edited", False)
    message.edit.assert_not_awaited()
    message.author.id = 900
    message.edit.return_value = message
    await messages.edit_message(access, "200", "300", "edited", False)
    assert message.edit.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}


@pytest.mark.parametrize(
    "opt_in,permission,success", [(False, True, False), (True, False, False), (True, True, True)]
)
async def test_delete_other_author_requires_opt_in_and_permission(
    access, opt_in, permission, success
):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    message = make_message(author_id=901)
    channel.fetch_message.return_value = message
    channel.permissions_for.return_value = discord.Permissions(manage_messages=permission)
    if success:
        assert (await messages.delete_message(access, "200", "300", opt_in)).action == "deleted"
        message.delete.assert_awaited_once()
    else:
        with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
            await messages.delete_message(access, "200", "300", opt_in)
        message.delete.assert_not_awaited()


async def test_delete_own_message_needs_no_manage_messages(access):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    channel.fetch_message.return_value = make_message()
    await messages.delete_message(access, "200", "300", False)
    channel.permissions_for.assert_not_called()


async def test_reaction_add_and_remove(access):
    channel = make_channel()
    access.client.get_channel.return_value = channel
    message = make_message()
    channel.fetch_message.return_value = message
    await messages.add_reaction(access, "200", "300", "👍")
    message.add_reaction.assert_awaited_once_with("👍")
    await messages.remove_reaction(access, "200", "300", "👍", None)
    assert message.remove_reaction.call_args.args[1].id == 900
    channel.permissions_for.return_value = discord.Permissions.none()
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await messages.remove_reaction(access, "200", "300", "👍", "901")
