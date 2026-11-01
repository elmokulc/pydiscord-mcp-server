from ..models import ChannelInfo, ChannelPage
from .access import DiscordAccess
from .serialization import channel_info


async def list_channels(
    access: DiscordAccess, guild_id: str | None, limit: int, after: str | None
) -> ChannelPage:
    guild = await access.guild(guild_id)
    channels = guild.channels or list(await guild.fetch_channels())
    selected = sorted(
        [c for c in channels if after is None or c.id > int(after)], key=lambda c: c.id
    )
    page = selected[:limit]
    return ChannelPage(
        items=[channel_info(c) for c in page],
        next_cursor=str(page[-1].id) if len(selected) > limit else None,
    )


async def get_channel_info(access: DiscordAccess, channel_id: str) -> ChannelInfo:
    return channel_info(await access.channel(channel_id))
