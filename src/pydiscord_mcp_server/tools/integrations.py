from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field, StrictBool

from ..models import AllowMentions, MessageContent, MessageInfo, PageLimit, Snowflake
from ..models.management import (
    EmojiInfo,
    InviteInfo,
    MutationResult,
    Name,
    Page,
    Reason,
    WebhookInfo,
)
from ..services import integrations, resources
from ..services.access import DiscordAccess
from .common import DELETE, EDIT, READ, WRITE

EmojiName = Annotated[str, Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_]+$")]
RoleIds = Annotated[list[Snowflake], Field(max_length=250)]
InviteCode = Annotated[
    str, Field(min_length=1, max_length=200, description="Invite code or Discord invite URL")
]


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=WRITE)
    async def create_webhook(
        channel_id: Snowflake,
        name: Name,
        reason: Reason | None = None,
    ) -> WebhookInfo:
        """Create a webhook; returns its ID and metadata without token or secret URL."""
        async with access.operation():
            return await integrations.create_webhook(access, channel_id, name, reason)

    @mcp.tool(annotations=READ)
    async def list_webhooks(
        channel_id: Snowflake,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> Page[WebhookInfo]:
        """List webhook metadata in a channel, without tokens; next_cursor goes in after."""
        async with access.operation():
            return await integrations.list_webhooks(access, channel_id, limit, after)

    @mcp.tool(annotations=DELETE)
    async def delete_webhook(
        webhook_id: Snowflake,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Delete a webhook after checking its owning guild and channel."""
        async with access.operation():
            return await integrations.delete_webhook(access, webhook_id, reason)

    @mcp.tool(annotations=WRITE)
    async def send_webhook_message(
        webhook_id: Snowflake,
        content: MessageContent,
        allow_mentions: AllowMentions = False,
        thread_id: Snowflake | None = None,
    ) -> MessageInfo:
        """Send via a bot-managed webhook ID; optional thread must belong to its channel."""
        async with access.operation():
            return await integrations.send_webhook_message(
                access, webhook_id, content, allow_mentions, thread_id
            )

    @mcp.tool(annotations=WRITE)
    async def create_invite(
        channel_id: Snowflake,
        max_age: Annotated[int, Field(strict=True, ge=0, le=604800)] = 86400,
        max_uses: Annotated[int, Field(strict=True, ge=0, le=100)] = 0,
        temporary: StrictBool = False,
        unique: StrictBool = True,
        reason: Reason | None = None,
    ) -> InviteInfo:
        """Create a channel invite; max_age=0 never expires; max_uses=0 is unlimited."""
        async with access.operation():
            return await integrations.create_invite(
                access, channel_id, max_age, max_uses, temporary, unique, reason
            )

    @mcp.tool(annotations=READ)
    async def list_invites(
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Annotated[str, Field(max_length=200)] | None = None,
    ) -> Page[InviteInfo]:
        """List guild invites by code, with usage statistics; next_cursor goes in after."""
        async with access.operation():
            return await integrations.list_invites(access, guild_id, limit, after)

    @mcp.tool(annotations=DELETE)
    async def delete_invite(code: InviteCode, reason: Reason | None = None) -> MutationResult:
        """Revoke a guild invite after checking the guild allowlist."""
        async with access.operation():
            return await integrations.delete_invite(access, code, reason)

    @mcp.tool(annotations=READ)
    async def get_invite_details(code: InviteCode) -> InviteInfo:
        """Fetch a guild invite's public details; configured guild restrictions still apply."""
        async with access.operation():
            return resources.invite_info(await integrations.resolve_invite(access, code))

    @mcp.tool(annotations=READ)
    async def list_emojis(
        guild_id: Snowflake | None = None,
        limit: PageLimit = 50,
        after: Snowflake | None = None,
    ) -> Page[EmojiInfo]:
        """List custom guild emojis and role restrictions; next_cursor goes in after."""
        async with access.operation():
            return await integrations.list_emojis(access, guild_id, limit, after)

    @mcp.tool(annotations=READ)
    async def get_emoji_details(
        emoji_id: Snowflake, guild_id: Snowflake | None = None
    ) -> EmojiInfo:
        """Get custom emoji metadata from cache then REST within one guild."""
        async with access.operation():
            guild = await access.guild(guild_id)
            return resources.emoji_info(await resources.emoji(access, guild, emoji_id))

    @mcp.tool(annotations=WRITE)
    async def create_emoji(
        name: EmojiName,
        image_base64: Annotated[str, Field(min_length=1, max_length=350000)],
        guild_id: Snowflake | None = None,
        role_ids: RoleIds | None = None,
        reason: Reason | None = None,
    ) -> EmojiInfo:
        """Upload a custom emoji from base64 image data (max 256 KiB); no arbitrary URL fetching."""
        async with access.operation():
            return await integrations.create_emoji(
                access, name, image_base64, guild_id, role_ids, reason
            )

    @mcp.tool(annotations=EDIT)
    async def edit_emoji(
        emoji_id: Snowflake,
        guild_id: Snowflake | None = None,
        name: EmojiName | None = None,
        role_ids: RoleIds | None = None,
        reason: Reason | None = None,
    ) -> EmojiInfo:
        """Rename an emoji or replace its role restrictions; role_ids=[] allows every role."""
        async with access.operation():
            return await integrations.edit_emoji(access, emoji_id, guild_id, name, role_ids, reason)

    @mcp.tool(annotations=DELETE)
    async def delete_emoji(
        emoji_id: Snowflake,
        guild_id: Snowflake | None = None,
        reason: Reason | None = None,
    ) -> MutationResult:
        """Permanently delete a custom emoji from the selected guild."""
        async with access.operation():
            return await integrations.delete_emoji(access, emoji_id, guild_id, reason)
