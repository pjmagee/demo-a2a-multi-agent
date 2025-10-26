"""Configuration for the webapp backend service."""

from functools import lru_cache
from typing import cast

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment configuration for the backend."""

    agent_addresses: list[str] = Field(default_factory=list)
    allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    copilotkit_remote_token: str | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_prefix="WEBAPP_",
        env_file=".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("agent_addresses", mode="before")
    @classmethod
    def _parse_addresses(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            typed_value = cast("list[object]", value)
            cleaned: list[str] = []
            for raw_item in typed_value:
                candidate = str(raw_item).strip()
                if candidate:
                    cleaned.append(candidate)
            return cleaned
        return []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
