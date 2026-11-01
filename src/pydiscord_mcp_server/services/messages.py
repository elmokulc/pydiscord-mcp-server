from typing import TypedDict

import discord

from ..errors import DiscordToolError
from ..models import ActionResult, MessageInfo, MessagePage
from .access import DiscordAccess
from .serialization import message_info


class ReplyOptions(TypedDict, total=False):
    reference: discord.MessageReference


async def read_messages(
    access: DiscordAccess,
    channel_id: str,
    limit: int,
    before: str | None,
    after: str | None = None,
    around: str | None = None,
) -> MessagePage:
    channel = await access.message_channel(channel_id)
    return await read_history(channel, limit, before, after, around)


async def read_history(
    channel: discord.abc.Messageable,
    limit: int,
    before: str | None,
    after: str | None = None,
    around: str | None = None,
    *,
    allow_dm: bool = False,
) -> MessagePage:
    if sum(marker is not None for marker in (before, after, around)) > 1:
        raise DiscordToolError("INVALID_PARAMETER", "Choose only one of before, after or around.")
    oldest_first = after is not None
    messages = [
        m
        async for m in channel.history(
            limit=limit + 1,
            before=discord.Object(int(before)) if before else None,
            after=discord.Object(int(after)) if after else None,
            around=discord.Object(int(around)) if around else None,
            oldest_first=oldest_first,
        )
    ]
    page = messages[:limit]
    return MessagePage(
        items=[message_info(m, allow_dm=allow_dm) for m in page],
        next_cursor=str(page[-1].id) if len(messages) > limit and around is None else None,
        order="oldest_first" if oldest_first else "newest_first",
        cursor_parameter=None if around is not None else "after" if oldest_first else "before",
    )


async def get_message(access: DiscordAccess, channel_id: str, message_id: str) -> MessageInfo:
    channel = await access.message_channel(channel_id)
    return message_info(await access.message(channel, message_id))


async def send_message(
    access: DiscordAccess,
    channel_id: str,
    content: str,
    reply_to_message_id: str | None,
    allow_mentions: bool,
) -> MessageInfo:
    channel = await access.message_channel(channel_id)
    reply: ReplyOptions = {}
    if reply_to_message_id:
        # Fetch verifies that the target exists and belongs to this channel.
        target = await access.message(channel, reply_to_message_id)
        reply["reference"] = target.to_reference(fail_if_not_exists=True)
    message = await channel.send(
        content,
        **reply,
        allowed_mentions=discord.AllowedMentions.all()
        if allow_mentions
        else discord.AllowedMentions.none(),
    )
    return message_info(message)


async def edit_message(
    access: DiscordAccess, channel_id: str, message_id: str, content: str, allow_mentions: bool
) -> MessageInfo:
    channel = await access.message_channel(channel_id)
    message = await access.message(channel, message_id)
    if message.author.id != access.bot_id():
        raise DiscordToolError("ACCESS_DENIED", "Only the bot's own messages can be edited.")
    edited = await message.edit(
        content=content,
        allowed_mentions=discord.AllowedMentions.all()
        if allow_mentions
        else discord.AllowedMentions.none(),
    )
    return message_info(edited)


async def delete_message(
    access: DiscordAccess, channel_id: str, message_id: str, allow_other_author: bool
) -> ActionResult:
    channel = await access.message_channel(channel_id)
    message = await access.message(channel, message_id)
    if message.author.id != access.bot_id():
        if not allow_other_author:
            raise DiscordToolError(
                "ACCESS_DENIED",
                "Deleting another member's message requires allow_other_author=true.",
            )
        await access.require_manage_messages(channel)
    await message.delete()
    return ActionResult(channel_id=channel_id, message_id=message_id, action="deleted")


async def add_reaction(
    access: DiscordAccess, channel_id: str, message_id: str, emoji: str
) -> ActionResult:
    channel = await access.message_channel(channel_id)
    message = await access.message(channel, message_id)
    await message.add_reaction(emoji)
    return ActionResult(channel_id=channel_id, message_id=message_id, action="reaction_added")


async def remove_reaction(
    access: DiscordAccess, channel_id: str, message_id: str, emoji: str, member_id: str | None
) -> ActionResult:
    channel = await access.message_channel(channel_id)
    target_id = int(member_id) if member_id else access.bot_id()
    if target_id != access.bot_id():
        await access.require_manage_messages(channel)
    message = await access.message(channel, message_id)
    await message.remove_reaction(emoji, discord.Object(target_id))
    return ActionResult(channel_id=channel_id, message_id=message_id, action="reaction_removed")
