import discord

from ..models.management import MutationResult, Page, RoleInfo, RoleUpdate
from . import resources
from .access import DiscordAccess


async def list_roles(
    access: DiscordAccess,
    guild_id: str | None,
    limit: int,
    after: str | None,
) -> Page[RoleInfo]:
    guild = await access.guild(guild_id)
    roles = guild.roles or await guild.fetch_roles()
    roles = sorted([r for r in roles if after is None or r.id > int(after)], key=lambda r: r.id)
    return Page[RoleInfo](
        items=[resources.role_info(r) for r in roles[:limit]],
        next_cursor=str(roles[limit - 1].id) if len(roles) > limit else None,
    )


async def create_role(
    access: DiscordAccess,
    name: str,
    guild_id: str | None,
    settings: RoleUpdate | None,
    reason: str | None,
) -> RoleInfo:
    guild = await access.guild(guild_id)
    data = settings.model_dump(exclude_unset=True, exclude_none=True) if settings else {}
    # Position changes use Role.edit after creation; reject rather than silently ignoring them.
    if "position" in data:
        raise resources.invalid("Set position using edit_role after creation.")
    if "permissions" in data:
        data["permissions"] = discord.Permissions(int(data["permissions"]))
    if "colour" in data:
        data["colour"] = discord.Colour(data["colour"])
    data["name"] = name
    return resources.role_info(await guild.create_role(**data, reason=reason))


async def edit_role(
    access: DiscordAccess,
    role_id: str,
    guild_id: str | None,
    settings: RoleUpdate,
    reason: str | None,
) -> RoleInfo:
    guild = await access.guild(guild_id)
    role = await resources.role(access, guild, role_id)
    data = settings.model_dump(exclude_unset=True, exclude_none=True)
    resources.require_changes(data)
    if "permissions" in data:
        data["permissions"] = discord.Permissions(int(data["permissions"]))
    if "colour" in data:
        data["colour"] = discord.Colour(data["colour"])
    return resources.role_info(await role.edit(**data, reason=reason) or role)


async def delete_role(
    access: DiscordAccess,
    role_id: str,
    guild_id: str | None,
    reason: str | None,
) -> MutationResult:
    guild = await access.guild(guild_id)
    role = await resources.role(access, guild, role_id)
    await role.delete(reason=reason)
    return MutationResult(resource_id=role_id, guild_id=str(guild.id), action="deleted")


async def member_role(
    access: DiscordAccess,
    member_id: str,
    role_id: str,
    guild_id: str | None,
    reason: str | None,
    remove: bool = False,
) -> MutationResult:
    guild = await access.guild(guild_id)
    role = await resources.role(access, guild, role_id)
    member = await access.member(guild, int(member_id))
    if remove:
        await member.remove_roles(role, reason=reason, atomic=True)
    else:
        await member.add_roles(role, reason=reason, atomic=True)
    return MutationResult(
        resource_id=member_id,
        guild_id=str(guild.id),
        action=f"role_{role_id}_{'removed' if remove else 'assigned'}",
    )
