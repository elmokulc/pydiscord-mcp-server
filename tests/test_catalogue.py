import base64
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from mcp import Client

from pydiscord_mcp_server.server import create_application

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a8WQAAAAASUVORK5CYII="
START = (datetime.now(UTC) + timedelta(days=7)).isoformat()
END = (datetime.now(UTC) + timedelta(days=8)).isoformat()
CASES = {
    "list_guilds": {},
    "get_guild_info": {},
    "get_server_info": {},
    "list_channels": {},
    "get_channel_info": {"channel_id": "200"},
    "read_messages": {"channel_id": "200"},
    "get_message": {"channel_id": "200", "message_id": "300"},
    "send_message": {"channel_id": "200", "content": "test"},
    "edit_message": {"channel_id": "200", "message_id": "300", "content": "test"},
    "delete_message": {"channel_id": "200", "message_id": "300"},
    "add_reaction": {"channel_id": "200", "message_id": "300", "emoji": "👍"},
    "remove_reaction": {"channel_id": "200", "message_id": "300", "emoji": "👍"},
    "search_messages": {"channel_id": "200", "query": "hello"},
    "get_message_replies": {"channel_id": "200", "message_id": "300"},
    "list_threads": {"channel_id": "200"},
    "get_thread_info": {"thread_id": "201"},
    "list_active_threads": {},
    "get_member": {"member_id": "901"},
    "get_member_by_id": {"user_id": "901"},
    "get_user_id_by_name": {"username": "alice"},
    "search_members": {"query": "ali"},
    "create_poll": {
        "channel_id": "200",
        "question": "On déploie ?",
        "answers": [{"text": "Oui", "emoji": "👍"}, {"text": "Non"}],
    },
    "get_poll": {"channel_id": "200", "message_id": "310"},
    "end_poll": {"channel_id": "200", "message_id": "310"},
    "get_poll_answer_voters": {"channel_id": "200", "message_id": "310", "answer_id": 1},
    "create_text_channel": {"name": "new", "settings": {"category_id": "202", "topic": "test"}},
    "edit_text_channel": {"channel_id": "200", "settings": {"topic": "new", "category_id": None}},
    "delete_channel": {"channel_id": "200"},
    "find_channel": {"name": "test-channel"},
    "move_channel": {"channel_id": "200", "category_id": "202"},
    "create_category": {"name": "new"},
    "edit_category": {"category_id": "202", "settings": {"name": "new"}},
    "delete_category": {"category_id": "202"},
    "find_category": {"name": "test-channel"},
    "list_channels_in_category": {"category_id": "202"},
    "create_voice_channel": {"name": "new", "settings": {"bitrate": 64000}},
    "create_stage_channel": {"name": "new"},
    "edit_voice_channel": {"channel_id": "203", "settings": {"rtc_region": None}},
    "create_forum_channel": {"name": "new", "settings": {"default_layout": "gallery_view"}},
    "edit_forum_channel": {
        "channel_id": "205",
        "settings": {"default_sort_order": "creation_date"},
    },
    "list_forum_channels": {},
    "get_forum_channel_info": {"channel_id": "205"},
    "list_forum_tags": {"channel_id": "205"},
    "create_forum_post": {
        "channel_id": "205",
        "title": "Post",
        "content": "test",
        "tag_ids": ["550"],
    },
    "list_forum_posts": {"channel_id": "205"},
    "modify_forum_post": {"post_id": "206", "settings": {"pinned": True, "tag_ids": []}},
    "list_roles": {},
    "create_role": {"name": "new", "settings": {"permissions": "1024"}},
    "edit_role": {"role_id": "500", "settings": {"colour": 0x123456}},
    "delete_role": {"role_id": "500"},
    "assign_role": {"member_id": "901", "role_id": "500"},
    "remove_role": {"member_id": "901", "role_id": "500"},
    "kick_member": {"member_id": "901"},
    "ban_member": {"member_id": "901"},
    "unban_member": {"member_id": "901"},
    "timeout_member": {"member_id": "901", "duration_seconds": 60},
    "remove_timeout": {"member_id": "901"},
    "set_nickname": {"member_id": "901", "nickname": None},
    "get_bans": {},
    "move_member": {"member_id": "901", "channel_id": "203"},
    "disconnect_member": {"member_id": "901"},
    "modify_voice_state": {"member_id": "901", "mute": True},
    "list_channel_permission_overwrites": {"channel_id": "200"},
    "upsert_role_channel_permissions": {
        "channel_id": "200",
        "role_id": "500",
        "changes": {"permissions": {"send_messages": False}},
    },
    "upsert_member_channel_permissions": {
        "channel_id": "200",
        "member_id": "901",
        "changes": {"permissions": {"send_messages": True}},
    },
    "delete_channel_permission_overwrite": {
        "channel_id": "200",
        "target_id": "500",
        "target_type": "role",
    },
    "create_webhook": {"channel_id": "200", "name": "hook"},
    "list_webhooks": {"channel_id": "200"},
    "delete_webhook": {"webhook_id": "800"},
    "send_webhook_message": {"webhook_id": "800", "content": "test"},
    "create_invite": {"channel_id": "200"},
    "list_invites": {},
    "delete_invite": {"code": "testInvite"},
    "get_invite_details": {"code": "testInvite"},
    "list_emojis": {},
    "get_emoji_details": {"emoji_id": "600"},
    "create_emoji": {"name": "new", "image_base64": PNG},
    "edit_emoji": {"emoji_id": "600", "name": "new", "role_ids": []},
    "delete_emoji": {"emoji_id": "600"},
    "create_guild_scheduled_event": {
        "name": "Event",
        "start_time": START,
        "end_time": END,
        "entity_type": "external",
        "location": "Paris",
    },
    "edit_guild_scheduled_event": {"event_id": "700", "settings": {"name": "new"}},
    "delete_guild_scheduled_event": {"event_id": "700"},
    "list_guild_scheduled_events": {},
    "get_guild_scheduled_event_users": {"event_id": "700"},
    "send_private_message": {"user_id": "901", "content": "test"},
    "read_private_messages": {"user_id": "901"},
    "edit_private_message": {"user_id": "901", "message_id": "330", "content": "new"},
    "delete_private_message": {"user_id": "901", "message_id": "330"},
}


def test_catalogue_covers_pinned_reference_and_extensions():
    reference = json.loads((Path(__file__).parent / "fixtures/reference_tools.json").read_text())
    assert len(reference["tools"]) == 81
    assert set(reference["tools"]) <= CASES.keys()
    assert len(CASES) == 88
    assert base64.b64decode(PNG).startswith(b"\x89PNG")


@pytest.mark.parametrize("name,arguments", CASES.items(), ids=CASES.keys())
async def test_each_tool_through_official_mcp_client(scene, name, arguments):
    application = create_application(scene.access.settings, scene.access.runtime)
    async with Client(application.mcp) as client:
        result = await client.call_tool(name, arguments)
    assert not result.is_error, (name, result.content)
    assert result.structured_content is not None
    assert "secret-webhook-token-must-not-leak" not in str(result)
