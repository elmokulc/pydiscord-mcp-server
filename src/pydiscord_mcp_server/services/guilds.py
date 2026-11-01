from ..models import GuildInfo, GuildPage
from .access import DiscordAccess
from .serialization import guild_info


async def list_guilds(access: DiscordAccess, limit: int, after: str | None) -> GuildPage:
    guilds = sorted(access.client.guilds, key=lambda g: g.id)
    allowed = access.settings.discord_allowed_guild_ids
    guilds = [
        g
        for g in guilds
        if (allowed is None or str(g.id) in allowed) and (after is None or g.id > int(after))
    ]
    page = guilds[:limit]
    return GuildPage(
        items=[guild_info(g) for g in page],
        next_cursor=str(page[-1].id) if len(guilds) > limit else None,
    )


async def get_guild_info(access: DiscordAccess, guild_id: str | None) -> GuildInfo:
    return guild_info(await access.guild(guild_id))
