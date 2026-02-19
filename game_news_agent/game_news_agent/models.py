"""Pydantic models for Game News Agent - generated from JSON Schema contracts."""

from datetime import date, datetime
from enum import Enum, StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GameGenre(StrEnum):
    """Supported game genres."""

    ACTION = "action"
    ADVENTURE = "adventure"
    RPG = "rpg"
    STRATEGY = "strategy"
    SPORTS = "sports"
    RACING = "racing"
    SIMULATION = "simulation"
    PUZZLE = "puzzle"
    SHOOTER = "shooter"
    PLATFORMER = "platformer"
    FIGHTING = "fighting"
    HORROR = "horror"
    SURVIVAL = "survival"
    INDIE = "indie"


class GameMode(StrEnum):
    """Supported game modes."""

    ONLINE = "online"
    OFFLINE = "offline"
    SINGLE_PLAYER = "single_player"
    MULTI_PLAYER = "multi_player"


class GameReportRequest(BaseModel):
    """Request schema for generating a gaming report."""

    game_genres: list[GameGenre] = Field(
        ...,
        min_length=1,
        description="List of game genres to include in the report",
    )
    date_from: date = Field(
        ...,
        description="Start date for filtering games/articles (ISO 8601 format: YYYY-MM-DD)",
    )
    date_to: date = Field(
        ...,
        description="End date for filtering games/articles (ISO 8601 format: YYYY-MM-DD). Must be >= date_from and within 31 days of date_from.",
    )
    game_modes: list[GameMode] = Field(
        ...,
        min_length=1,
        description="Game modes to filter by",
    )

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Validate that date_to is after date_from and within 31 days."""
        if hasattr(info, "data") and "date_from" in info.data:
            date_from = info.data["date_from"]
            if v < date_from:
                raise ValueError("date_to must be >= date_from")
            if (v - date_from).days > 31:
                raise ValueError("date range must not exceed 31 days")
        return v


class AnticipatedGame(BaseModel):
    """Highly anticipated upcoming game."""

    name: str = Field(..., description="Game title")
    expected_release_date: str | None = Field(
        None,
        description="Expected release date (may be TBD or approximate)",
    )
    description: str = Field(..., description="Brief description and why it's anticipated")


class ReleasedGame(BaseModel):
    """Recently released game with rating."""

    name: str = Field(..., description="Game title")
    release_date: date = Field(..., description="Actual release date")
    rating: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Rating score (e.g., Metacritic or aggregate)",
    )
    description: str = Field(..., description="Brief description and reception")


class UpcomingGame(BaseModel):
    """Upcoming game with expected release."""

    name: str = Field(..., description="Game title")
    expected_release_date: str | None = Field(
        None,
        description="Expected release date or window",
    )
    description: str = Field(..., description="Brief description of the game")


class PoorlyReceivedGame(BaseModel):
    """Poorly received or controversial game."""

    name: str = Field(..., description="Game title")
    release_date: date = Field(..., description="Release date")
    rating: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Low rating score",
    )
    description: str = Field(..., description="Why it was poorly received")


class Reference(BaseModel):
    """Source reference used in the report."""

    title: str = Field(..., description="Reference title or source name")
    url: str = Field(..., description="URL to the source")
    accessed_date: date | None = Field(
        None,
        description="Date the source was accessed",
    )


class ReportSections(BaseModel):
    """Structured sections of the gaming report."""

    highly_anticipated: list[AnticipatedGame] = Field(
        default_factory=list,
        description="Highly anticipated upcoming games",
    )
    recently_released: list[ReleasedGame] = Field(
        default_factory=list,
        description="Recently released games with ratings",
    )
    upcoming_games: list[UpcomingGame] = Field(
        default_factory=list,
        description="Upcoming games with expected release dates",
    )
    poorly_received: list[PoorlyReceivedGame] = Field(
        default_factory=list,
        description="Poorly received or controversial games",
    )


class GameReportResponse(BaseModel):
    """Response schema for a generated gaming report."""

    report_markdown: str = Field(..., description="Complete gaming report in markdown format")
    sections: ReportSections = Field(..., description="Structured sections of the report")
    references: list[Reference] = Field(
        default_factory=list,
        description="List of sources and references used in the report",
    )
    generated_at: datetime = Field(..., description="ISO 8601 timestamp when the report was generated")
    fact_check_passed: bool = Field(..., description="Whether the report passed fact-checking validation")
    validation_errors: list[str] | None = Field(
        None,
        description="List of validation errors if any occurred",
    )
