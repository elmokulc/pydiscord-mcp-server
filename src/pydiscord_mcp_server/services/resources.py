"""Typed resource resolution and guild boundary checks used by administration tools."""

from typing import Any

import discord

from ..errors import DiscordToolError
from ..models.management import (
    EmojiInfo,
    EventInfo,
    ForumInfo,
    ForumTagInfo,
    InviteInfo,
    RoleInfo,
    WebhookInfo,
)
from .access import DiscordAccess, GuildChannel
from .serialization import channel_info


def invalid(message: str) -> DiscordToolError:
    return DiscordToolError("INVALID_PARAMETER", message)


def same_guild(channel: GuildChannel, guild: discord.Guild) -> None:
    if channel.guild.id != guild.id:
        raise invalid("Resources must belong to the same guild.")


async def category(
    access: DiscordAccess, category_id: str | None, guild: discord.Guild
) -> discord.CategoryChannel | None:
    if category_id is None:
        return None
    result = await access.channel(category_id)
    same_guild(result, guild)
    if not isinstance(result, discord.CategoryChannel):
        raise invalid("Resource must be a category.")
    return result


async def forum(access: DiscordAccess, channel_id: str) -> discord.ForumChannel:
    result = await access.channel(channel_id)
    if not isinstance(result, discord.ForumChannel):
        raise invalid("Resource must be a forum/media channel.")
    return result


async def vocal(
    access: DiscordAccess, channel_id: str
) -> discord.VoiceChannel | discord.StageChannel:
    result = await access.channel(channel_id)
    if not isinstance(result, (discord.VoiceChannel, discord.StageChannel)):
        raise invalid("Resource must be a voice/stage channel.")
    return result


async def role(access: DiscordAccess, guild: discord.Guild, role_id: str) -> discord.Role:
    access.check_guild(guild.id)
    result = guild.get_role(int(role_id))
    if result is None:
        result = next((r for r in await guild.fetch_roles() if r.id == int(role_id)), None)
    if result is None:
        raise DiscordToolError("NOT_FOUND", "Role does not exist in this guild.")
    return result


async def webhook(access: DiscordAccess, webhook_id: str) -> discord.Webhook:
    result = await access.client.fetch_webhook(int(webhook_id))
    if result.guild_id is None or result.channel_id is None:
        raise DiscordToolError("ACCESS_DENIED", "Webhook must belong to a guild channel.")
    access.check_guild(result.guild_id)
    channel = await access.channel(str(result.channel_id))
    if channel.guild.id != result.guild_id:
        raise DiscordToolError("ACCESS_DENIED", "Webhook guild/channel mismatch.")
    return result


async def event(
    access: DiscordAccess, guild: discord.Guild, event_id: str
) -> discord.ScheduledEvent:
    access.check_guild(guild.id)
    return guild.get_scheduled_event(int(event_id)) or await guild.fetch_scheduled_event(
        int(event_id)
    )


async def emoji(access: DiscordAccess, guild: discord.Guild, emoji_id: str) -> discord.Emoji:
    access.check_guild(guild.id)
    return guild.get_emoji(int(emoji_id)) or await guild.fetch_emoji(int(emoji_id))


def role_info(role: discord.Role) -> RoleInfo:
    return RoleInfo(
        id=str(role.id),
        guild_id=str(role.guild.id),
        name=role.name,
        permissions=str(role.permissions.value),
        colour=role.colour.value,
        position=role.position,
        hoist=role.hoist,
        mentionable=role.mentionable,
        managed=role.managed,
    )


def webhook_info(webhook: discord.Webhook) -> WebhookInfo:
    if webhook.guild_id is None or webhook.channel_id is None:
        raise invalid("Guild webhook expected.")
    return WebhookInfo(
        id=str(webhook.id),
        guild_id=str(webhook.guild_id),
        channel_id=str(webhook.channel_id),
        name=webhook.name,
        type=str(webhook.type),
    )


def invite_info(invite: discord.Invite) -> InviteInfo:
    if invite.guild is None:
        raise invalid("Guild invite expected.")
    return InviteInfo(
        code=invite.code,
        url=invite.url,
        guild_id=str(invite.guild.id),
        channel_id=str(invite.channel.id) if invite.channel else None,
        uses=invite.uses,
        max_uses=invite.max_uses,
        max_age=invite.max_age,
        temporary=invite.temporary,
        expires_at=invite.expires_at,
    )


def emoji_info(emoji: discord.Emoji) -> EmojiInfo:
    return EmojiInfo(
        id=str(emoji.id),
        guild_id=str(emoji.guild_id),
        name=emoji.name or "",
        animated=emoji.animated,
        available=emoji.available,
        role_ids=[str(r.id) for r in emoji.roles],
        url=str(emoji.url),
    )


def tag_info(tag: discord.ForumTag) -> ForumTagInfo:
    return ForumTagInfo(
        id=str(tag.id),
        name=tag.name,
        moderated=tag.moderated,
        emoji=str(tag.emoji) if tag.emoji else None,
    )


def forum_info(channel: discord.ForumChannel) -> ForumInfo:
    data = channel_info(channel).model_dump()
    data.update(
        tags=[tag_info(t) for t in channel.available_tags],
        nsfw=channel.nsfw,
        slowmode_delay=channel.slowmode_delay,
        default_thread_slowmode_delay=channel.default_thread_slowmode_delay,
        default_sort_order=str(channel.default_sort_order)
        if channel.default_sort_order is not None
        else None,
        default_layout=str(channel.default_layout),
    )
    return ForumInfo(**data)


def event_info(event: discord.ScheduledEvent) -> EventInfo:
    return EventInfo(
        id=str(event.id),
        guild_id=str(event.guild_id),
        name=event.name,
        description=event.description,
        entity_type=str(event.entity_type),
        status=str(event.status),
        channel_id=str(event.channel_id) if event.channel_id else None,
        location=event.location,
        start_time=event.start_time,
        end_time=event.end_time,
        user_count=event.user_count,
        url=event.url,
    )


def require_changes(changes: dict[str, Any]) -> None:
    if not changes:
        raise invalid("Provide at least one field to update.")
