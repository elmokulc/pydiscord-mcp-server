import discord

from ..errors import DiscordToolError
from ..models import ActionResult, MessageInfo, MessagePage
from .access import DiscordAccess
from .messages import ReplyOptions, read_history
from .serialization import message_info


async def private_channel(
    access: DiscordAccess, user_id: str, guild_id: str | None
) -> discord.DMChannel:
    if not access.settings.discord_enable_dms:
        raise DiscordToolError("ACCESS_DENIED", "Private tools require DISCORD_ENABLE_DMS=true.")
    # Direct user IDs still require membership in the selected allowed guild.
    guild = await access.guild(guild_id)
    # Refresh membership: cached members can outlive their departure when Members intent is off.
    member = await guild.fetch_member(int(user_id))
    return member.dm_channel or await member.create_dm()


async def send_private_message(
    access: DiscordAccess,
    user_id: str,
    content: str,
    guild_id: str | None,
    reply_to_message_id: str | None,
    allow_mentions: bool,
) -> MessageInfo:
    channel = await private_channel(access, user_id, guild_id)
    reply: ReplyOptions = {}
    if reply_to_message_id:
        reply["reference"] = (await channel.fetch_message(int(reply_to_message_id))).to_reference()
    return message_info(
        await channel.send(
            content,
            **reply,
            allowed_mentions=discord.AllowedMentions.all()
            if allow_mentions
            else discord.AllowedMentions.none(),
        ),
        allow_dm=True,
    )


async def read_private_messages(
    access: DiscordAccess,
    user_id: str,
    guild_id: str | None,
    limit: int,
    before: str | None,
    after: str | None,
    around: str | None,
) -> MessagePage:
    channel = await private_channel(access, user_id, guild_id)
    return await read_history(channel, limit, before, after, around, allow_dm=True)


async def edit_private_message(
    access: DiscordAccess,
    user_id: str,
    message_id: str,
    content: str,
    guild_id: str | None,
    allow_mentions: bool,
) -> MessageInfo:
    channel = await private_channel(access, user_id, guild_id)
    message = await channel.fetch_message(int(message_id))
    if message.author.id != access.bot_id():
        raise DiscordToolError("ACCESS_DENIED", "Only this bot's private messages can be edited.")
    return message_info(
        await message.edit(
            content=content,
            allowed_mentions=discord.AllowedMentions.all()
            if allow_mentions
            else discord.AllowedMentions.none(),
        ),
        allow_dm=True,
    )


async def delete_private_message(
    access: DiscordAccess,
    user_id: str,
    message_id: str,
    guild_id: str | None,
) -> ActionResult:
    channel = await private_channel(access, user_id, guild_id)
    message = await channel.fetch_message(int(message_id))
    if message.author.id != access.bot_id():
        raise DiscordToolError("ACCESS_DENIED", "Only this bot's private messages can be deleted.")
    await message.delete()
    return ActionResult(channel_id=str(channel.id), message_id=message_id, action="deleted")
