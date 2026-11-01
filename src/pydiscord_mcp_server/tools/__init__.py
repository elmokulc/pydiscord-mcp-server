from mcp.server import MCPServer

from ..services.access import DiscordAccess
from . import (
    channels,
    events,
    guilds,
    integrations,
    manage_channels,
    members,
    messages,
    moderation,
    permissions,
    polls,
    private_messages,
    roles,
    search,
    threads,
)


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    """Explicit domain registry; importing a module never registers tools implicitly."""
    guilds.register_tools(mcp, access)
    channels.register_tools(mcp, access)
    messages.register_tools(mcp, access)
    threads.register_tools(mcp, access)
    members.register_tools(mcp, access)
    polls.register_tools(mcp, access)
    manage_channels.register_tools(mcp, access)
    roles.register_tools(mcp, access)
    moderation.register_tools(mcp, access)
    permissions.register_tools(mcp, access)
    integrations.register_tools(mcp, access)
    events.register_tools(mcp, access)
    search.register_tools(mcp, access)
    private_messages.register_tools(mcp, access)
