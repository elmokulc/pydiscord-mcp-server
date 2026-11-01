from typing import Any

import discord

from ..models import ChannelInfo, ChannelPage, MessageInfo
from ..models.management import (
    CategoryUpdate,
    ForumInfo,
    ForumPostUpdate,
    ForumUpdate,
    MutationResult,
    TextChannelUpdate,
    VoiceChannelUpdate,
)
from . import resources
from .access import DiscordAccess
from .serialization import channel_info, message_info

ChannelUpdate = TextChannelUpdate | VoiceChannelUpdate | ForumUpdate


async def options(
    access: DiscordAccess, guild: discord.Guild, update: ChannelUpdate
) -> dict[str, Any]:
    data = update.model_dump(exclude_unset=True, exclude_none=True)
    data.pop("category_id", None)
    if "category_id" in update.model_fields_set:
        data["category"] = await resources.category(access, update.category_id, guild)
    if isinstance(update, VoiceChannelUpdate) and "rtc_region" in update.model_fields_set:
        data["rtc_region"] = update.rtc_region
    if isinstance(update, ForumUpdate):
        if update.default_sort_order is not None:
            data["default_sort_order"] = getattr(discord.ForumOrderType, update.default_sort_order)
        if update.default_layout is not None:
            data["default_layout"] = getattr(discord.ForumLayoutType, update.default_layout)
    return data


async def create_text_channel(
    access: DiscordAccess,
    name: str,
    guild_id: str | None,
    settings: TextChannelUpdate | None,
    reason: str | None,
) -> ChannelInfo:
    guild = await access.guild(guild_id)
    data = await options(access, guild, settings) if settings else {}
    data["name"] = name
    return channel_info(await guild.create_text_channel(**data, reason=reason))


async def edit_text_channel(
    access: DiscordAccess,
    channel_id: str,
    settings: TextChannelUpdate,
    reason: str | None,
) -> ChannelInfo:
    channel = await access.channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        raise resources.invalid("Resource must be a text/news channel.")
    data = await options(access, channel.guild, settings)
    resources.require_changes(data)
    updated = await channel.edit(**data, reason=reason)
    return channel_info(updated or channel)


async def delete_channel(
    access: DiscordAccess, channel_id: str, reason: str | None
) -> MutationResult:
    channel = await access.channel(channel_id)
    await channel.delete(reason=reason)
    return MutationResult(resource_id=channel_id, guild_id=str(channel.guild.id), action="deleted")


async def find_channel(
    access: DiscordAccess,
    name: str,
    guild_id: str | None,
    categories_only: bool = False,
    limit: int = 50,
    after: str | None = None,
) -> ChannelPage:
    guild = await access.guild(guild_id)
    channels = guild.channels or list(await guild.fetch_channels())
    selected = sorted(
        [
            c
            for c in channels
            if c.name.casefold() == name.casefold()
            and (not categories_only or isinstance(c, discord.CategoryChannel))
            and (after is None or c.id > int(after))
        ],
        key=lambda c: c.id,
    )
    return ChannelPage(
        items=[channel_info(c) for c in selected[:limit]],
        next_cursor=str(selected[limit - 1].id) if len(selected) > limit else None,
    )


async def move_channel(
    access: DiscordAccess,
    channel_id: str,
    category_id: str | None,
    position: int | None,
    remove_category: bool,
    reason: str | None,
) -> ChannelInfo:
    channel = await access.channel(channel_id)
    if not isinstance(
        channel,
        (discord.TextChannel, discord.ForumChannel, discord.VoiceChannel, discord.StageChannel),
    ):
        raise resources.invalid("Only non-category guild channels can be moved to categories.")
    if category_id is not None and remove_category:
        raise resources.invalid("Choose category_id or remove_category, not both.")
    data: dict[str, Any] = {}
    if category_id is not None or remove_category:
        data["category"] = await resources.category(access, category_id, channel.guild)
    if position is not None:
        data["position"] = position
    resources.require_changes(data)
    updated = await channel.edit(**data, reason=reason)
    return channel_info(updated or channel)


async def create_category(
    access: DiscordAccess,
    name: str,
    guild_id: str | None,
    position: int | None,
    reason: str | None,
) -> ChannelInfo:
    guild = await access.guild(guild_id)
    data: dict[str, Any] = {"position": position} if position is not None else {}
    return channel_info(await guild.create_category(name, **data, reason=reason))


async def edit_category(
    access: DiscordAccess,
    category_id: str,
    settings: CategoryUpdate,
    reason: str | None,
) -> ChannelInfo:
    channel = await access.channel(category_id)
    if not isinstance(channel, discord.CategoryChannel):
        raise resources.invalid("Resource must be a category.")
    data = settings.model_dump(exclude_unset=True, exclude_none=True)
    resources.require_changes(data)
    return channel_info(await channel.edit(**data, reason=reason) or channel)


async def delete_category(
    access: DiscordAccess,
    category_id: str,
    reason: str | None,
) -> MutationResult:
    channel = await access.channel(category_id)
    if not isinstance(channel, discord.CategoryChannel):
        raise resources.invalid("Resource must be a category.")
    return await delete_channel(access, category_id, reason)


async def list_channels_in_category(
    access: DiscordAccess,
    category_id: str,
    limit: int,
    after: str | None,
) -> ChannelPage:
    channel = await access.channel(category_id)
    if not isinstance(channel, discord.CategoryChannel):
        raise resources.invalid("Resource must be a category.")
    children = channel.channels
    if not children:
        children = [c for c in await channel.guild.fetch_channels() if c.category_id == channel.id]
    selected = sorted(
        [c for c in children if after is None or c.id > int(after)], key=lambda c: c.id
    )
    return ChannelPage(
        items=[channel_info(c) for c in selected[:limit]],
        next_cursor=str(selected[limit - 1].id) if len(selected) > limit else None,
    )


async def create_voice_channel(
    access: DiscordAccess,
    name: str,
    guild_id: str | None,
    settings: VoiceChannelUpdate | None,
    reason: str | None,
    stage: bool = False,
) -> ChannelInfo:
    guild = await access.guild(guild_id)
    data = await options(access, guild, settings) if settings else {}
    data["name"] = name
    channel: discord.VoiceChannel | discord.StageChannel
    if stage:
        channel = await guild.create_stage_channel(**data, reason=reason)
    else:
        channel = await guild.create_voice_channel(**data, reason=reason)
    return channel_info(channel)


async def edit_voice_channel(
    access: DiscordAccess,
    channel_id: str,
    settings: VoiceChannelUpdate,
    reason: str | None,
) -> ChannelInfo:
    channel = await resources.vocal(access, channel_id)
    data = await options(access, channel.guild, settings)
    resources.require_changes(data)
    return channel_info(await channel.edit(**data, reason=reason) or channel)


async def create_forum_channel(
    access: DiscordAccess,
    name: str,
    guild_id: str | None,
    settings: ForumUpdate | None,
    reason: str | None,
) -> ForumInfo:
    guild = await access.guild(guild_id)
    data = await options(access, guild, settings) if settings else {}
    data.pop("name", None)
    return resources.forum_info(await guild.create_forum(name, **data, reason=reason))


async def edit_forum_channel(
    access: DiscordAccess,
    channel_id: str,
    settings: ForumUpdate,
    reason: str | None,
) -> ForumInfo:
    channel = await resources.forum(access, channel_id)
    data = await options(access, channel.guild, settings)
    resources.require_changes(data)
    return resources.forum_info(await channel.edit(**data, reason=reason) or channel)


async def list_forum_channels(
    access: DiscordAccess,
    guild_id: str | None,
    limit: int,
    after: str | None,
) -> ChannelPage:
    guild = await access.guild(guild_id)
    channels = guild.channels or list(await guild.fetch_channels())
    selected = sorted(
        [
            c
            for c in channels
            if isinstance(c, discord.ForumChannel) and (after is None or c.id > int(after))
        ],
        key=lambda c: c.id,
    )
    return ChannelPage(
        items=[channel_info(c) for c in selected[:limit]],
        next_cursor=str(selected[limit - 1].id) if len(selected) > limit else None,
    )


def selected_tags(channel: discord.ForumChannel, tag_ids: list[str]) -> list[discord.ForumTag]:
    tags = {str(t.id): t for t in channel.available_tags}
    if any(t not in tags for t in tag_ids):
        raise resources.invalid("Every tag must belong to this forum.")
    return [tags[t] for t in tag_ids]


async def modify_forum_post(
    access: DiscordAccess,
    post_id: str,
    settings: ForumPostUpdate,
    reason: str | None,
) -> ChannelInfo:
    thread = await access.channel(post_id)
    if not isinstance(thread, discord.Thread):
        raise resources.invalid("Resource must be a forum post thread.")
    if thread.parent_id is None:
        raise resources.invalid("Thread parent is unavailable.")
    parent = await resources.forum(access, str(thread.parent_id))
    resources.same_guild(parent, thread.guild)
    data = settings.model_dump(exclude_unset=True, exclude_none=True)
    tags = data.pop("tag_ids", None)
    if tags is not None:
        data["applied_tags"] = selected_tags(parent, tags)
    resources.require_changes(data)
    return channel_info(await thread.edit(**data, reason=reason))


async def list_active_threads(
    access: DiscordAccess,
    guild_id: str | None,
    limit: int,
    after: str | None,
) -> ChannelPage:
    guild = await access.guild(guild_id)
    threads = sorted(
        [t for t in await guild.active_threads() if after is None or t.id > int(after)],
        key=lambda t: t.id,
    )
    return ChannelPage(
        items=[channel_info(t) for t in threads[:limit]],
        next_cursor=str(threads[limit - 1].id) if len(threads) > limit else None,
    )


async def create_forum_post(
    access: DiscordAccess,
    channel_id: str,
    title: str,
    content: str,
    tag_ids: list[str] | None,
    allow_mentions: bool,
    reason: str | None,
) -> MessageInfo:
    channel = await resources.forum(access, channel_id)
    tags = selected_tags(channel, tag_ids or [])
    result = await channel.create_thread(
        name=title,
        content=content,
        applied_tags=tags,
        allowed_mentions=discord.AllowedMentions.all()
        if allow_mentions
        else discord.AllowedMentions.none(),
        reason=reason,
    )
    return message_info(result.message)
