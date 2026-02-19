"""RAWG API client for fetching game data."""

import logging
import os
from datetime import date
from typing import Any

import httpx

from game_news_agent.models import GameMode

logger = logging.getLogger(__name__)

RAWG_BASE_URL = "https://api.rawg.io/api"


class RAWGClient:
    """Client for RAWG.io game database API."""

    def __init__(self, api_key: str | None = None):
        """Initialize RAWG client.

        Args:
            api_key: RAWG API key (optional, fetched from env if not provided)
        """
        self.api_key = api_key or os.getenv("RAWG_API_KEY", "")
        self.client = httpx.AsyncClient(
            base_url=RAWG_BASE_URL,
            timeout=30.0,
            headers={"User-Agent": "GameNewsAgent/0.1.0"},
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "RAWGClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    def _build_params(self, **kwargs) -> dict[str, Any]:
        """Build query parameters with API key."""
        params = {"key": self.api_key} if self.api_key else {}
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return params

    def _map_game_modes_to_tags(self, game_modes: list[GameMode]) -> str:
        """Map game modes to RAWG tags.

        Args:
            game_modes: List of game mode enums

        Returns:
            Comma-separated string of RAWG tag IDs
        """
        tag_mapping = {
            GameMode.SINGLE_PLAYER: "singleplayer",
            GameMode.MULTI_PLAYER: "multiplayer",
            GameMode.ONLINE: "online",
            GameMode.OFFLINE: "offline",
        }
        tags = [tag_mapping.get(mode) for mode in game_modes if mode in tag_mapping]
        return ",".join(filter(None, tags))

    async def get_games_by_genre(
        self,
        genre: str,
        date_from: date,
        date_to: date,
        game_modes: list[GameMode] | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Get games by genre and release date range.

        Args:
            genre: Genre slug (e.g., 'rpg', 'action')
            date_from: Start date for filtering
            date_to: End date for filtering
            game_modes: Optional list of game modes to filter
            page_size: Number of results to return

        Returns:
            List of game data dicts
        """
        params = self._build_params(
            genres=genre,
            dates=f"{date_from.isoformat()},{date_to.isoformat()}",
            ordering="-released",
            page_size=page_size,
        )

        if game_modes:
            tags = self._map_game_modes_to_tags(game_modes)
            if tags:
                params["tags"] = tags

        try:
            response = await self.client.get("/games", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching games by genre: {e}")
            return []

    async def get_upcoming_games(
        self,
        genre: str,
        date_from: date,
        game_modes: list[GameMode] | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Get upcoming games (future releases).

        Args:
            genre: Genre slug
            date_from: Start date for filtering upcoming releases
            game_modes: Optional list of game modes to filter
            page_size: Number of results to return

        Returns:
            List of upcoming game data dicts
        """
        params = self._build_params(
            genres=genre,
            dates=f"{date_from.isoformat()},2027-12-31",  # Far future date
            ordering="released",  # Ascending to get nearest releases first
            page_size=page_size,
        )

        if game_modes:
            tags = self._map_game_modes_to_tags(game_modes)
            if tags:
                params["tags"] = tags

        try:
            response = await self.client.get("/games", params=params)
            response.raise_for_status()
            data = response.json()
            # Filter to only games with future or TBD release dates
            results = data.get("results", [])
            upcoming = [
                game
                for game in results
                if game.get("released") is None or game.get("tba") or game.get("released") >= date_from.isoformat()
            ]
            return upcoming
        except httpx.HTTPError as e:
            logger.error(f"Error fetching upcoming games: {e}")
            return []

    async def get_highly_rated_games(
        self,
        genre: str,
        date_from: date,
        date_to: date,
        game_modes: list[GameMode] | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Get highly rated games in date range.

        Args:
            genre: Genre slug
            date_from: Start date for filtering
            date_to: End date for filtering
            game_modes: Optional list of game modes to filter
            page_size: Number of results to return

        Returns:
            List of highly rated game data dicts
        """
        params = self._build_params(
            genres=genre,
            dates=f"{date_from.isoformat()},{date_to.isoformat()}",
            ordering="-metacritic,-rating",  # Sort by Metacritic, then rating
            metacritic="80,100",  # Only highly rated games
            page_size=page_size,
        )

        if game_modes:
            tags = self._map_game_modes_to_tags(game_modes)
            if tags:
                params["tags"] = tags

        try:
            response = await self.client.get("/games", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching highly rated games: {e}")
            return []

    async def get_poorly_rated_games(
        self,
        genre: str,
        date_from: date,
        date_to: date,
        game_modes: list[GameMode] | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Get poorly rated games in date range.

        Args:
            genre: Genre slug
            date_from: Start date for filtering
            date_to: End date for filtering
            game_modes: Optional list of game modes to filter
            page_size: Number of results to return

        Returns:
            List of poorly rated game data dicts
        """
        params = self._build_params(
            genres=genre,
            dates=f"{date_from.isoformat()},{date_to.isoformat()}",
            ordering="metacritic,rating",  # Sort by lowest rating
            metacritic="1,50",  # Only poorly rated games
            page_size=page_size,
        )

        if game_modes:
            tags = self._map_game_modes_to_tags(game_modes)
            if tags:
                params["tags"] = tags

        try:
            response = await self.client.get("/games", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching poorly rated games: {e}")
            return []
