from mcp.server import MCPServer

from ..models import (
    ActionResult,
    AllowMentions,
    MessageContent,
    MessageInfo,
    MessagePage,
    PageLimit,
    Snowflake,
)
from ..services import private_messages
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, READ, WRITE


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=WRITE)
    async def send_private_message(
        user_id: Snowflake,
        content: MessageContent,
        guild_id: Snowflake | None = None,
        reply_to_message_id: Snowflake | None = None,
        allow_mentions: AllowMentions = False,
    ) -> MessageInfo:
        """Send a bot DM; requires explicit DM opt-in and membership in the selected guild."""
        async with access.operation():
            return await private_messages.send_private_message(
                access, user_id, content, guild_id, reply_to_message_id, allow_mentions
            )

    @mcp.tool(annotations=READ)
    async def read_private_messages(
        user_id: Snowflake,
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        before: Snowflake | None = None,
        after: Snowflake | None = None,
        around: Snowflake | None = None,
    ) -> MessagePage:
        """Read bot DM history after opt-in and guild authorization; at most one history cursor."""
        async with access.operation():
            return await private_messages.read_private_messages(
                access, user_id, guild_id, limit, before, after, around
            )

    @mcp.tool(annotations=EDIT)
    async def edit_private_message(
        user_id: Snowflake,
        message_id: Snowflake,
        content: MessageContent,
        guild_id: Snowflake | None = None,
        allow_mentions: AllowMentions = False,
    ) -> MessageInfo:
        """Edit this bot's DM after opt-in and guild authorization; mentions disabled by default."""
        async with access.operation():
            return await private_messages.edit_private_message(
                access, user_id, message_id, content, guild_id, allow_mentions
            )

    @mcp.tool(annotations=DELETE)
    async def delete_private_message(
        user_id: Snowflake,
        message_id: Snowflake,
        guild_id: Snowflake | None = None,
    ) -> ActionResult:
        """Delete this bot's own DM after opt-in and guild authorization."""
        async with access.operation():
            return await private_messages.delete_private_message(
                access, user_id, message_id, guild_id
            )
