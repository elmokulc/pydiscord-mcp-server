from datetime import timedelta

import discord

from ..errors import DiscordToolError
from ..models import MessageInfo, PageLimit, Snowflake, UserInfo
from ..models.management import Page
from ..models.polls import PollOption
from .access import DiscordAccess
from .serialization import message_info, user_info


async def create_poll(
    access: DiscordAccess,
    channel_id: str,
    question: str,
    answers: list[PollOption],
    duration_hours: int,
    allow_multiselect: bool,
) -> MessageInfo:
    if not question.strip():
        raise DiscordToolError("INVALID_PARAMETER", "Poll question cannot be blank.")
    channel = await access.message_channel(channel_id)
    poll = discord.Poll(question, timedelta(hours=duration_hours), multiple=allow_multiselect)
    for answer in answers:
        poll.add_answer(text=answer.text, emoji=answer.emoji)
    sent = await channel.send(poll=poll, allowed_mentions=discord.AllowedMentions.none())
    return message_info(sent)


async def get_poll(access: DiscordAccess, channel_id: str, message_id: str) -> MessageInfo:
    channel = await access.message_channel(channel_id)
    # Votes must be refreshed via REST instead of relying on cached message snapshots.
    message = await channel.fetch_message(int(message_id))
    if message.poll is None:
        raise DiscordToolError("INVALID_PARAMETER", "Message does not contain a native poll.")
    return message_info(message)


async def end_poll(access: DiscordAccess, channel_id: str, message_id: str) -> MessageInfo:
    channel = await access.message_channel(channel_id)
    message = await channel.fetch_message(int(message_id))
    if message.poll is None:
        raise DiscordToolError("INVALID_PARAMETER", "Message does not contain a native poll.")
    if message.author.id != access.bot_id():
        raise DiscordToolError("ACCESS_DENIED", "Only polls created by this bot can be ended.")
    return message_info(await message.end_poll())


async def get_poll_answer_voters(
    access: DiscordAccess,
    channel_id: str,
    message_id: str,
    answer_id: int,
    limit: PageLimit,
    after: Snowflake | None,
) -> Page[UserInfo]:
    channel = await access.message_channel(channel_id)
    message = await channel.fetch_message(int(message_id))
    if message.poll is None:
        raise DiscordToolError("INVALID_PARAMETER", "Message does not contain a native poll.")
    answer = message.poll.get_answer(answer_id)
    if answer is None:
        raise DiscordToolError("NOT_FOUND", "Poll answer does not exist.")
    users = [
        u
        async for u in answer.voters(
            limit=limit + 1, after=discord.Object(int(after)) if after else None
        )
    ]
    return Page[UserInfo](
        items=[user_info(u) for u in users[:limit]],
        next_cursor=str(users[limit - 1].id) if len(users) > limit else None,
    )
