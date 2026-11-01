from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from ..models import PageLimit, Snowflake
from ..models.management import HistorySearchResult, ScanLimit
from ..services import search
from ..services.access import DiscordAccess
from .common import READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def search_messages(
        channel_id: Snowflake,
        query: Annotated[str, Field(min_length=1, max_length=2000)],
        limit: PageLimit = 25,
        scan_limit: ScanLimit = 1000,
        before: Snowflake | None = None,
    ) -> HistorySearchResult:
        """Scan up to 1000 messages for body and embed text, newest first; no global search.

        Embed title, description, fields, author and footer are searched case-insensitively.
        next_cursor resumes in before. Message Content intent controls searchable content.
        """
        async with access.operation():
            return await search.search_messages(
                access, channel_id, query, limit, scan_limit, before
            )

    @mcp.tool(annotations=READ)
    async def get_message_replies(
        channel_id: Snowflake,
        message_id: Snowflake,
        limit: PageLimit = 25,
        scan_limit: ScanLimit = 1000,
        after: Snowflake | None = None,
    ) -> HistorySearchResult:
        """Find explicit replies by scanning up to 1000 later messages in this channel/thread.

        Oldest first; next_cursor resumes in after. Results are bounded, not an exhaustive index.
        """
        async with access.operation():
            return await search.get_message_replies(
                access, channel_id, message_id, limit, scan_limit, after
            )
