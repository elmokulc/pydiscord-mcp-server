from types import SimpleNamespace

import discord
import pytest
from conftest import async_items, make_message
from mcp import Client

from pydiscord_mcp_server.server import create_application
from pydiscord_mcp_server.services.serialization import message_info


@pytest.fixture
def rich_message(scene):
    # Parse a real Discord payload: an embed-only Raid-Helper message, no network involved.
    client = discord.Client(intents=discord.Intents.none())
    return discord.Message(
        state=client._connection,
        channel=scene.text,
        data={
            "id": "1560925185862017045",
            "type": 0,
            "content": "",
            "edited_timestamp": "2026-10-27T23:05:02+00:00",
            "author": {
                "id": "579155972115660803",
                "username": "Raid-Helper",
                "discriminator": "0000",
                "avatar": None,
                "bot": True,
            },
            "attachments": [],
            "mentions": [],
            "mention_roles": [],
            "pinned": True,
            "embeds": [
                {
                    "type": "rich",
                    "title": "Roster de guilde",
                    "description": "Équipe du raid\n" + "x" * 4000,
                    "url": "https://raid-helper.dev/event/123",
                    "color": 0x123456,
                    "timestamp": "2026-10-17T07:59:24Z",
                    "author": {
                        "name": "Raid-Helper",
                        "url": "https://raid-helper.dev",
                        "icon_url": "https://example.com/author.png",
                        "proxy_icon_url": "https://proxy.example.com/author.png",
                    },
                    "footer": {
                        "text": "Inscrivez-vous ici",
                        "icon_url": "https://example.com/footer.png",
                    },
                    "fields": [
                        {"name": "Tanks", "value": "Alice\nBob", "inline": True},
                        {"name": "Soigneurs", "value": "y" * 1024},
                    ],
                    "image": {
                        "url": "https://example.com/roster.png",
                        "proxy_url": "https://proxy.example.com/roster.png",
                        "width": 800,
                        "height": 600,
                    },
                    "thumbnail": {"url": "https://example.com/thumb.png"},
                },
                {
                    "type": "video",
                    "video": {"url": "https://example.com/raid.mp4", "width": 640},
                    "provider": {"name": "Video host", "url": "https://example.com"},
                },
            ],
            "sticker_items": [{"id": "1234567890123456789", "name": "Wave", "format_type": 1}],
            "components": [
                {
                    "type": 17,
                    "id": 1,
                    "components": [
                        {"type": 10, "id": 2, "content": "Choisir un rôle"},
                        {
                            "type": 1,
                            "id": 3,
                            "components": [
                                {
                                    "type": 2,
                                    "id": 4,
                                    "style": 5,
                                    "label": "S'inscrire",
                                    "url": "https://raid-helper.dev/event/123",
                                }
                            ],
                        },
                        {
                            "type": 1,
                            "id": 5,
                            "components": [
                                {
                                    "type": 3,
                                    "id": 6,
                                    "custom_id": "raid-role",
                                    "options": [{"label": "Tank", "value": "tank"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        },
    )


def test_native_bot_message_preserves_all_rich_content(rich_message):
    result = message_info(rich_message).model_dump(mode="json")
    assert result["content"] == "" and result["attachments"] == [] and result["poll"] is None
    assert result["author"]["bot"] is True
    assert result["author"]["name"] == "Raid-Helper"
    assert len(result["embeds"]) == 2
    embed = result["embeds"][0]
    assert embed["title"] == "Roster de guilde"
    assert embed["description"] == "Équipe du raid\n" + "x" * 4000
    assert embed["url"] == "https://raid-helper.dev/event/123"
    assert embed["color"] == 0x123456
    assert embed["timestamp"] == "2026-10-17T07:59:24Z"
    assert embed["author"]["proxy_icon_url"] == "https://proxy.example.com/author.png"
    assert embed["footer"]["text"] == "Inscrivez-vous ici"
    assert embed["fields"] == [
        {"name": "Tanks", "value": "Alice\nBob", "inline": True},
        {"name": "Soigneurs", "value": "y" * 1024, "inline": False},
    ]
    assert embed["image"]["width"] == 800
    assert embed["image"]["proxy_url"] == "https://proxy.example.com/roster.png"
    assert embed["thumbnail"]["url"] == "https://example.com/thumb.png"
    assert result["embeds"][1]["video"]["url"] == "https://example.com/raid.mp4"
    assert result["embeds"][1]["provider"]["name"] == "Video host"
    assert result["stickers"] == [
        {
            "id": "1234567890123456789",
            "name": "Wave",
            "format": "png",
            "url": "https://cdn.discordapp.com/stickers/1234567890123456789.png",
        }
    ]
    children = result["components"][0]["components"]
    assert result["components"][0]["type"] == 17
    assert children[0]["content"] == "Choisir un rôle"
    assert children[1]["components"][0]["url"] == "https://raid-helper.dev/event/123"
    assert children[2]["components"][0]["options"][0]["value"] == "tank"
    assert result["type"] == "default" and result["pinned"] is True
    assert result["is_system"] is False and result["system_content"] is None


def test_plain_message_has_empty_rich_content():
    result = message_info(make_message())
    assert result.content == "Bonjour @everyone"
    assert result.embeds == result.stickers == result.components == []
    assert result.mentions == result.role_mentions == result.channel_mentions == []
    assert result.type == "default" and not result.pinned


def test_system_message_and_resolved_mentions(rich_message, scene):
    rich_message.type = discord.MessageType.pins_add
    rich_message.mentions = [scene.member]
    rich_message.role_mentions = [scene.role]
    result = message_info(rich_message).model_dump(mode="json")
    assert result["type"] == "pins_add" and result["is_system"] is True
    assert "pinned a message" in result["system_content"]
    assert result["mentions"][0]["id"] == "901"
    assert result["role_mentions"] == [{"id": "500", "name": "Reader"}]

    message = make_message()
    message.channel_mentions = [scene.text]
    message.mention_everyone = True
    result = message_info(message)
    assert result.channel_mentions[0].model_dump() == {"id": "200", "name": "test-channel"}
    assert result.mention_everyone is True


def test_resolved_reply_preserves_embeds_without_recursing(rich_message):
    reply = make_message()
    reply.reference = SimpleNamespace(
        message_id=rich_message.id, channel_id=200, guild_id=100, resolved=rich_message
    )
    rich_message.reference = SimpleNamespace(
        message_id=reply.id, channel_id=200, guild_id=100, resolved=reply
    )
    result = message_info(reply)
    assert result.reply_to.embeds[0].title == "Roster de guilde"
    assert result.reply_to.reply_to is None


@pytest.mark.parametrize("tool", ["read_messages", "get_message", "get_message_replies"])
async def test_rich_content_survives_mcp_output_schema(scene, rich_message, tool):
    rich_message.reference = SimpleNamespace(
        message_id=300, channel_id=200, guild_id=100, resolved=None
    )
    scene.text.history.side_effect = lambda **kwargs: async_items([rich_message])
    scene.text.fetch_message.side_effect = None
    scene.text.fetch_message.return_value = rich_message
    application = create_application(scene.access.settings, scene.access.runtime)
    arguments = {"channel_id": "200"}
    if tool != "read_messages":
        arguments["message_id"] = "300" if tool == "get_message_replies" else str(rich_message.id)
    async with Client(application.mcp) as client:
        result = await client.call_tool(tool, arguments)
    assert not result.is_error
    data = result.structured_content
    if tool != "get_message":
        data = data["items"][0]
    assert data["content"] == ""
    assert data["embeds"][0]["title"] == "Roster de guilde"
    assert data["components"][0]["components"][0]["content"] == "Choisir un rôle"
