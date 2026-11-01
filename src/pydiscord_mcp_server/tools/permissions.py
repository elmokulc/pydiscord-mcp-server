from typing import Literal

from mcp.server import MCPServer

from ..models import PageLimit, Snowflake
from ..models.management import MutationResult, OverwriteChanges, OverwriteInfo, Page, Reason
from ..services import permissions
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def list_channel_permission_overwrites(
        channel_id: Snowflake,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> Page[OverwriteInfo]:
        """List explicit role/member channel overwrites by ID; next_cursor goes in after."""
        async with access.operation():
            return await permissions.list_channel_permission_overwrites(
                access, channel_id, limit, after
            )

    @mcp.tool(annotations=EDIT)
    async def upsert_role_channel_permissions(
        channel_id: Snowflake,
        role_id: Snowflake,
        changes: OverwriteChanges,
        reason: Reason | None = None,
    ) -> OverwriteInfo:
        """Merge supplied role permissions: true=allow, false=deny, null=inherit."""
        async with access.operation():
            return await permissions.upsert_permissions(
                access, channel_id, role_id, "role", changes, reason
            )

    @mcp.tool(annotations=EDIT)
    async def upsert_member_channel_permissions(
        channel_id: Snowflake,
        member_id: Snowflake,
        changes: OverwriteChanges,
        reason: Reason | None = None,
    ) -> OverwriteInfo:
        """Merge supplied member permissions without replacing unrelated overwrite fields."""
        async with access.operation():
            return await permissions.upsert_permissions(
                access, channel_id, member_id, "member", changes, reason
            )

    @mcp.tool(annotations=DELETE)
    async def delete_channel_permission_overwrite(
        channel_id: Snowflake,
        target_id: Snowflake,
        target_type: Literal["role", "member"],
        reason: Reason | None = None,
    ) -> MutationResult:
        """Delete a complete role/member overwrite; inherited permissions then apply."""
        async with access.operation():
            return await permissions.delete_overwrite(
                access, channel_id, target_id, target_type, reason
            )
