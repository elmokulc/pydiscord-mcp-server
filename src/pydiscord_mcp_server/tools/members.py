from mcp.server import MCPServer

from ..models import MemberInfo, MemberQuery, MemberSearchResult, PageLimit, Snowflake
from ..models.management import UserLookupInfo
from ..services import members
from ..services.access import DiscordAccess
from .common import READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def get_member(member_id: Snowflake, guild_id: Snowflake | None = None) -> MemberInfo:
        """Get one guild member from cache then REST; no exhaustive member enumeration."""
        async with access.operation():
            return await members.get_member(access, member_id, guild_id)

    @mcp.tool(annotations=READ)
    async def search_members(
        query: MemberQuery, guild_id: Snowflake | None = None, limit: PageLimit = 25
    ) -> MemberSearchResult:
        """Search ID or available member names/nicknames/global names; bounded, not exhaustive.

        Names use cached members plus Gateway prefix results and require Members intent.
        ID queries use a targeted REST fallback. No pagination or global user search.
        """
        async with access.operation():
            return await members.search_members(access, query, guild_id, limit)

    @mcp.tool(annotations=READ)
    async def get_member_by_id(
        user_id: Snowflake,
        guild_id: Snowflake | None = None,
    ) -> MemberInfo:
        """Get a member by stable ID; equivalent to get_member, including roles and nickname."""
        async with access.operation():
            return await members.get_member(access, user_id, guild_id)

    @mcp.tool(annotations=READ)
    async def get_user_id_by_name(
        username: MemberQuery,
        guild_id: Snowflake | None = None,
    ) -> UserLookupInfo:
        """Resolve an exact username from the available cache/prefix query; use IDs if ambiguous."""
        async with access.operation():
            return await members.get_user_id_by_name(access, username, guild_id)
