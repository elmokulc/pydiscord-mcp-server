from typing import Annotated, Literal

from mcp.server import MCPServer
from pydantic import AwareDatetime, Field, StrictBool

from ..models import PageLimit, Snowflake, UserInfo
from ..models.management import EventInfo, EventUpdate, MutationResult, Name, Page, Reason
from ..services import events
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, READ, WRITE


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=WRITE)
    async def create_guild_scheduled_event(
        name: Name,
        start_time: AwareDatetime,
        entity_type: Literal["voice", "stage_instance", "external"],
        guild_id: Snowflake | None = None,
        channel_id: Snowflake | None = None,
        end_time: AwareDatetime | None = None,
        location: Annotated[str, Field(min_length=1, max_length=100)] | None = None,
        description: Annotated[str, Field(max_length=1000)] | None = None,
        reason: Reason | None = None,
    ) -> EventInfo:
        """Schedule an external event or a voice/stage event in a channel.

        External events require location and end_time; channel events require channel_id.
        """
        async with access.operation():
            return await events.create_event(
                access,
                name,
                start_time,
                entity_type,
                guild_id,
                channel_id,
                end_time,
                location,
                description,
                reason,
            )

    @mcp.tool(annotations=EDIT)
    async def edit_guild_scheduled_event(
        event_id: Snowflake,
        settings: EventUpdate,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> EventInfo:
        """Update event details or status; timestamps require an explicit timezone."""
        async with access.operation():
            return await events.edit_event(access, event_id, guild_id, settings, reason)

    @mcp.tool(annotations=DELETE)
    async def delete_guild_scheduled_event(
        event_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Permanently delete a scheduled guild event."""
        async with access.operation():
            return await events.delete_event(access, event_id, guild_id, reason)

    @mcp.tool(annotations=READ)
    async def list_guild_scheduled_events(
        guild_id: Snowflake | None = None,
        with_user_count: StrictBool = True,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> Page[EventInfo]:
        """List scheduled and active guild events by ID; next_cursor goes in after."""
        async with access.operation():
            return await events.list_events(access, guild_id, with_user_count, limit, after)

    @mcp.tool(annotations=READ)
    async def get_guild_scheduled_event_users(
        event_id: Snowflake,
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> Page[UserInfo]:
        """List users interested in an event by ascending user ID; next_cursor goes in after."""
        async with access.operation():
            return await events.event_users(access, event_id, guild_id, limit, after)
