from mcp.server import MCPServer

from ..models import GuildInfo, GuildPage, PageLimit, Snowflake
from ..services import guilds
from ..services.access import DiscordAccess
from .common import READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def list_guilds(limit: PageLimit = 50, after: Snowflake | None = None) -> GuildPage:
        """List allowed guilds from the bot cache, ID ascending; pass next_cursor as after."""
        async with access.operation():
            return await guilds.list_guilds(access, limit, after)

    @mcp.tool(annotations=READ)
    async def get_guild_info(guild_id: Snowflake | None = None) -> GuildInfo:
        """Get a guild by ID, using DISCORD_GUILD_ID if omitted. Cache then REST."""
        async with access.operation():
            return await guilds.get_guild_info(access, guild_id)

    @mcp.tool(annotations=READ)
    async def get_server_info(guild_id: Snowflake | None = None) -> GuildInfo:
        """Get the selected server's identity, owner, member count and description."""
        async with access.operation():
            return await guilds.get_guild_info(access, guild_id)
