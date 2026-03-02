"""RAWG API service wrapper using Microsoft Kiota-generated client."""

from __future__ import annotations

import html
import logging
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx
from games.games_get_response import GamesGetResponse
from kiota_abstractions.authentication import AnonymousAuthenticationProvider
from kiota_abstractions.base_request_configuration import RequestConfiguration
from kiota_abstractions.request_information import RequestInformation
from kiota_http.httpx_request_adapter import HttpxRequestAdapter

from game_news_agent.models import GameMode
from rawg_kiota_client.games.games_request_builder import GamesRequestBuilder
from rawg_kiota_client.models.game_single import GameSingle
from rawg_kiota_client.rawg_client import RawgClient


@dataclass
class GameReview:
    """A single user review from the RAWG /reviews endpoint."""

    id: int
    text: str
    rating: int
    username: str
    likes_positive: int = 0
    likes_count: int = 0


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_review_text(raw: str) -> str:
    """Strip HTML tags and unescape entities from review text."""
    text = _HTML_TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return " ".join(text.split())  # collapse whitespace

logger = logging.getLogger(__name__)


class ApiKeyHttpxAdapter(HttpxRequestAdapter):
    """Custom adapter that adds API key to all requests."""

    def __init__(self, auth_provider, api_key: str):
        """Initialize with API key."""
        super().__init__(auth_provider)
        self.api_key = api_key

    def get_serialization_writer_factory(self):
        """Override to access request adapter methods."""
        return super().get_serialization_writer_factory()

    def get_request_from_request_information(
        self, request_info: RequestInformation, parent_span=None, attribute_span=None
    ):
        """Override to add API key to the URL before creating the httpx Request."""
        # Call parent to get the httpx Request object
        request = super().get_request_from_request_information(request_info, parent_span, attribute_span)

        # Add API key to the URL
        url_str = str(request.url)
        separator = '&' if '?' in url_str else '?'
        modified_url = f"{url_str}{separator}key={self.api_key}"

        # Create new request with modified URL
        from httpx import Request
        modified_request = Request(
            method=request.method,
            url=modified_url,
            headers=request.headers,
            content=request.content,
        )

        logger.debug(f"Modified request URL: {modified_url}")
        return modified_request
class RAWGKiotaClient:
    """Clean wrapper around Kiota-generated RAWG client."""

    def __init__(self, api_key: str | None = None):
        """Initialize the RAWG Kiota client.

        Args:
            api_key: Optional RAWG API key (defaults to env var RAWG_API_KEY)
        """
        self.api_key = api_key or os.getenv("RAWG_API_KEY", "")

        # Create custom request adapter with API key injection
        auth_provider = AnonymousAuthenticationProvider()
        self.request_adapter = ApiKeyHttpxAdapter(auth_provider, self.api_key)

        # Create the client (serializers are registered automatically in RawgClient.__init__)
        self.client = RawgClient(self.request_adapter)

    async def close(self) -> None:
        """Close the HTTP client."""
        # The request adapter handles cleanup internally
        pass
    async def __aenter__(self) -> RAWGKiotaClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def get_game_details(self, game_id: int) -> GameSingle | None:
        """Get detailed information about a specific game.

        Args:
            game_id: RAWG game ID

        Returns:
            GameSingle model or None if not found
        """
        try:
            game = await self.client.games.by_game_pk_id(str(game_id)).get()
            return game
        except Exception as e:
            print(f"Error fetching game details: {e}")
            return None

    async def search_games(
        self,
        query: str,
        page_size: int = 20,
        ordering: str | None = None,
        search_precise: bool = True,
        search_exact: bool = False,
    ) -> list[dict[str, Any]]:
        """Search for games by query.

        Args:
            query: Search query (game name or description)
            page_size: Number of results to return
            ordering: Sort order; None uses RAWG relevance ranking (recommended for name search)
            search_precise: Disable fuzzy search — results must contain the search term (default True)
            search_exact: Restrict to exact title matches only (stricter than search_precise)

        Returns:
            List of game data dicts
        """
        try:
            # Create request configuration with query parameters
            config = RequestConfiguration[GamesRequestBuilder.GamesRequestBuilderGetQueryParameters]()
            config.query_parameters = GamesRequestBuilder.GamesRequestBuilderGetQueryParameters()
            config.query_parameters.search = query
            config.query_parameters.page_size = page_size
            config.query_parameters.search_precise = search_precise
            config.query_parameters.search_exact = search_exact
            if ordering:
                config.query_parameters.ordering = ordering

            response: GamesGetResponse | None = await self.client.games.get(request_configuration=config)

            logger.info(f"RAWG search response: {response}")
            logger.info(f"Results count: {len(response.results) if response and response.results else 0}")

            if response and response.results:
                return [self._game_to_dict(game) for game in response.results]
            return []
        except Exception as e:
            logger.error(f"Error searching games: {e}", exc_info=True)
            return []

    async def get_games_by_genre(
        self,
        genre: str,
        dates: str,
        page_size: int = 20,
        ordering: str = "-released",
    ) -> list[dict[str, Any]]:
        """Get games filtered by genre and date range.

        Args:
            genre: Genre slug
            dates: Date range in format "YYYY-MM-DD,YYYY-MM-DD"
            page_size: Number of results
            ordering: Sort order

        Returns:
            List of game data dicts
        """
        try:
            # Create request configuration with query parameters
            config = RequestConfiguration[GamesRequestBuilder.GamesRequestBuilderGetQueryParameters]()
            config.query_parameters = GamesRequestBuilder.GamesRequestBuilderGetQueryParameters()
            config.query_parameters.genres = genre
            config.query_parameters.dates = dates
            config.query_parameters.page_size = page_size
            config.query_parameters.ordering = ordering

            response = await self.client.games.get(request_configuration=config)

            if response and response.results:
                return [self._game_to_dict(game) for game in response.results]
            return []
        except Exception as e:
            print(f"Error fetching games by genre: {e}")
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
        try:
            config = RequestConfiguration[GamesRequestBuilder.GamesRequestBuilderGetQueryParameters]()
            config.query_parameters = GamesRequestBuilder.GamesRequestBuilderGetQueryParameters()
            config.query_parameters.genres = genre
            config.query_parameters.dates = f"{date_from.isoformat()},{date_to.isoformat()}"
            config.query_parameters.ordering = "-metacritic,-rating"
            config.query_parameters.metacritic = "80,100"
            config.query_parameters.page_size = page_size
            if game_modes:
                config.query_parameters.tags = self._map_game_modes_to_tags(game_modes)

            response = await self.client.games.get(request_configuration=config)

            if response and response.results:
                return [self._game_to_dict(game) for game in response.results]
            return []
        except Exception as e:
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
        try:
            config = RequestConfiguration[GamesRequestBuilder.GamesRequestBuilderGetQueryParameters]()
            config.query_parameters = GamesRequestBuilder.GamesRequestBuilderGetQueryParameters()
            config.query_parameters.genres = genre
            config.query_parameters.dates = f"{date_from.isoformat()},{date_to.isoformat()}"
            config.query_parameters.ordering = "metacritic,rating"
            config.query_parameters.metacritic = "1,50"
            config.query_parameters.page_size = page_size
            if game_modes:
                config.query_parameters.tags = self._map_game_modes_to_tags(game_modes)

            response = await self.client.games.get(request_configuration=config)

            if response and response.results:
                return [self._game_to_dict(game) for game in response.results]
            return []
        except Exception as e:
            logger.error(f"Error fetching poorly rated games: {e}")
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
        try:
            config = RequestConfiguration[GamesRequestBuilder.GamesRequestBuilderGetQueryParameters]()
            config.query_parameters = GamesRequestBuilder.GamesRequestBuilderGetQueryParameters()
            config.query_parameters.genres = genre
            config.query_parameters.dates = f"{date_from.isoformat()},2027-12-31"
            config.query_parameters.ordering = "released"
            config.query_parameters.page_size = page_size
            if game_modes:
                config.query_parameters.tags = self._map_game_modes_to_tags(game_modes)

            response = await self.client.games.get(request_configuration=config)

            if response and response.results:
                # Filter to only games with future or TBD release dates
                upcoming = [
                    game
                    for game in response.results
                    if not game.released or game.tba or str(game.released) >= date_from.isoformat()
                ]
                return [self._game_to_dict(game) for game in upcoming]
            return []
        except Exception as e:
            logger.error(f"Error fetching upcoming games: {e}")
            return []

    async def get_game_reviews(
        self,
        game_id: int | str,
        page_size: int = 20,
        ordering: str = "-rating",
    ) -> list[GameReview]:
        """Get user reviews for a specific game from the RAWG /reviews endpoint.

        The RAWG /reviews endpoint is undocumented (not in the OpenAPI spec) but accepts
        both numeric IDs and slug strings, e.g.:
            GET /api/games/3328/reviews
            GET /api/games/the-witcher-3-wild-hunt/reviews

        Args:
            game_id: RAWG game ID (int) or slug (str, e.g. 'the-witcher-3-wild-hunt')
            page_size: Number of reviews to fetch per page
            ordering: Sort order — '-rating' (highest first), 'rating' (lowest first),
                      '-created' (newest first), 'created' (oldest first)

        Returns:
            List of GameReview objects; entries with no text are filtered out
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.rawg.io/api/games/{game_id}/reviews",
                    params={
                        "key": self.api_key,
                        "page_size": page_size,
                        "ordering": ordering,
                    },
                )
                response.raise_for_status()
                data = response.json()

            results = data.get("results", [])
            total = data.get("count", "?")
            logger.info(f"Fetched {len(results)}/{total} reviews for '{game_id}' (ordering={ordering})")
            reviews = []
            for r in results:
                raw_text = r.get("text") or ""
                text = _clean_review_text(raw_text)
                if len(text) < 50:  # skip trivially short reviews ("10/10", "Good game")
                    continue
                reviews.append(
                    GameReview(
                        id=r["id"],
                        text=text,
                        rating=r.get("rating", 0),
                        username=r.get("user", {}).get("username", "unknown"),
                        likes_positive=r.get("likes_positive", 0),
                        likes_count=r.get("likes_count", 0),
                    )
                )
            logger.info(f"After filtering short texts: {len(reviews)} usable reviews")
            return reviews
        except Exception as e:
            logger.error(f"Error fetching reviews for game '{game_id}': {e}")
            return []

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

    def _game_to_dict(self, game: Any) -> dict[str, Any]:
        """Convert game model to dict.

        Args:
            game: Game model instance

        Returns:
            Dictionary representation
        """
        # Kiota models have attributes, convert to dict
        # Properly serialize nested objects like platforms and genres
        platforms = getattr(game, "platforms", None)
        serialized_platforms = []
        if platforms:
            for p in platforms:
                platform_obj = getattr(p, "platform", None)
                if platform_obj:
                    serialized_platforms.append({
                        "platform": {
                            "id": getattr(platform_obj, "id", None),
                            "name": getattr(platform_obj, "name", None),
                            "slug": getattr(platform_obj, "slug", None),
                        }
                    })

        genres_list = getattr(game, "genres", None)
        serialized_genres = []
        if genres_list:
            for g in genres_list:
                serialized_genres.append({
                    "id": getattr(g, "id", None),
                    "name": getattr(g, "name", None),
                    "slug": getattr(g, "slug", None),
                })

        return {
            "id": getattr(game, "id", None),
            "name": getattr(game, "name", None),
            "released": getattr(game, "released", None),
            "rating": getattr(game, "rating", None),
            "metacritic": getattr(game, "metacritic", None),
            "background_image": getattr(game, "background_image", None),
            "platforms": serialized_platforms,
            "genres": serialized_genres,
            "tba": getattr(game, "tba", None),
        }
