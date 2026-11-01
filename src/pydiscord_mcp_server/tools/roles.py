from mcp.server import MCPServer

from ..models import PageLimit, Snowflake
from ..models.management import MutationResult, Name, Page, Reason, RoleInfo, RoleUpdate
from ..services import roles
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, READ, WRITE


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def list_roles(
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> Page[RoleInfo]:
        """List guild roles by ID; permission bitsets are decimal strings; cursor goes in after."""
        async with access.operation():
            return await roles.list_roles(access, guild_id, limit, after)

    @mcp.tool(annotations=WRITE)
    async def create_role(
        name: Name,
        guild_id: Snowflake | None = None,
        settings: RoleUpdate | None = None,
        reason: Reason | None = None,
    ) -> RoleInfo:
        """Create a role with optional permissions, RGB colour, hoist and mentionability."""
        async with access.operation():
            return await roles.create_role(access, name, guild_id, settings, reason)

    @mcp.tool(annotations=EDIT)
    async def edit_role(
        role_id: Snowflake,
        settings: RoleUpdate,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> RoleInfo:
        """Edit an existing role; Discord enforces permission and role hierarchy restrictions."""
        async with access.operation():
            return await roles.edit_role(access, role_id, guild_id, settings, reason)

    @mcp.tool(annotations=DELETE)
    async def delete_role(
        role_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Permanently delete a guild role."""
        async with access.operation():
            return await roles.delete_role(access, role_id, guild_id, reason)

    @mcp.tool(annotations=EDIT)
    async def assign_role(
        member_id: Snowflake,
        role_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Assign one role to a guild member without replacing their other roles."""
        async with access.operation():
            return await roles.member_role(access, member_id, role_id, guild_id, reason)

    @mcp.tool(annotations=EDIT)
    async def remove_role(
        member_id: Snowflake,
        role_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Remove one role from a guild member without replacing their other roles."""
        async with access.operation():
            return await roles.member_role(access, member_id, role_id, guild_id, reason, True)
