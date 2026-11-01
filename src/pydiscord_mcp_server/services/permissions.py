from typing import Literal

import discord

from ..models.management import MutationResult, OverwriteChanges, OverwriteInfo, Page
from . import resources
from .access import DiscordAccess


async def permission_channel(access: DiscordAccess, channel_id: str) -> discord.abc.GuildChannel:
    channel = await access.channel(channel_id)
    if isinstance(channel, discord.Thread):
        raise resources.invalid("Threads inherit parent permissions; use the parent channel.")
    return channel


async def list_channel_permission_overwrites(
    access: DiscordAccess,
    channel_id: str,
    limit: int,
    after: str | None,
) -> Page[OverwriteInfo]:
    channel = await permission_channel(access, channel_id)
    entries = sorted(
        [
            (target, overwrite)
            for target, overwrite in channel.overwrites.items()
            if after is None or target.id > int(after)
        ],
        key=lambda entry: entry[0].id,
    )
    items = []
    for target, overwrite in entries[:limit]:
        allow, deny = overwrite.pair()
        role = isinstance(target, discord.Role) or (
            isinstance(target, discord.Object) and target.type is discord.Role
        )
        items.append(
            OverwriteInfo(
                target_id=str(target.id),
                target_type="role" if role else "member",
                allow=str(allow.value),
                deny=str(deny.value),
                permissions=dict(overwrite),
            )
        )
    return Page[OverwriteInfo](
        items=items, next_cursor=str(entries[limit - 1][0].id) if len(entries) > limit else None
    )


async def upsert_permissions(
    access: DiscordAccess,
    channel_id: str,
    target_id: str,
    target_type: Literal["role", "member"],
    changes: OverwriteChanges,
    reason: str | None,
) -> OverwriteInfo:
    channel = await permission_channel(access, channel_id)
    target = (
        await resources.role(access, channel.guild, target_id)
        if target_type == "role"
        else await access.member(channel.guild, int(target_id))
    )
    overwrite = channel.overwrites_for(target)
    overwrite.update(**changes.permissions)
    await channel.set_permissions(target, overwrite=overwrite, reason=reason)
    allow, deny = overwrite.pair()
    return OverwriteInfo(
        target_id=target_id,
        target_type=target_type,
        allow=str(allow.value),
        deny=str(deny.value),
        permissions=dict(overwrite),
    )


async def delete_overwrite(
    access: DiscordAccess,
    channel_id: str,
    target_id: str,
    target_type: Literal["role", "member"],
    reason: str | None,
) -> MutationResult:
    channel = await permission_channel(access, channel_id)
    target = (
        await resources.role(access, channel.guild, target_id)
        if target_type == "role"
        else await access.member(channel.guild, int(target_id))
    )
    await channel.set_permissions(target, overwrite=None, reason=reason)
    return MutationResult(
        resource_id=target_id,
        guild_id=str(channel.guild.id),
        action="channel_permission_overwrite_deleted",
    )
