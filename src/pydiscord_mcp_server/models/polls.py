from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from . import Emoji

PollQuestion = Annotated[
    str, Field(min_length=1, max_length=300, description="Native poll question")
]
PollAnswerText = Annotated[str, Field(min_length=1, max_length=55)]
PollDuration = Annotated[
    int, Field(strict=True, ge=1, le=768, description="Duration in hours, 1–768")
]


class PollOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: PollAnswerText
    emoji: Emoji | None = None

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Poll option cannot be blank")
        return value


PollOptions = Annotated[list[PollOption], Field(min_length=2, max_length=10)]
Multiselect = Annotated[
    StrictBool, Field(description="Allow each person to select multiple answers")
]
