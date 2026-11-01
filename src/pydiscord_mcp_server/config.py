"""Environment-only configuration; token values are never rendered in errors."""

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import Snowflake


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True
    )

    discord_token: SecretStr = Field(repr=False)
    discord_guild_id: Snowflake | None = None
    discord_allowed_guild_ids: list[Snowflake] | None = None
    discord_intent_message_content: bool = False
    discord_intent_members: bool = False
    discord_enable_dms: bool = False
    mcp_host: str = "127.0.0.1"
    mcp_port: int = Field(default=8085, ge=1, le=65535)
    mcp_allowed_hosts: list[str] = ["localhost:*", "127.0.0.1:*", "[::1]:*", "discord-mcp:8085"]
    mcp_allowed_origins: list[str] = []
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    discord_ready_timeout: float = Field(default=30, gt=0, le=300)
    discord_operation_timeout: float = Field(default=30, gt=0, le=300)
    discord_shutdown_timeout: float = Field(default=10, gt=0, le=60)

    @field_validator("discord_token")
    @classmethod
    def token_not_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("DISCORD_TOKEN is required and must not be blank")
        return value

    @field_validator("discord_guild_id", mode="before")
    @classmethod
    def empty_default_guild(cls, value: object) -> object:
        return None if value == "" else value
