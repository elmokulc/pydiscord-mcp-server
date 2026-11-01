from datetime import timedelta

import discord

from ..models import MemberInfo
from ..models.management import BanInfo, MutationResult, Page
from . import resources
from .access import DiscordAccess
from .serialization import member_info, user_info


async def kick_member(
    access: DiscordAccess,
    member_id: str,
    guild_id: str | None,
    reason: str | None,
) -> MutationResult:
    guild = await access.guild(guild_id)
    member = await access.member(guild, int(member_id))
    await member.kick(reason=reason)
    return MutationResult(resource_id=member_id, guild_id=str(guild.id), action="kicked")


async def ban_member(
    access: DiscordAccess,
    member_id: str,
    guild_id: str | None,
    reason: str | None,
    delete_message_seconds: int,
) -> MutationResult:
    guild = await access.guild(guild_id)
    await guild.ban(
        discord.Object(int(member_id)), reason=reason, delete_message_seconds=delete_message_seconds
    )
    return MutationResult(resource_id=member_id, guild_id=str(guild.id), action="banned")


async def unban_member(
    access: DiscordAccess,
    member_id: str,
    guild_id: str | None,
    reason: str | None,
) -> MutationResult:
    guild = await access.guild(guild_id)
    await guild.unban(discord.Object(int(member_id)), reason=reason)
    return MutationResult(resource_id=member_id, guild_id=str(guild.id), action="unbanned")


async def timeout_member(
    access: DiscordAccess,
    member_id: str,
    guild_id: str | None,
    duration_seconds: int | None,
    reason: str | None,
) -> MutationResult:
    guild = await access.guild(guild_id)
    member = await access.member(guild, int(member_id))
    await member.timeout(
        timedelta(seconds=duration_seconds) if duration_seconds else None, reason=reason
    )
    return MutationResult(
        resource_id=member_id,
        guild_id=str(guild.id),
        action="timed_out" if duration_seconds else "timeout_removed",
    )


async def set_nickname(
    access: DiscordAccess,
    member_id: str,
    nickname: str | None,
    guild_id: str | None,
    reason: str | None,
) -> MemberInfo:
    guild = await access.guild(guild_id)
    member = await access.member(guild, int(member_id))
    updated = await member.edit(nick=nickname, reason=reason)
    return member_info(updated or await guild.fetch_member(int(member_id)))


async def get_bans(
    access: DiscordAccess,
    guild_id: str | None,
    limit: int,
    after: str | None,
) -> Page[BanInfo]:
    guild = await access.guild(guild_id)
    bans = [
        b
        async for b in guild.bans(
            limit=limit + 1, after=discord.Object(int(after)) if after else discord.utils.MISSING
        )
    ]
    return Page[BanInfo](
        items=[BanInfo(user=user_info(b.user), reason=b.reason) for b in bans[:limit]],
        next_cursor=str(bans[limit - 1].user.id) if len(bans) > limit else None,
    )


async def move_member(
    access: DiscordAccess,
    member_id: str,
    channel_id: str | None,
    guild_id: str | None,
    reason: str | None,
) -> MutationResult:
    guild = await access.guild(guild_id)
    destination = await resources.vocal(access, channel_id) if channel_id else None
    if destination:
        resources.same_guild(destination, guild)
    member = await access.member(guild, int(member_id))
    await member.move_to(destination, reason=reason)
    return MutationResult(
        resource_id=member_id,
        guild_id=str(guild.id),
        action="voice_moved" if destination else "voice_disconnected",
    )


async def modify_voice_state(
    access: DiscordAccess,
    member_id: str,
    guild_id: str | None,
    mute: bool | None,
    deafen: bool | None,
    reason: str | None,
) -> MutationResult:
    data = {k: v for k, v in {"mute": mute, "deafen": deafen}.items() if v is not None}
    resources.require_changes(data)
    guild = await access.guild(guild_id)
    member = await access.member(guild, int(member_id))
    await member.edit(
        mute=mute if mute is not None else discord.utils.MISSING,
        deafen=deafen if deafen is not None else discord.utils.MISSING,
        reason=reason,
    )
    return MutationResult(
        resource_id=member_id, guild_id=str(guild.id), action="voice_state_modified"
    )
