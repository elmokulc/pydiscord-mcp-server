import asyncio
import logging
from contextlib import suppress

import uvicorn
from pydantic import ValidationError
from pydantic_settings import SettingsError

from .config import Settings
from .server import create_application


async def serve(settings: Settings) -> int:
    application = create_application(settings)
    # HTTP debug logs may include bodies. Never enable them through LOG_LEVEL.
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.webhook").setLevel(logging.WARNING)
    logging.getLogger("mcp.server").setLevel(logging.WARNING)
    server = uvicorn.Server(
        uvicorn.Config(
            application.app,
            host=settings.mcp_host,
            port=settings.mcp_port,
            workers=1,
            log_level=settings.log_level.lower(),
            timeout_graceful_shutdown=15,
            access_log=False,
        )
    )
    serving = asyncio.create_task(server.serve())
    failure = asyncio.create_task(application.runtime.failed.wait())
    try:
        done, _ = await asyncio.wait([serving, failure], return_when=asyncio.FIRST_COMPLETED)
        if failure in done:
            logging.getLogger(__name__).critical("Fatal Discord failure; stopping HTTP server")
            server.should_exit = True
        await serving
        return 1 if application.runtime.failed.is_set() or not server.started else 0
    finally:
        failure.cancel()
        with suppress(asyncio.CancelledError):
            await failure


def main() -> None:
    try:
        settings = Settings()
    except (ValidationError, SettingsError):
        # Do not print pydantic's raw input values or environment content.
        raise SystemExit(
            "Invalid configuration. Check .env against .env.example (token required)."
        ) from None
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    raise SystemExit(asyncio.run(serve(settings)))


if __name__ == "__main__":
    main()
