"""Structured resource contracts and bounded inputs for administration tools."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
)

from . import ChannelInfo, MessageInfo, Snowflake, UserInfo, snowflake_range

Name = Annotated[str, Field(min_length=1, max_length=100, description="Resource name")]
Reason = Annotated[str, Field(max_length=512, description="Discord audit log reason")]
Position = Annotated[int, Field(strict=True, ge=0)]
Slowmode = Annotated[int, Field(strict=True, ge=0, le=21600)]
ScanLimit = Annotated[int, Field(strict=True, ge=1, le=1000)]
PermissionBits = Annotated[
    str,
    Field(pattern=r"^[0-9]{1,20}$", description="Permission bitset in decimal"),
    AfterValidator(snowflake_range),
]


class Page[T](BaseModel):
    items: list[T]
    next_cursor: str | None = None


class MutationResult(BaseModel):
    resource_id: str
    guild_id: str | None = None
    action: str


class UpdateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TextChannelUpdate(UpdateModel):
    name: Name | None = None
    topic: Annotated[str, Field(max_length=1024)] | None = None
    nsfw: StrictBool | None = None
    slowmode_delay: Slowmode | None = None
    category_id: Snowflake | None = Field(
        default=None, description="Explicit null removes category"
    )
    position: Position | None = None


class CategoryUpdate(UpdateModel):
    name: Name | None = None
    position: Position | None = None


class VoiceChannelUpdate(UpdateModel):
    name: Name | None = None
    bitrate: Annotated[int, Field(strict=True, ge=8000, le=384000)] | None = None
    user_limit: Annotated[int, Field(strict=True, ge=0, le=99)] | None = None
    rtc_region: Annotated[str, Field(max_length=100)] | None = Field(
        default=None, description="Explicit null selects automatic region"
    )
    category_id: Snowflake | None = None
    position: Position | None = None


class ForumUpdate(UpdateModel):
    name: Name | None = None
    topic: Annotated[str, Field(max_length=4096)] | None = None
    nsfw: StrictBool | None = None
    slowmode_delay: Slowmode | None = None
    default_thread_slowmode_delay: Slowmode | None = None
    category_id: Snowflake | None = None
    position: Position | None = None
    default_sort_order: Literal["latest_activity", "creation_date"] | None = None
    default_layout: Literal["not_set", "list_view", "gallery_view"] | None = None


class ForumPostUpdate(UpdateModel):
    locked: StrictBool | None = None
    archived: StrictBool | None = None
    pinned: StrictBool | None = None
    tag_ids: Annotated[list[Snowflake], Field(max_length=5)] | None = None


class RoleUpdate(UpdateModel):
    name: Name | None = None
    permissions: PermissionBits | None = None
    colour: Annotated[int, Field(strict=True, ge=0, le=0xFFFFFF)] | None = None
    hoist: StrictBool | None = None
    mentionable: StrictBool | None = None
    position: Position | None = None


class RoleInfo(BaseModel):
    id: str
    guild_id: str
    name: str
    permissions: str
    colour: int
    position: int
    hoist: bool
    mentionable: bool
    managed: bool


class BanInfo(BaseModel):
    user: UserInfo
    reason: str | None


class WebhookInfo(BaseModel):
    id: str
    guild_id: str
    channel_id: str
    name: str | None
    type: str
    # Webhook tokens and token-bearing URLs are intentionally excluded.


class InviteInfo(BaseModel):
    code: str
    url: str
    guild_id: str
    channel_id: str | None
    uses: int | None
    max_uses: int | None
    max_age: int | None
    temporary: bool | None
    expires_at: datetime | None


class EmojiInfo(BaseModel):
    id: str
    guild_id: str
    name: str
    animated: bool
    available: bool
    role_ids: list[str]
    url: str


class OverwriteInfo(BaseModel):
    target_id: str
    target_type: Literal["role", "member"]
    allow: str
    deny: str
    permissions: dict[str, bool | None]


PermissionChanges = Annotated[
    dict[str, StrictBool | None],
    Field(
        min_length=1, max_length=64, description="Permission name to true, false or null (inherit)"
    ),
]


class OverwriteChanges(UpdateModel):
    permissions: PermissionChanges

    @field_validator("permissions")
    @classmethod
    def known_permissions(cls, value: dict[str, bool | None]) -> dict[str, bool | None]:
        import discord

        unknown = set(value) - discord.Permissions.VALID_FLAGS.keys()
        if unknown:
            raise ValueError("Unknown Discord permission names")
        return value


class ForumTagInfo(BaseModel):
    id: str
    name: str
    moderated: bool
    emoji: str | None


class ForumInfo(ChannelInfo):
    tags: list[ForumTagInfo]
    nsfw: bool
    slowmode_delay: int
    default_thread_slowmode_delay: int
    default_sort_order: str | None
    default_layout: str


class EventInfo(BaseModel):
    id: str
    guild_id: str
    name: str
    description: str | None
    entity_type: str
    status: str
    channel_id: str | None
    location: str | None
    start_time: datetime
    end_time: datetime | None
    user_count: int | None
    url: str


class EventUpdate(UpdateModel):
    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    description: Annotated[str, Field(max_length=1000)] | None = None
    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None
    location: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    status: Literal["scheduled", "active", "completed", "cancelled"] | None = None


class HistorySearchResult(BaseModel):
    items: list[MessageInfo]
    scanned: int
    scan_limit: int
    next_cursor: str | None = None
    exhausted: bool
    cursor_parameter: Literal["before", "after"] = "before"
    scope: str = "Bounded scan of this channel/thread only; no global search"


class UserLookupInfo(BaseModel):
    id: str
    username: str
    mention: str
