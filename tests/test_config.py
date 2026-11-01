import pytest
from pydantic import TypeAdapter, ValidationError

from pydiscord_mcp_server.config import Settings
from pydiscord_mcp_server.models import PageLimit, Snowflake


@pytest.mark.parametrize("value", [0, 101, -1, True, "10"])
def test_invalid_page_limit(value):
    with pytest.raises(ValidationError):
        TypeAdapter(PageLimit).validate_python(value)


@pytest.mark.parametrize("value", ["0", "-1", "1.5", "01", "18446744073709551616", 123])
def test_invalid_snowflake(value):
    with pytest.raises(ValidationError):
        TypeAdapter(Snowflake).validate_python(value)


def test_snowflake_preserves_precision():
    ident = "1234567890123456789"
    assert TypeAdapter(Snowflake).validate_python(ident) == ident


def test_token_required_and_secret():
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
    with pytest.raises(ValidationError):
        Settings(discord_token=" ", _env_file=None)
    settings = Settings(discord_token="do-not-print-me", _env_file=None)
    assert "do-not-print-me" not in repr(settings)
    assert "do-not-print-me" not in settings.model_dump_json()


def test_environment_json_and_default(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "fake")
    monkeypatch.setenv("DISCORD_GUILD_ID", "")
    monkeypatch.setenv("DISCORD_ALLOWED_GUILD_IDS", '["100","101"]')
    settings = Settings(_env_file=None)
    assert settings.discord_guild_id is None
    assert settings.discord_allowed_guild_ids == ["100", "101"]
