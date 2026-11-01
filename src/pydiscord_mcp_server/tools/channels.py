from mcp.server import MCPServer

from ..models import ChannelInfo, ChannelPage, PageLimit, Snowflake
from ..services import channels
from ..services.access import DiscordAccess
from .common import READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def list_channels(
        guild_id: Snowflake | None = None, limit: PageLimit = 50, after: Snowflake | None = None
    ) -> ChannelPage:
        """List guild channels (excluding threads), ID ascending; next_cursor goes in after."""
        async with access.operation():
            return await channels.list_channels(access, guild_id, limit, after)

    @mcp.tool(annotations=READ)
    async def get_channel_info(channel_id: Snowflake) -> ChannelInfo:
        """Get an allowed guild channel or thread, including uncached archived threads, by ID."""
        async with access.operation():
            return await channels.get_channel_info(access, channel_id)
