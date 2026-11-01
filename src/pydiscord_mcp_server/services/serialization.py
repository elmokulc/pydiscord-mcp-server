import discord

from ..models import (
    AttachmentInfo,
    ChannelInfo,
    ComponentInfo,
    EmbedInfo,
    GuildInfo,
    MemberInfo,
    MentionInfo,
    MessageInfo,
    PollAnswerInfo,
    PollInfo,
    ReplyReference,
    StickerInfo,
    UserInfo,
    optional_id,
)
from .access import GuildChannel


def guild_info(guild: discord.Guild) -> GuildInfo:
    return GuildInfo(
        id=str(guild.id),
        name=guild.name,
        owner_id=optional_id(guild.owner_id),
        member_count=guild.member_count,
        description=guild.description,
    )


def channel_info(channel: GuildChannel) -> ChannelInfo:
    thread = channel if isinstance(channel, discord.Thread) else None
    return ChannelInfo(
        id=str(channel.id),
        guild_id=str(channel.guild.id),
        name=channel.name,
        type=str(channel.type),
        parent_id=optional_id(thread.parent_id if thread else channel.category_id),
        topic=getattr(channel, "topic", None),
        archived=thread.archived if thread else None,
        locked=thread.locked if thread else None,
        archive_timestamp=thread.archive_timestamp if thread else None,
        position=channel.position if isinstance(channel, discord.abc.GuildChannel) else None,
        nsfw=channel.nsfw
        if isinstance(
            channel,
            (discord.TextChannel, discord.ForumChannel, discord.VoiceChannel, discord.StageChannel),
        )
        else None,
        slowmode_delay=channel.slowmode_delay
        if isinstance(channel, (discord.TextChannel, discord.ForumChannel, discord.Thread))
        else None,
        bitrate=channel.bitrate
        if isinstance(channel, (discord.VoiceChannel, discord.StageChannel))
        else None,
        user_limit=channel.user_limit
        if isinstance(channel, (discord.VoiceChannel, discord.StageChannel))
        else None,
        rtc_region=channel.rtc_region
        if isinstance(channel, (discord.VoiceChannel, discord.StageChannel))
        else None,
        owner_id=optional_id(thread.owner_id) if thread else None,
        message_count=thread.message_count if thread else None,
        member_count=thread.member_count if thread else None,
        url=f"https://discord.com/channels/{channel.guild.id}/{channel.id}",
    )


def user_info(user: discord.User | discord.Member) -> UserInfo:
    return UserInfo(
        id=str(user.id),
        name=user.name,
        display_name=user.display_name,
        bot=user.bot,
        global_name=getattr(user, "global_name", None),
        discriminator=getattr(user, "discriminator", "0"),
    )


def member_info(member: discord.Member) -> MemberInfo:
    return MemberInfo(
        **user_info(member).model_dump(),
        guild_id=str(member.guild.id),
        nickname=member.nick,
        joined_at=member.joined_at,
        role_ids=[str(role.id) for role in member.roles],
    )


def poll_info(poll: discord.Poll) -> PollInfo:
    return PollInfo(
        question=poll.question,
        allow_multiselect=poll.multiple,
        expires_at=poll.expires_at,
        finalized=poll.is_finalized(),
        total_votes=poll.total_votes,
        answers=[
            PollAnswerInfo(
                id=a.id,
                text=a.text,
                emoji=str(a.emoji) if a.emoji else None,
                votes=a.vote_count if poll.total_votes is not None else None,
            )
            for a in poll.answers
        ],
    )


def message_info(
    message: discord.Message, *, allow_dm: bool = False, include_reply: bool = True
) -> MessageInfo:
    if message.guild is None and not allow_dm:
        raise ValueError("Guild message expected")
    reference = message.reference
    resolved_reply = getattr(reference, "resolved", None) if reference else None
    reply = (
        message_info(resolved_reply, allow_dm=allow_dm, include_reply=False)
        if include_reply and isinstance(resolved_reply, discord.Message)
        else None
    )
    return MessageInfo(
        id=str(message.id),
        guild_id=str(message.guild.id) if message.guild else None,
        channel_id=str(message.channel.id),
        author=user_info(message.author),
        created_at=message.created_at,
        edited_at=message.edited_at,
        content=message.content,
        attachments=[
            AttachmentInfo(
                id=str(a.id),
                filename=a.filename,
                url=a.url,
                proxy_url=a.proxy_url,
                size=a.size,
                content_type=a.content_type,
                description=a.description,
            )
            for a in message.attachments
        ],
        reference=ReplyReference(
            message_id=optional_id(reference.message_id),
            channel_id=str(reference.channel_id),
            guild_id=optional_id(reference.guild_id),
        )
        if reference
        else None,
        url=message.jump_url,
        poll=poll_info(message.poll) if message.poll is not None else None,
        reply_to=reply,
        embeds=[EmbedInfo.model_validate(embed.to_dict()) for embed in message.embeds],
        stickers=[
            StickerInfo(id=str(s.id), name=s.name, format=s.format.name, url=s.url)
            for s in message.stickers
        ],
        components=[ComponentInfo.model_validate(c.to_dict()) for c in message.components],
        type=message.type.name,
        pinned=message.pinned,
        is_system=message.is_system(),
        system_content=message.system_content if message.is_system() else None,
        mentions=[user_info(user) for user in message.mentions],
        role_mentions=[MentionInfo(id=str(r.id), name=r.name) for r in message.role_mentions],
        channel_mentions=[MentionInfo(id=str(c.id), name=c.name) for c in message.channel_mentions],
        mention_everyone=message.mention_everyone,
    )
