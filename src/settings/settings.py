"""Application settings loaded from environment variables."""

import logging
from pathlib import Path

from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JSON_PATH = BASE_DIR / "data.json"
LOCALES_PATH = BASE_DIR / "locales"


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

    owners: list[int] = Field(
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


# noinspection PyArgumentList
settings = Settings()
