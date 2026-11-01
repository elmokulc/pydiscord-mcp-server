"""Discord-shaped async doubles shared by catalogue and policy tests."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import discord
from conftest import async_items, make_channel, make_guild, make_message


def build_scene(access):
    access.settings.discord_guild_id = "100"
    access.settings.discord_intent_members = True
    access.settings.discord_enable_dms = True
    guild = make_guild()
    text = make_channel(200, guild)
    thread = make_channel(201, guild, discord.Thread)
    category = make_channel(202, guild, discord.CategoryChannel)
    voice = make_channel(203, guild, discord.VoiceChannel)
    stage = make_channel(204, guild, discord.StageChannel)
    forum = make_channel(205, guild, discord.ForumChannel)
    post = make_channel(206, guild, discord.Thread)
    post.parent_id = 205
    tag = discord.ForumTag(name="tag")
    tag.id = 550
    forum.available_tags = [tag]
    forum.default_thread_slowmode_delay = 0
    forum.default_sort_order = discord.ForumOrderType.latest_activity
    forum.default_layout = discord.ForumLayoutType.list_view
    channels = {c.id: c for c in [text, thread, category, voice, stage, forum, post]}
    guild.channels = [text, category, voice, stage, forum]
    category.channels = [text, voice, stage, forum]
    guild.fetch_channels.return_value = guild.channels
    access.client.guilds = [guild]
    access.client.get_guild.side_effect = lambda ident: guild if ident == 100 else None
    access.client.get_channel.side_effect = channels.get
    access.client.fetch_channel.side_effect = lambda ident: channels[ident]

    role = MagicMock(spec=discord.Role)
    role.id = 500
    role.guild = guild
    role.name = "Reader"
    role.permissions = discord.Permissions(view_channel=True)
    role.colour = discord.Colour(0x123456)
    role.position = 1
    role.hoist = False
    role.mentionable = False
    role.managed = False
    role.edit.return_value = role
    guild.roles = [role]
    guild.get_role.side_effect = lambda ident: role if ident == 500 else None
    guild.fetch_roles.return_value = [role]
    guild.create_role.return_value = role

    member = MagicMock(spec=discord.Member)
    member.id = 901
    member.guild = guild
    member.name = "alice"
    member.display_name = "Alice"
    member.global_name = "Alice Global"
    member.discriminator = "0"
    member.bot = False
    member.nick = None
    member.joined_at = datetime(2026, 1, 1, tzinfo=UTC)
    member.roles = [role]
    member.edit.return_value = member
    guild.members = [member]
    guild.get_member.side_effect = lambda ident: member if ident in (900, 901) else None
    guild.fetch_member.return_value = member
    guild.query_members.return_value = [member]
    guild.bans.side_effect = lambda **kwargs: async_items(
        [SimpleNamespace(user=member, reason="test")]
    )

    poll = MagicMock(spec=discord.Poll)
    poll.question = "On déploie ?"
    poll.multiple = False
    poll.expires_at = datetime.now(UTC) + timedelta(hours=24)
    poll.total_votes = 2
    poll.is_finalized.return_value = False
    answer = MagicMock(spec=discord.PollAnswer)
    answer.id = 1
    answer.text = "Oui"
    answer.emoji = None
    answer.vote_count = 2
    answer.voters.side_effect = lambda **kwargs: async_items([member])
    poll.answers = [answer]
    poll.get_answer.side_effect = lambda ident: answer if ident == 1 else None
    poll_message = make_message(310, text)
    poll_message.poll = poll
    poll_message.end_poll.return_value = poll_message

    messages = [make_message(i, text) for i in [313, 312, 311]]
    for message in messages:
        message.content = "hello world"
    messages[-1].reference = SimpleNamespace(
        message_id=300, channel_id=200, guild_id=100, resolved=None
    )
    for channel in channels.values():
        sent = make_message(320, channel)
        sent.edit.return_value = sent
        if isinstance(channel, discord.abc.Messageable):
            channel.send.return_value = sent
            channel.fetch_message.side_effect = lambda ident, c=channel: (
                poll_message if ident == 310 else message_for(c, ident)
            )
            channel.history.side_effect = lambda **kwargs: async_items(messages[: kwargs["limit"]])
        channel.edit.return_value = channel
        channel.permissions_for.return_value = discord.Permissions.all()
        if not isinstance(channel, discord.Thread):
            channel.overwrites = {role: discord.PermissionOverwrite(view_channel=True)}
            channel.overwrites_for.side_effect = lambda target: discord.PermissionOverwrite(
                view_channel=True
            )
    guild.active_threads.return_value = [thread, post]
    text.archived_threads.side_effect = lambda **kwargs: async_items([thread])
    forum.archived_threads.side_effect = lambda **kwargs: async_items([post])
    forum.create_thread.return_value = SimpleNamespace(thread=post, message=make_message(321, post))
    guild.create_text_channel.return_value = text
    guild.create_category.return_value = category
    guild.create_voice_channel.return_value = voice
    guild.create_stage_channel.return_value = stage
    guild.create_forum.return_value = forum

    hook = MagicMock(spec=discord.Webhook)
    hook.id = 800
    hook.guild_id = 100
    hook.channel_id = 200
    hook.name = "Test hook"
    hook.type = discord.WebhookType.incoming
    hook.token = "secret-webhook-token-must-not-leak"
    hook.send.return_value = make_message(322, text)
    access.client.fetch_webhook.return_value = hook
    text.create_webhook.return_value = hook
    text.webhooks.return_value = [hook]

    invite = MagicMock(spec=discord.Invite)
    invite.code = "testInvite"
    invite.url = "https://discord.gg/testInvite"
    invite.guild = guild
    invite.channel = text
    invite.uses = 0
    invite.max_uses = 5
    invite.max_age = 3600
    invite.temporary = False
    invite.expires_at = datetime.now(UTC) + timedelta(hours=1)
    text.create_invite.return_value = invite
    guild.invites.return_value = [invite]
    access.client.fetch_invite.return_value = invite

    emoji = MagicMock(spec=discord.Emoji)
    emoji.id = 600
    emoji.guild_id = 100
    emoji.name = "hello"
    emoji.animated = False
    emoji.available = True
    emoji.roles = []
    emoji.url = "https://cdn.discordapp.com/emojis/600.png"
    emoji.edit.return_value = emoji
    guild.emojis = [emoji]
    guild.get_emoji.side_effect = lambda ident: emoji if ident == 600 else None
    guild.fetch_emoji.return_value = emoji
    guild.create_custom_emoji.return_value = emoji

    event = MagicMock(spec=discord.ScheduledEvent)
    event.id = 700
    event.guild_id = 100
    event.name = "Release"
    event.description = "Test event"
    event.entity_type = discord.EntityType.external
    event.status = discord.EventStatus.scheduled
    event.channel_id = None
    event.location = "Paris"
    event.start_time = datetime.now(UTC) + timedelta(days=3)
    event.end_time = datetime.now(UTC) + timedelta(days=4)
    event.user_count = 1
    event.url = "https://discord.com/events/100/700"
    event.edit.return_value = event
    event.users.side_effect = lambda **kwargs: async_items([member])
    guild.get_scheduled_event.side_effect = lambda ident: event if ident == 700 else None
    guild.fetch_scheduled_event.return_value = event
    guild.create_scheduled_event.return_value = event
    guild.fetch_scheduled_events.return_value = [event]

    dm = MagicMock(spec=discord.DMChannel)
    dm.id = 400
    dm_message = make_message(330, text)
    dm_message.channel = dm
    dm_message.guild = None
    dm_message.edit.return_value = dm_message
    dm.send.return_value = dm_message
    dm.fetch_message.return_value = dm_message
    dm.history.side_effect = lambda **kwargs: async_items([dm_message])
    member.dm_channel = dm
    member.create_dm.return_value = dm

    return SimpleNamespace(
        access=access,
        guild=guild,
        channels=channels,
        text=text,
        thread=thread,
        category=category,
        voice=voice,
        stage=stage,
        forum=forum,
        post=post,
        role=role,
        member=member,
        poll=poll,
        poll_message=poll_message,
        answer=answer,
        hook=hook,
        invite=invite,
        emoji=emoji,
        event=event,
        dm=dm,
        dm_message=dm_message,
    )


def message_for(channel, ident):
    result = make_message(ident, channel)
    result.edit.return_value = result
    return result
