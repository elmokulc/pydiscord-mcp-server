from ..errors import DiscordToolError
from ..models import MemberInfo, MemberSearchResult
from ..models.management import UserLookupInfo
from .access import DiscordAccess
from .serialization import member_info


async def get_member(access: DiscordAccess, member_id: str, guild_id: str | None) -> MemberInfo:
    guild = await access.guild(guild_id)
    return member_info(await access.member(guild, int(member_id)))


async def search_members(
    access: DiscordAccess,
    query: str,
    guild_id: str | None,
    limit: int,
    *,
    resolve_id: bool = True,
) -> MemberSearchResult:
    if not query.strip():
        raise DiscordToolError("INVALID_PARAMETER", "query cannot be blank.")
    if resolve_id and query.isdecimal():
        if not 0 < int(query) < 2**64:
            raise DiscordToolError("INVALID_PARAMETER", "Member ID is outside Discord's ID range.")
        member = await get_member(access, query, guild_id)
        return MemberSearchResult(items=[member], scope="One member by ID, cache then REST")
    if not access.settings.discord_intent_members:
        raise DiscordToolError(
            "INVALID_PARAMETER",
            "search_members requires DISCORD_INTENT_MEMBERS=true and portal intent.",
        )
    guild = await access.guild(guild_id)
    results = await guild.query_members(query=query, limit=max(5, limit), cache=False)
    available = {m.id: m for m in guild.members}
    available.update({m.id: m for m in results})
    needle = query.casefold()
    matches = [
        m
        for m in available.values()
        if any(
            needle in text.casefold()
            for text in (m.name, m.display_name, m.nick or "", m.global_name or "")
        )
    ]
    return MemberSearchResult(items=[member_info(m) for m in matches[:limit]])


async def get_user_id_by_name(
    access: DiscordAccess,
    username: str,
    guild_id: str | None,
) -> UserLookupInfo:
    result = await search_members(access, username.split("#")[0], guild_id, 100, resolve_id=False)
    needle = username.casefold()
    matches = [
        m
        for m in result.items
        if needle in (m.name.casefold(), f"{m.name}#{m.discriminator}".casefold())
    ]
    if len(matches) != 1:
        raise DiscordToolError(
            "INVALID_PARAMETER",
            "Exact username is missing or ambiguous in this bounded search; use user ID.",
        )
    user = matches[0]
    return UserLookupInfo(id=user.id, username=user.name, mention=f"<@{user.id}>")
