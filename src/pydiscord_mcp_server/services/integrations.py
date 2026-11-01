import base64
import binascii
from typing import Any

import discord

from ..errors import DiscordToolError
from ..models import MessageInfo
from ..models.management import EmojiInfo, InviteInfo, MutationResult, Page, WebhookInfo
from . import resources
from .access import DiscordAccess
from .serialization import message_info


async def webhook_channel(
    access: DiscordAccess, channel_id: str
) -> discord.TextChannel | discord.ForumChannel | discord.VoiceChannel | discord.StageChannel:
    channel = await access.channel(channel_id)
    if not isinstance(
        channel,
        (discord.TextChannel, discord.ForumChannel, discord.VoiceChannel, discord.StageChannel),
    ):
        raise resources.invalid("Channel does not support webhooks.")
    return channel


async def create_webhook(
    access: DiscordAccess, channel_id: str, name: str, reason: str | None
) -> WebhookInfo:
    channel = await webhook_channel(access, channel_id)
    return resources.webhook_info(await channel.create_webhook(name=name, reason=reason))


async def list_webhooks(
    access: DiscordAccess, channel_id: str, limit: int, after: str | None
) -> Page[WebhookInfo]:
    channel = await webhook_channel(access, channel_id)
    hooks = sorted(
        [h for h in await channel.webhooks() if after is None or h.id > int(after)],
        key=lambda h: h.id,
    )
    return Page[WebhookInfo](
        items=[resources.webhook_info(h) for h in hooks[:limit]],
        next_cursor=str(hooks[limit - 1].id) if len(hooks) > limit else None,
    )


async def delete_webhook(
    access: DiscordAccess,
    webhook_id: str,
    reason: str | None,
) -> MutationResult:
    hook = await resources.webhook(access, webhook_id)
    await hook.delete(reason=reason)
    return MutationResult(resource_id=webhook_id, guild_id=str(hook.guild_id), action="deleted")


async def send_webhook_message(
    access: DiscordAccess,
    webhook_id: str,
    content: str,
    allow_mentions: bool,
    thread_id: str | None,
) -> MessageInfo:
    hook = await resources.webhook(access, webhook_id)
    if hook.token is None:
        raise DiscordToolError("ACCESS_DENIED", "Bot cannot obtain this webhook's send capability.")
    thread = discord.utils.MISSING
    if thread_id:
        resolved = await access.channel(thread_id)
        if not isinstance(resolved, discord.Thread) or resolved.parent_id != hook.channel_id:
            raise resources.invalid("Thread must belong to the webhook channel.")
        thread = resolved
    return message_info(
        await hook.send(
            content,
            wait=True,
            thread=thread,
            allowed_mentions=discord.AllowedMentions.all()
            if allow_mentions
            else discord.AllowedMentions.none(),
        )
    )


async def create_invite(
    access: DiscordAccess,
    channel_id: str,
    max_age: int,
    max_uses: int,
    temporary: bool,
    unique: bool,
    reason: str | None,
) -> InviteInfo:
    channel = await access.channel(channel_id)
    if isinstance(channel, discord.Thread):
        raise resources.invalid("Create an invite on the parent channel, not a thread.")
    invite = await channel.create_invite(
        max_age=max_age, max_uses=max_uses, temporary=temporary, unique=unique, reason=reason
    )
    return resources.invite_info(invite)


async def list_invites(
    access: DiscordAccess,
    guild_id: str | None,
    limit: int,
    after: str | None,
) -> Page[InviteInfo]:
    guild = await access.guild(guild_id)
    invites = sorted(
        [i for i in await guild.invites() if after is None or i.code > after], key=lambda i: i.code
    )
    return Page[InviteInfo](
        items=[resources.invite_info(i) for i in invites[:limit]],
        next_cursor=invites[limit - 1].code if len(invites) > limit else None,
    )


async def resolve_invite(access: DiscordAccess, code: str) -> discord.Invite:
    invite = await access.client.fetch_invite(code, with_counts=True, with_expiration=True)
    if invite.guild is None:
        raise DiscordToolError("ACCESS_DENIED", "Only guild invites are supported.")
    access.check_guild(invite.guild.id)
    return invite


async def delete_invite(
    access: DiscordAccess,
    code: str,
    reason: str | None,
) -> MutationResult:
    invite = await resolve_invite(access, code)
    await invite.delete(reason=reason)
    return MutationResult(
        resource_id=invite.code,
        guild_id=str(invite.guild.id) if invite.guild else None,
        action="deleted",
    )


async def list_emojis(
    access: DiscordAccess,
    guild_id: str | None,
    limit: int,
    after: str | None,
) -> Page[EmojiInfo]:
    guild = await access.guild(guild_id)
    emojis = guild.emojis or await guild.fetch_emojis()
    selected = sorted([e for e in emojis if after is None or e.id > int(after)], key=lambda e: e.id)
    return Page[EmojiInfo](
        items=[resources.emoji_info(e) for e in selected[:limit]],
        next_cursor=str(selected[limit - 1].id) if len(selected) > limit else None,
    )


def decode_emoji_image(data: str) -> bytes:
    if data.startswith("data:image/"):
        data = data.partition(",")[2]
    try:
        image = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error):
        raise resources.invalid("Image must be valid base64.") from None
    if not 1 <= len(image) <= 256 * 1024:
        raise resources.invalid("Emoji image must be at most 256 KiB.")
    if not (
        image.startswith((b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"\xff\xd8\xff"))
        or (image.startswith(b"RIFF") and image[8:12] == b"WEBP")
    ):
        raise resources.invalid("Image must be PNG, JPEG, GIF or WebP.")
    return image


async def create_emoji(
    access: DiscordAccess,
    name: str,
    image_base64: str,
    guild_id: str | None,
    role_ids: list[str] | None,
    reason: str | None,
) -> EmojiInfo:
    image = decode_emoji_image(image_base64)
    guild = await access.guild(guild_id)
    roles = [await resources.role(access, guild, r) for r in role_ids or []]
    emoji = await guild.create_custom_emoji(name=name, image=image, roles=roles, reason=reason)
    return resources.emoji_info(emoji)


async def edit_emoji(
    access: DiscordAccess,
    emoji_id: str,
    guild_id: str | None,
    name: str | None,
    role_ids: list[str] | None,
    reason: str | None,
) -> EmojiInfo:
    guild = await access.guild(guild_id)
    emoji = await resources.emoji(access, guild, emoji_id)
    data: dict[str, Any] = {}
    if name is not None:
        data["name"] = name
    if role_ids is not None:
        data["roles"] = [await resources.role(access, guild, r) for r in role_ids]
    resources.require_changes(data)
    return resources.emoji_info(await emoji.edit(**data, reason=reason))


async def delete_emoji(
    access: DiscordAccess,
    emoji_id: str,
    guild_id: str | None,
    reason: str | None,
) -> MutationResult:
    guild = await access.guild(guild_id)
    emoji = await resources.emoji(access, guild, emoji_id)
    await emoji.delete(reason=reason)
    return MutationResult(resource_id=emoji_id, guild_id=str(guild.id), action="deleted")
