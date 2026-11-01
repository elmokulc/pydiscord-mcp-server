from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from . import __version__
from .config import Settings
from .discord_client import DiscordRuntime
from .services.access import DiscordAccess
from .tools import register_tools


@dataclass
class Application:
    app: Starlette
    mcp: MCPServer
    runtime: DiscordRuntime


def create_application(settings: Settings, runtime: DiscordRuntime | None = None) -> Application:
    runtime = runtime if runtime is not None else DiscordRuntime(settings)
    mcp = MCPServer(
        "pydiscord-mcp-server",
        version=__version__,
        instructions="Guild bot operations. Writes affect Discord. Mentions disabled by default.",
        log_level=settings.log_level,
    )
    register_tools(mcp, DiscordAccess(runtime))
    http_app = mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=settings.mcp_allowed_hosts,
            allowed_origins=settings.mcp_allowed_origins,
        ),
    )

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        try:
            await runtime.start()
            async with mcp.session_manager.run():
                yield
        finally:
            await runtime.close()

    async def live(request: Request) -> JSONResponse:
        return JSONResponse({"status": "live"})

    async def ready(request: Request) -> JSONResponse:
        healthy = runtime.ready
        return JSONResponse(
            {"status": "ready" if healthy else "not_ready"}, status_code=200 if healthy else 503
        )

    app = Starlette(
        routes=[Route("/health/live", live), Route("/health/ready", ready), Mount("/", http_app)],
        lifespan=lifespan,
    )
    return Application(app=app, mcp=mcp, runtime=runtime)
