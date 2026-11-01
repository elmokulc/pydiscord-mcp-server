import discord

from ..models.management import HistorySearchResult
from . import resources
from .access import DiscordAccess
from .serialization import message_info


async def search_messages(
    access: DiscordAccess,
    channel_id: str,
    query: str,
    limit: int,
    scan_limit: int,
    before: str | None,
) -> HistorySearchResult:
    if not query.strip():
        raise resources.invalid("Search query cannot be blank.")
    channel = await access.message_channel(channel_id)
    scanned = 0
    last_id = None
    items = []
    exhausted = True
    async for message in channel.history(
        limit=scan_limit, before=discord.Object(int(before)) if before else None, oldest_first=False
    ):
        scanned += 1
        last_id = str(message.id)
        if query.casefold() in message.content.casefold():
            items.append(message_info(message))
        if len(items) >= limit:
            exhausted = False
            break
    if scanned >= scan_limit:
        exhausted = False
    return HistorySearchResult(
        items=items,
        scanned=scanned,
        scan_limit=scan_limit,
        next_cursor=None if exhausted else last_id,
        exhausted=exhausted,
    )


async def get_message_replies(
    access: DiscordAccess,
    channel_id: str,
    message_id: str,
    limit: int,
    scan_limit: int,
    after: str | None,
) -> HistorySearchResult:
    channel = await access.message_channel(channel_id)
    await access.message(channel, message_id)
    boundary = max(int(message_id), int(after)) if after else int(message_id)
    items = []
    scanned = 0
    last_id = None
    exhausted = True
    async for message in channel.history(
        limit=scan_limit, after=discord.Object(boundary), oldest_first=True
    ):
        scanned += 1
        last_id = str(message.id)
        reference = message.reference
        if (
            reference
            and reference.message_id == int(message_id)
            and reference.channel_id == channel.id
        ):
            items.append(message_info(message))
        if len(items) >= limit:
            exhausted = False
            break
    if scanned >= scan_limit:
        exhausted = False
    return HistorySearchResult(
        items=items,
        scanned=scanned,
        scan_limit=scan_limit,
        next_cursor=None if exhausted else last_id,
        exhausted=exhausted,
        cursor_parameter="after",
    )
