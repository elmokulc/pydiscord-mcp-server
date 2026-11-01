from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from ..models import MessageInfo, PageLimit, Snowflake, UserInfo
from ..models.management import Page
from ..models.polls import Multiselect, PollDuration, PollOptions, PollQuestion
from ..services import polls
from ..services.access import DiscordAccess
from .common import EDIT, READ, WRITE


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=WRITE)
    async def create_poll(
        channel_id: Snowflake,
        question: PollQuestion,
        answers: PollOptions,
        duration_hours: PollDuration = 24,
        allow_multiselect: Multiselect = False,
    ) -> MessageInfo:
        """Create a native Discord poll (the + menu poll), with 2–10 answers and optional emojis.

        Requires Send Polls and Send Messages. Mentions are disabled. Bots cannot vote.
        """
        async with access.operation():
            return await polls.create_poll(
                access, channel_id, question, answers, duration_hours, allow_multiselect
            )

    @mcp.tool(annotations=READ)
    async def get_poll(channel_id: Snowflake, message_id: Snowflake) -> MessageInfo:
        """Fetch a native poll and current counts; only finalized counts are definitive."""
        async with access.operation():
            return await polls.get_poll(access, channel_id, message_id)

    @mcp.tool(annotations=EDIT)
    async def end_poll(channel_id: Snowflake, message_id: Snowflake) -> MessageInfo:
        """Close a native poll early; only polls created by this bot can be closed."""
        async with access.operation():
            return await polls.end_poll(access, channel_id, message_id)

    @mcp.tool(annotations=READ)
    async def get_poll_answer_voters(
        channel_id: Snowflake,
        message_id: Snowflake,
        answer_id: Annotated[int, Field(strict=True, ge=1)],
        limit: PageLimit = 25,
        after: Snowflake | None = None,
    ) -> Page[UserInfo]:
        """List voters for one poll answer, user IDs ascending; next_cursor goes in after."""
        async with access.operation():
            return await polls.get_poll_answer_voters(
                access, channel_id, message_id, answer_id, limit, after
            )
