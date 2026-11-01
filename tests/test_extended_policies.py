from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import discord
import pytest
from conftest import make_channel, make_guild
from mcp import Client
from pydantic import ValidationError
from test_catalogue import CASES

from pydiscord_mcp_server.errors import DiscordToolError
from pydiscord_mcp_server.models.management import (
    EventUpdate,
    ForumPostUpdate,
    OverwriteChanges,
    RoleUpdate,
    TextChannelUpdate,
)
from pydiscord_mcp_server.server import create_application
from pydiscord_mcp_server.services import (
    events,
    integrations,
    manage_channels,
    members,
    permissions,
    private_messages,
    roles,
)


@pytest.mark.parametrize(
    "name",
    [
        "create_text_channel",
        "edit_text_channel",
        "delete_channel",
        "move_channel",
        "assign_role",
        "kick_member",
        "ban_member",
        "timeout_member",
        "upsert_role_channel_permissions",
        "delete_channel_permission_overwrite",
        "send_webhook_message",
        "delete_webhook",
        "get_invite_details",
        "delete_invite",
        "create_guild_scheduled_event",
        "delete_guild_scheduled_event",
        "delete_emoji",
        "send_private_message",
        "read_private_messages",
        "edit_private_message",
        "delete_private_message",
    ],
)
async def test_extended_tools_respect_guild_allowlist(scene, name):
    scene.access.settings.discord_allowed_guild_ids = ["999"]
    app = create_application(scene.access.settings, scene.access.runtime)
    async with Client(app.mcp) as client:
        result = await client.call_tool(name, CASES[name])
    assert result.is_error
    assert "ACCESS_DENIED" in result.content[0].text
    for method in [
        scene.text.send,
        scene.text.edit,
        scene.text.delete,
        scene.guild.create_text_channel,
        scene.member.add_roles,
        scene.member.kick,
        scene.guild.ban,
        scene.member.timeout,
        scene.text.set_permissions,
        scene.hook.send,
        scene.hook.delete,
        scene.invite.delete,
        scene.guild.create_scheduled_event,
        scene.event.delete,
        scene.emoji.delete,
        scene.dm.send,
        scene.dm.fetch_message,
        scene.dm.history,
    ]:
        assert not method.called


async def test_cross_guild_category_rejected_even_when_both_allowed(scene):
    foreign = make_channel(999, make_guild(101), discord.CategoryChannel)
    scene.channels[999] = foreign
    with pytest.raises(DiscordToolError, match="same guild"):
        await manage_channels.move_channel(scene.access, "200", "999", None, False, None)
    scene.text.edit.assert_not_awaited()


async def test_permission_merge_preserves_existing_fields_and_null_inherits(scene):
    result = await permissions.upsert_permissions(
        scene.access,
        "200",
        "500",
        "role",
        OverwriteChanges(permissions={"send_messages": False, "attach_files": None}),
        None,
    )
    assert result.permissions["read_messages"] is True  # discord.py's canonical alias
    assert result.permissions["send_messages"] is False
    overwrite = scene.text.set_permissions.call_args.kwargs["overwrite"]
    assert overwrite.attach_files is None
    with pytest.raises(ValidationError):
        OverwriteChanges(permissions={"unknown_permission": True})
    with pytest.raises(ValidationError):
        OverwriteChanges(permissions={"send_messages": "false"})


async def test_threads_cannot_receive_independent_overwrites(scene):
    with pytest.raises(DiscordToolError, match="inherit"):
        await permissions.list_channel_permission_overwrites(scene.access, "201", 10, None)


async def test_webhook_thread_must_belong_to_webhook_channel(scene):
    with pytest.raises(DiscordToolError, match="Thread must belong"):
        await integrations.send_webhook_message(scene.access, "800", "test", False, "206")
    scene.hook.send.assert_not_awaited()


async def test_webhook_send_mentions_disabled(scene):
    await integrations.send_webhook_message(scene.access, "800", "@everyone", False, None)
    assert scene.hook.send.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}


async def test_dm_opt_in_and_message_ownership(scene):
    scene.access.settings.discord_enable_dms = False
    with pytest.raises(DiscordToolError, match="ENABLE_DMS"):
        await private_messages.private_channel(scene.access, "901", "100")
    scene.dm.send.assert_not_awaited()
    scene.access.settings.discord_enable_dms = True
    scene.dm_message.author.id = 901
    with pytest.raises(DiscordToolError, match="ACCESS_DENIED"):
        await private_messages.delete_private_message(scene.access, "901", "330", "100")
    scene.dm_message.delete.assert_not_awaited()


async def test_dm_membership_is_verified_before_opening_channel(scene):
    scene.guild.get_member.side_effect = None
    scene.guild.get_member.return_value = None
    scene.guild.fetch_member.side_effect = discord.NotFound(
        SimpleNamespace(status=404, reason="Not Found"), "member absent"
    )
    with pytest.raises(DiscordToolError, match="NOT_FOUND"):
        async with scene.access.operation():
            await private_messages.private_channel(scene.access, "999", "100")
    scene.member.create_dm.assert_not_awaited()


async def test_role_permissions_and_single_role_assignment(scene):
    await roles.create_role(scene.access, "role", "100", RoleUpdate(permissions="1024"), None)
    assert scene.guild.create_role.call_args.kwargs["permissions"].value == 1024
    await roles.member_role(scene.access, "901", "500", "100", "test")
    scene.member.add_roles.assert_awaited_once_with(scene.role, reason="test", atomic=True)


async def test_channel_updates_distinguish_omitted_and_explicit_null(scene):
    await manage_channels.edit_text_channel(
        scene.access, "200", TextChannelUpdate(topic="new"), None
    )
    assert "category" not in scene.text.edit.call_args.kwargs
    await manage_channels.edit_text_channel(
        scene.access, "200", TextChannelUpdate(category_id=None), None
    )
    assert scene.text.edit.call_args.kwargs["category"] is None


async def test_forum_post_tags_must_belong_to_parent(scene):
    with pytest.raises(DiscordToolError, match="Every tag"):
        await manage_channels.modify_forum_post(
            scene.access, "206", ForumPostUpdate(tag_ids=["999"]), None
        )
    scene.post.edit.assert_not_awaited()


async def test_external_event_requires_end_and_aware_times(scene):
    with pytest.raises(DiscordToolError, match="require location/end_time"):
        await events.create_event(
            scene.access,
            "E",
            datetime.now(UTC) + timedelta(days=1),
            "external",
            "100",
            None,
            None,
            "Paris",
            None,
            None,
        )
    with pytest.raises(ValidationError):
        EventUpdate(start_time="2027-01-01T12:00:00")
    scene.guild.create_scheduled_event.assert_not_awaited()


async def test_member_search_cache_global_name_and_targeted_id(scene):
    result = await members.search_members(scene.access, "Global", "100", 10)
    assert result.items[0].id == "901" and not result.exhaustive
    scene.access.settings.discord_intent_members = False
    result = await members.search_members(scene.access, "901", "100", 10)
    assert result.items[0].id == "901"


@pytest.mark.parametrize("data", ["not-base64!", "", "eA=="])
def test_invalid_emoji_images_rejected(data):
    with pytest.raises(DiscordToolError, match="INVALID_PARAMETER"):
        integrations.decode_emoji_image(data)
