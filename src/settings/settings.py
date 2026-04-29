"""Application settings loaded from environment variables."""

import json
import logging
from pathlib import Path
from typing import Annotated

from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JSON_PATH = BASE_DIR / "data.json"
LOCALES_PATH = BASE_DIR / "locales"
SUPPORTED_LANGUAGES = frozenset({"en", "ru"})


class Settings(BaseSettings):
    """Typed runtime configuration for the bot."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    token: SecretStr = Field(
        ...,
        description=(
            "Telegram bot API token obtained from BotFather. "
            "Used to authenticate requests to the Telegram Bot API. "
        ),
    )

    owners: Annotated[list[int], NoDecode] = Field(
        default_factory=list,
        description=(
            "List of Telegram user IDs with owner privileges. "
            "Users listed here are allowed to access restricted bot commands. "
            "Each value must be a valid Telegram numeric user ID."
        ),
    )

    group_limit: int = Field(
        default=5,
        description=(
            "Maximum number of groups allowed per chat. "
            "Defines how many groups can be created within a single chat session. "
        ),
    )

    default_language: str = Field(
        default="en",
        description=(
            "Default language used for bot messages when Telegram user language is unavailable "
            "or not supported."
        ),
    )
    log_level: str = Field(
        default="INFO",
        description="Application log level. For example: DEBUG, INFO, WARNING, ERROR.",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> str:
        """Normalize and validate logging level names from environment configuration."""

        if not isinstance(value, str):
            raise TypeError("log_level must be a string")

        normalized = value.strip().upper()
        if normalized not in logging.getLevelNamesMapping():
            raise ValueError(f"unsupported log level: {value}")
        return normalized

    @field_validator("owners", mode="before")
    @classmethod
    def parse_owners(cls, value: object) -> list[int]:
        """Accept owner IDs as JSON array, comma-separated string, or list."""

        if value is None:
            return []

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                try:
                    decoded = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError("owners JSON array is invalid") from exc
                return cls.parse_owners(decoded)
            values: object = raw.split(",")
        else:
            values = value

        if not isinstance(values, (list, tuple, set)):
            raise TypeError("owners must be a list or comma-separated string")

        owners: list[int] = []
        for item in values:
            if isinstance(item, bool):
                raise TypeError("owner IDs must be integers")
            if isinstance(item, str):
                item = item.strip()
                if not item:
                    continue
            owners.append(int(item))
        return owners

    @field_validator("group_limit")
    @classmethod
    def validate_group_limit(cls, value: int) -> int:
        """Ensure the configured per-chat group limit can be reached."""

        if value < 1:
            raise ValueError("group_limit must be greater than zero")
        return value

    @field_validator("default_language", mode="before")
    @classmethod
    def validate_default_language(cls, value: object) -> str:
        """Normalize and validate the fallback locale."""

        if not isinstance(value, str):
            raise TypeError("default_language must be a string")

        normalized = value.strip().lower()
        if normalized not in SUPPORTED_LANGUAGES:
            supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
            raise ValueError(
                f"unsupported default language: {value!r}; expected one of: {supported}"
            )
        return normalized

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: SecretStr) -> SecretStr:
        """Reject empty bot tokens early during startup."""

        if not value.get_secret_value().strip():
            raise ValueError("token must not be empty")
        return value


# noinspection PyArgumentList
settings = Settings()
