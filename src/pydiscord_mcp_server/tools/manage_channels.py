from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field, StrictBool

from ..models import (
    AllowMentions,
    ChannelInfo,
    ChannelPage,
    MessageContent,
    MessageInfo,
    PageLimit,
    Snowflake,
    ThreadPage,
)
from ..models.management import (
    CategoryUpdate,
    ForumInfo,
    ForumPostUpdate,
    ForumTagInfo,
    ForumUpdate,
    MutationResult,
    Name,
    Page,
    Position,
    Reason,
    TextChannelUpdate,
    VoiceChannelUpdate,
)
from ..services import manage_channels as service
from ..services import resources, threads
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, READ, WRITE


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=WRITE)
    async def create_text_channel(
        name: Name,
        guild_id: Snowflake | None = None,
        settings: TextChannelUpdate | None = None,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Create a text channel; settings includes topic, slowmode, category and position."""
        async with access.operation():
            return await service.create_text_channel(access, name, guild_id, settings, reason)

    @mcp.tool(annotations=EDIT)
    async def edit_text_channel(
        channel_id: Snowflake,
        settings: TextChannelUpdate,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Update supplied text/news channel fields; explicit category_id=null removes category."""
        async with access.operation():
            return await service.edit_text_channel(access, channel_id, settings, reason)

    @mcp.tool(annotations=DELETE)
    async def delete_channel(channel_id: Snowflake, reason: Reason | None = None) -> MutationResult:
        """Permanently delete a guild channel or thread and its messages."""
        async with access.operation():
            return await service.delete_channel(access, channel_id, reason)

    @mcp.tool(annotations=READ)
    async def find_channel(
        name: Name,
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> ChannelPage:
        """Find exact case-insensitive channel names in one guild; duplicate names are returned."""
        async with access.operation():
            return await service.find_channel(access, name, guild_id, limit=limit, after=after)

    @mcp.tool(annotations=EDIT)
    async def move_channel(
        channel_id: Snowflake,
        category_id: Snowflake | None = None,
        position: Position | None = None,
        remove_category: StrictBool = False,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Move a channel within its guild; choose a category or explicit remove_category."""
        async with access.operation():
            return await service.move_channel(
                access, channel_id, category_id, position, remove_category, reason
            )

    @mcp.tool(annotations=WRITE)
    async def create_category(
        name: Name,
        guild_id: Snowflake | None = None,
        position: Position | None = None,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Create a category in the selected guild."""
        async with access.operation():
            return await service.create_category(access, name, guild_id, position, reason)

    @mcp.tool(annotations=EDIT)
    async def edit_category(
        category_id: Snowflake,
        settings: CategoryUpdate,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Rename a category or change its position."""
        async with access.operation():
            return await service.edit_category(access, category_id, settings, reason)

    @mcp.tool(annotations=DELETE)
    async def delete_category(
        category_id: Snowflake,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Delete a category; Discord keeps its child channels without that category."""
        async with access.operation():
            return await service.delete_category(access, category_id, reason)

    @mcp.tool(annotations=READ)
    async def find_category(
        name: Name,
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> ChannelPage:
        """Find exact case-insensitive category names; next_cursor goes in after."""
        async with access.operation():
            return await service.find_channel(access, name, guild_id, True, limit, after)

    @mcp.tool(annotations=READ)
    async def list_channels_in_category(
        category_id: Snowflake,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> ChannelPage:
        """List category children by ascending ID; next_cursor goes in after."""
        async with access.operation():
            return await service.list_channels_in_category(access, category_id, limit, after)

    @mcp.tool(annotations=WRITE)
    async def create_voice_channel(
        name: Name,
        guild_id: Snowflake | None = None,
        settings: VoiceChannelUpdate | None = None,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Create a voice channel; Discord enforces the guild's bitrate limit."""
        async with access.operation():
            return await service.create_voice_channel(access, name, guild_id, settings, reason)

    @mcp.tool(annotations=WRITE)
    async def create_stage_channel(
        name: Name,
        guild_id: Snowflake | None = None,
        settings: VoiceChannelUpdate | None = None,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Create a stage channel; guild must support stages."""
        async with access.operation():
            return await service.create_voice_channel(
                access, name, guild_id, settings, reason, True
            )

    @mcp.tool(annotations=EDIT)
    async def edit_voice_channel(
        channel_id: Snowflake,
        settings: VoiceChannelUpdate,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Edit a voice/stage channel; rtc_region=null restores automatic region."""
        async with access.operation():
            return await service.edit_voice_channel(access, channel_id, settings, reason)

    @mcp.tool(annotations=WRITE)
    async def create_forum_channel(
        name: Name,
        guild_id: Snowflake | None = None,
        settings: ForumUpdate | None = None,
        reason: Reason | None = None,
    ) -> ForumInfo:
        """Create a forum with optional guidelines and defaults; guild feature required."""
        async with access.operation():
            return await service.create_forum_channel(access, name, guild_id, settings, reason)

    @mcp.tool(annotations=EDIT)
    async def edit_forum_channel(
        channel_id: Snowflake,
        settings: ForumUpdate,
        reason: Reason | None = None,
    ) -> ForumInfo:
        """Edit a forum/media channel's name, guidelines, category, layout and defaults."""
        async with access.operation():
            return await service.edit_forum_channel(access, channel_id, settings, reason)

    @mcp.tool(annotations=READ)
    async def list_forum_channels(
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> ChannelPage:
        """List forum/media channels; next_cursor goes in after."""
        async with access.operation():
            return await service.list_forum_channels(access, guild_id, limit, after)

    @mcp.tool(annotations=READ)
    async def get_forum_channel_info(channel_id: Snowflake) -> ForumInfo:
        """Get a forum/media channel's metadata, tags and defaults."""
        async with access.operation():
            return resources.forum_info(await resources.forum(access, channel_id))

    @mcp.tool(annotations=READ)
    async def list_forum_tags(channel_id: Snowflake) -> Page[ForumTagInfo]:
        """List tags in one forum (Discord bounds the number of tags)."""
        async with access.operation():
            channel = await resources.forum(access, channel_id)
            return Page[ForumTagInfo](items=[resources.tag_info(t) for t in channel.available_tags])

    @mcp.tool(annotations=WRITE)
    async def create_forum_post(
        channel_id: Snowflake,
        title: Name,
        content: MessageContent,
        tag_ids: Annotated[list[Snowflake], Field(max_length=5)] | None = None,
        allow_mentions: AllowMentions = False,
        reason: Reason | None = None,
    ) -> MessageInfo:
        """Create a forum post with its first message; tag IDs must belong to the forum."""
        async with access.operation():
            return await service.create_forum_post(
                access, channel_id, title, content, tag_ids, allow_mentions, reason
            )

    @mcp.tool(annotations=READ)
    async def list_forum_posts(
        channel_id: Snowflake,
        limit: PageLimit = 50,
        cursor: str | None = None,
    ) -> ThreadPage:
        """List active posts in one forum/media channel; next_cursor goes in cursor."""
        async with access.operation():
            await resources.forum(access, channel_id)
            return await threads.list_threads(access, channel_id, "active", limit, cursor)

    @mcp.tool(annotations=EDIT)
    async def modify_forum_post(
        post_id: Snowflake,
        settings: ForumPostUpdate,
        reason: Reason | None = None,
    ) -> ChannelInfo:
        """Lock, archive, pin or change tags on a forum post; [] clears tags."""
        async with access.operation():
            return await service.modify_forum_post(access, post_id, settings, reason)

    @mcp.tool(annotations=READ)
    async def list_active_threads(
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> ChannelPage:
        """List accessible active guild threads, ascending IDs; next_cursor goes in after."""
        async with access.operation():
            return await service.list_active_threads(access, guild_id, limit, after)
