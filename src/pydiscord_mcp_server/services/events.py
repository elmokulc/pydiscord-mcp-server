from datetime import UTC, datetime
from typing import Any, Literal

import discord

from ..models import UserInfo
from ..models.management import EventInfo, EventUpdate, MutationResult, Page
from . import resources
from .access import DiscordAccess
from .serialization import user_info


async def create_event(
    access: DiscordAccess,
    name: str,
    start_time: datetime,
    entity_type: Literal["voice", "stage_instance", "external"],
    guild_id: str | None,
    channel_id: str | None,
    end_time: datetime | None,
    location: str | None,
    description: str | None,
    reason: str | None,
) -> EventInfo:
    if start_time.tzinfo is None or start_time <= datetime.now(UTC):
        raise resources.invalid("Event start_time must be timezone-aware and in the future.")
    if end_time is not None and (end_time.tzinfo is None or end_time <= start_time):
        raise resources.invalid("Event end_time must be timezone-aware and after start_time.")
    guild = await access.guild(guild_id)
    data: dict[str, Any] = {
        "name": name,
        "start_time": start_time,
        "entity_type": getattr(discord.EntityType, entity_type),
        "privacy_level": discord.PrivacyLevel.guild_only,
        "reason": reason,
    }
    if description is not None:
        data["description"] = description
    if end_time is not None:
        data["end_time"] = end_time
    if entity_type == "external":
        if not location or end_time is None or channel_id is not None:
            raise resources.invalid("External events require location/end_time and no channel_id.")
        data.update(channel=None, location=location)
    else:
        if channel_id is None or location is not None:
            raise resources.invalid(
                "Voice/stage events require channel_id and no external location."
            )
        channel = await resources.vocal(access, channel_id)
        resources.same_guild(channel, guild)
        if (entity_type == "voice") != isinstance(channel, discord.VoiceChannel):
            raise resources.invalid("Event type must match voice/stage channel type.")
        data["channel"] = channel
    return resources.event_info(await guild.create_scheduled_event(**data))


async def edit_event(
    access: DiscordAccess,
    event_id: str,
    guild_id: str | None,
    settings: EventUpdate,
    reason: str | None,
) -> EventInfo:
    guild = await access.guild(guild_id)
    event = await resources.event(access, guild, event_id)
    data = settings.model_dump(exclude_unset=True, exclude_none=True)
    resources.require_changes(data)
    if settings.status is not None:
        data["status"] = getattr(discord.EventStatus, settings.status)
    start = settings.start_time or event.start_time
    end = settings.end_time or event.end_time
    if end is not None and end <= start:
        raise resources.invalid("Event end_time must be after start_time.")
    if settings.start_time is not None and settings.start_time <= datetime.now(UTC):
        raise resources.invalid("Updated start_time must be in the future.")
    if settings.location is not None and event.entity_type is not discord.EntityType.external:
        raise resources.invalid("Only external events have a location.")
    return resources.event_info(await event.edit(**data, reason=reason))


async def delete_event(
    access: DiscordAccess,
    event_id: str,
    guild_id: str | None,
    reason: str | None,
) -> MutationResult:
    guild = await access.guild(guild_id)
    event = await resources.event(access, guild, event_id)
    await event.delete(reason=reason)
    return MutationResult(resource_id=event_id, guild_id=str(guild.id), action="deleted")


async def list_events(
    access: DiscordAccess,
    guild_id: str | None,
    with_user_count: bool,
    limit: int,
    after: str | None,
) -> Page[EventInfo]:
    guild = await access.guild(guild_id)
    events = sorted(
        [
            e
            for e in await guild.fetch_scheduled_events(with_counts=with_user_count)
            if e.status in (discord.EventStatus.scheduled, discord.EventStatus.active)
            and (after is None or e.id > int(after))
        ],
        key=lambda e: e.id,
    )
    return Page[EventInfo](
        items=[resources.event_info(e) for e in events[:limit]],
        next_cursor=str(events[limit - 1].id) if len(events) > limit else None,
    )


async def event_users(
    access: DiscordAccess,
    event_id: str,
    guild_id: str | None,
    limit: int,
    after: str | None,
) -> Page[UserInfo]:
    if not access.settings.discord_intent_members:
        raise resources.invalid("Event user listing requires DISCORD_INTENT_MEMBERS=true.")
    guild = await access.guild(guild_id)
    event = await resources.event(access, guild, event_id)
    users = [
        u
        async for u in event.users(
            limit=limit + 1, after=discord.Object(int(after)) if after else None, oldest_first=True
        )
    ]
    return Page[UserInfo](
        items=[user_info(u) for u in users[:limit]],
        next_cursor=str(users[limit - 1].id) if len(users) > limit else None,
    )
