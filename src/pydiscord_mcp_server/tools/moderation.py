from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field, StrictBool

from ..models import MemberInfo, PageLimit, Snowflake
from ..models.management import BanInfo, MutationResult, Page, Reason
from ..services import moderation
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=DELETE)
    async def kick_member(
        member_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Kick a member; requires Kick Members and sufficient role hierarchy."""
        async with access.operation():
            return await moderation.kick_member(access, member_id, guild_id, reason)

    @mcp.tool(annotations=DELETE)
    async def ban_member(
        member_id: Snowflake,
        guild_id: Snowflake | None = None,
        delete_message_seconds: Annotated[int, Field(strict=True, ge=0, le=604800)] = 0,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Ban a user; optional message removal covers at most 7 days, disabled by default."""
        async with access.operation():
            return await moderation.ban_member(
                access, member_id, guild_id, reason, delete_message_seconds
            )

    @mcp.tool(annotations=EDIT)
    async def unban_member(
        member_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Remove a guild ban; does not automatically rejoin the user."""
        async with access.operation():
            return await moderation.unban_member(access, member_id, guild_id, reason)

    @mcp.tool(annotations=EDIT)
    async def timeout_member(
        member_id: Snowflake,
        duration_seconds: Annotated[int, Field(strict=True, ge=1, le=2419200)],
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Timeout a member for 1 second to 28 days; requires Moderate Members."""
        async with access.operation():
            return await moderation.timeout_member(
                access, member_id, guild_id, duration_seconds, reason
            )

    @mcp.tool(annotations=EDIT)
    async def remove_timeout(
        member_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Remove an existing member timeout."""
        async with access.operation():
            return await moderation.timeout_member(access, member_id, guild_id, None, reason)

    @mcp.tool(annotations=EDIT)
    async def set_nickname(
        member_id: Snowflake,
        nickname: Annotated[str, Field(max_length=32)] | None,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MemberInfo:
        """Set a guild nickname; explicit null restores the user's name."""
        async with access.operation():
            return await moderation.set_nickname(access, member_id, nickname, guild_id, reason)

    @mcp.tool(annotations=READ)
    async def get_bans(
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> Page[BanInfo]:
        """List guild bans with reasons, ascending user IDs; next_cursor goes in after."""
        async with access.operation():
            return await moderation.get_bans(access, guild_id, limit, after)

    @mcp.tool(annotations=EDIT)
    async def move_member(
        member_id: Snowflake,
        channel_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Move a connected member to a voice/stage channel in the same guild."""
        async with access.operation():
            return await moderation.move_member(access, member_id, channel_id, guild_id, reason)

    @mcp.tool(annotations=EDIT)
    async def disconnect_member(
        member_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Disconnect a guild member from voice."""
        async with access.operation():
            return await moderation.move_member(access, member_id, None, guild_id, reason)

    @mcp.tool(annotations=EDIT)
    async def modify_voice_state(
        member_id: Snowflake,
        guild_id: Snowflake | None = None,
        mute: StrictBool | None = None,
        deafen: StrictBool | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Set server mute/deafen flags on a member; at least one flag is required."""
        async with access.operation():
            return await moderation.modify_voice_state(
                access, member_id, guild_id, mute, deafen, reason
            )
