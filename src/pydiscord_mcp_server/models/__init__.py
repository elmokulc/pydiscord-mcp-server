"""Validated tool parameters and JSON result contracts."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field


def snowflake_range(value: str) -> str:
    if int(value) > 2**64 - 1:
        raise ValueError("Discord ID must fit in an unsigned 64-bit integer")
    return value


Snowflake = Annotated[
    str,
    Field(strict=True, pattern=r"^[1-9][0-9]{0,19}$", description="Discord ID as a decimal string"),
    AfterValidator(snowflake_range),
]
PageLimit = Annotated[int, Field(strict=True, ge=1, le=100, description="Page size, from 1 to 100")]
MessageContent = Annotated[str, Field(min_length=1, max_length=2000, description="Message text")]
AllowMentions = Annotated[
    bool,
    Field(strict=True, description="Explicitly allow user, role, everyone and reply mentions"),
]
AllowOtherAuthor = Annotated[
    bool,
    Field(
        strict=True, description="Allow deleting another author's message; requires Manage Messages"
    ),
]
ThreadMode = Literal["active", "archived_public", "archived_private", "archived_joined_private"]
Cursor = Annotated[str, Field(min_length=1, max_length=1024, description="Opaque next_cursor")]
MemberQuery = Annotated[
    str,
    Field(
        min_length=1, max_length=100, description="Username/nickname prefix (not a global search)"
    ),
]
Emoji = Annotated[
    str, Field(min_length=1, max_length=100, description="Unicode emoji or <:name:id> custom emoji")
]


class UserInfo(BaseModel):
    id: str
    name: str
    display_name: str
    bot: bool
    global_name: str | None = None
    discriminator: str = "0"


class GuildInfo(BaseModel):
    id: str
    name: str
    owner_id: str | None
    member_count: int | None
    description: str | None


class GuildPage(BaseModel):
    items: list[GuildInfo]
    next_cursor: str | None = None


class ChannelInfo(BaseModel):
    id: str
    guild_id: str
    name: str
    type: str
    parent_id: str | None = None
    topic: str | None = None
    archived: bool | None = None
    locked: bool | None = None
    archive_timestamp: datetime | None = None
    position: int | None = None
    nsfw: bool | None = None
    slowmode_delay: int | None = None
    bitrate: int | None = None
    user_limit: int | None = None
    rtc_region: str | None = None
    owner_id: str | None = None
    message_count: int | None = None
    member_count: int | None = None
    url: str


class ChannelPage(BaseModel):
    items: list[ChannelInfo]
    next_cursor: str | None = None


class AttachmentInfo(BaseModel):
    id: str
    filename: str
    url: str
    proxy_url: str
    size: int
    content_type: str | None
    description: str | None


class ReplyReference(BaseModel):
    message_id: str | None
    channel_id: str | None
    guild_id: str | None


class PollAnswerInfo(BaseModel):
    id: int
    text: str
    emoji: str | None
    votes: int | None


class PollInfo(BaseModel):
    question: str
    answers: list[PollAnswerInfo]
    allow_multiselect: bool
    expires_at: datetime | None
    finalized: bool
    total_votes: int | None


class MessageInfo(BaseModel):
    id: str
    guild_id: str | None
    channel_id: str
    author: UserInfo
    created_at: datetime
    edited_at: datetime | None
    content: str
    attachments: list[AttachmentInfo]
    reference: ReplyReference | None
    url: str
    poll: PollInfo | None = None
    reply_to: "MessageInfo | None" = None


class MessagePage(BaseModel):
    items: list[MessageInfo]
    next_cursor: str | None = None
    order: Literal["newest_first", "oldest_first"] = "newest_first"
    cursor_parameter: Literal["before", "after"] | None = "before"


class ThreadPage(BaseModel):
    items: list[ChannelInfo]
    next_cursor: str | None = None
    mode: ThreadMode


class MemberInfo(UserInfo):
    guild_id: str
    nickname: str | None
    joined_at: datetime | None
    role_ids: list[str]


class MemberSearchResult(BaseModel):
    items: list[MemberInfo]
    scope: str = "Available guild member cache plus bounded Gateway prefix query; no pagination"
    exhaustive: bool = False


class ActionResult(BaseModel):
    channel_id: str
    message_id: str
    action: Literal["deleted", "reaction_added", "reaction_removed"]


def optional_id(value: int | None) -> str | None:
    return str(value) if value is not None else None
