from mcp.server import MCPServer

from ..models import (
    ActionResult,
    AllowMentions,
    AllowOtherAuthor,
    Emoji,
    MessageContent,
    MessageInfo,
    MessagePage,
    PageLimit,
    Snowflake,
)
from ..services import messages
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, REACTION_ADD, READ, WRITE


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def read_messages(
        channel_id: Snowflake,
        limit: PageLimit = 50,
        before: Snowflake | None = None,
        after: Snowflake | None = None,
        around: Snowflake | None = None,
    ) -> MessagePage:
        """Read history with one cursor: before (newest first), after (oldest first), or around."""
        async with access.operation():
            return await messages.read_messages(access, channel_id, limit, before, after, around)

    @mcp.tool(annotations=READ)
    async def get_message(channel_id: Snowflake, message_id: Snowflake) -> MessageInfo:
        """Get a message by its ID in a guild channel or thread."""
        async with access.operation():
            return await messages.get_message(access, channel_id, message_id)

    @mcp.tool(annotations=WRITE)
    async def send_message(
        channel_id: Snowflake,
        content: MessageContent,
        reply_to_message_id: Snowflake | None = None,
        allow_mentions: AllowMentions = False,
    ) -> MessageInfo:
        """Send text, optionally replying in this channel. allow_mentions enables ALL mentions."""
        async with access.operation():
            return await messages.send_message(
                access, channel_id, content, reply_to_message_id, allow_mentions
            )

    @mcp.tool(annotations=EDIT)
    async def edit_message(
        channel_id: Snowflake,
        message_id: Snowflake,
        content: MessageContent,
        allow_mentions: AllowMentions = False,
    ) -> MessageInfo:
        """Replace text of the bot's own message. allow_mentions enables ALL mentions."""
        async with access.operation():
            return await messages.edit_message(
                access, channel_id, message_id, content, allow_mentions
            )

    @mcp.tool(annotations=DELETE)
    async def delete_message(
        channel_id: Snowflake,
        message_id: Snowflake,
        allow_other_author: AllowOtherAuthor = False,
    ) -> ActionResult:
        """Delete a message. Other authors require opt-in AND bot Manage Messages permission."""
        async with access.operation():
            return await messages.delete_message(access, channel_id, message_id, allow_other_author)

    @mcp.tool(annotations=REACTION_ADD)
    async def add_reaction(
        channel_id: Snowflake, message_id: Snowflake, emoji: Emoji
    ) -> ActionResult:
        """Add a Unicode/custom emoji reaction as the bot."""
        async with access.operation():
            return await messages.add_reaction(access, channel_id, message_id, emoji)

    @mcp.tool(annotations=EDIT)
    async def remove_reaction(
        channel_id: Snowflake,
        message_id: Snowflake,
        emoji: Emoji,
        member_id: Snowflake | None = None,
    ) -> ActionResult:
        """Remove the bot's reaction, or a member's reaction with Manage Messages permission."""
        async with access.operation():
            return await messages.remove_reaction(access, channel_id, message_id, emoji, member_id)
