from mcp.server import MCPServer

from ..models import ChannelInfo, Cursor, PageLimit, Snowflake, ThreadMode, ThreadPage
from ..services import threads
from ..services.access import DiscordAccess
from .common import READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def list_threads(
        channel_id: Snowflake,
        mode: ThreadMode = "active",
        limit: PageLimit = 50,
        cursor: Cursor | None = None,
    ) -> ThreadPage:
        """List threads in a parent; reuse next_cursor with the same channel/mode.

        Archived modes: public, private (Manage Threads), joined_private (bot's memberships).
        Active order: descending ID. Archives: descending archive time, or ID for joined_private.
        """
        async with access.operation():
            return await threads.list_threads(access, channel_id, mode, limit, cursor)

    @mcp.tool(annotations=READ)
    async def get_thread_info(thread_id: Snowflake) -> ChannelInfo:
        """Get a thread directly by ID, including accessible archived threads absent from cache."""
        async with access.operation():
            return await threads.get_thread_info(access, thread_id)
