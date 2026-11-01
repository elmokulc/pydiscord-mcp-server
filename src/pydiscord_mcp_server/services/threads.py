import base64
import binascii
from datetime import datetime

import discord
from pydantic import BaseModel, ConfigDict, ValidationError

from ..errors import DiscordToolError
from ..models import ChannelInfo, Snowflake, ThreadMode, ThreadPage
from .access import DiscordAccess
from .serialization import channel_info


class ThreadCursor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel_id: Snowflake
    mode: ThreadMode
    before: str

    def encode(self) -> str:
        return base64.urlsafe_b64encode(self.model_dump_json().encode()).decode()


def decode_cursor(cursor: str, channel_id: str, mode: ThreadMode) -> str:
    try:
        data = ThreadCursor.model_validate_json(
            base64.b64decode(cursor, altchars=b"-_", validate=True)
        )
        if data.channel_id != channel_id or data.mode != mode:
            raise ValueError("Cursor does not match this channel/mode")
        if mode in ("active", "archived_joined_private"):
            from pydantic import TypeAdapter

            TypeAdapter(Snowflake).validate_python(data.before)
        else:
            date = datetime.fromisoformat(data.before)
            if date.tzinfo is None or date.utcoffset() is None:
                raise ValueError("Timezone required")
        return data.before
    except (ValidationError, ValueError, binascii.Error):
        raise DiscordToolError(
            "INVALID_PARAMETER", "Invalid thread cursor for this channel/mode."
        ) from None


async def get_thread_info(access: DiscordAccess, thread_id: str) -> ChannelInfo:
    channel = await access.channel(thread_id)
    if not isinstance(channel, discord.Thread):
        raise DiscordToolError("INVALID_PARAMETER", "Resource is not a thread.")
    return channel_info(channel)


async def list_threads(
    access: DiscordAccess, channel_id: str, mode: ThreadMode, limit: int, cursor: str | None
) -> ThreadPage:
    before = decode_cursor(cursor, channel_id, mode) if cursor else None
    channel = await access.channel(channel_id)
    if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
        raise DiscordToolError(
            "INVALID_PARAMETER", "Thread parent must be a text/forum/media channel."
        )
    if mode == "active":
        # Discord exposes one guild-wide endpoint for all active threads.
        threads = sorted(
            [
                t
                for t in await channel.guild.active_threads()
                if t.parent_id == channel.id and (before is None or t.id < int(before))
            ],
            key=lambda t: t.id,
            reverse=True,
        )
    else:
        boundary: discord.Object | datetime | None = None
        if before:
            boundary = (
                discord.Object(int(before))
                if mode == "archived_joined_private"
                else datetime.fromisoformat(before)
            )
        if isinstance(channel, discord.ForumChannel):
            if mode != "archived_public":
                raise DiscordToolError("INVALID_PARAMETER", "Forum/media threads are public.")
            iterator = channel.archived_threads(limit=limit + 1, before=boundary)
        else:
            iterator = channel.archived_threads(
                limit=limit + 1,
                before=boundary,
                private=mode != "archived_public",
                joined=mode == "archived_joined_private",
            )
        threads = [t async for t in iterator]
    page = threads[:limit]
    next_cursor = None
    if len(threads) > limit:
        last = page[-1]
        if mode in ("active", "archived_joined_private"):
            marker = str(last.id)
        elif last.archive_timestamp is not None:
            marker = last.archive_timestamp.isoformat()
        else:
            raise DiscordToolError(
                "DISCORD_UNAVAILABLE", "Discord did not return archive timestamp."
            )
        next_cursor = ThreadCursor(channel_id=channel_id, mode=mode, before=marker).encode()
    return ThreadPage(items=[channel_info(t) for t in page], next_cursor=next_cursor, mode=mode)
