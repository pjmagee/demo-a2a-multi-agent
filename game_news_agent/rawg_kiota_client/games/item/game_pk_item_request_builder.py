from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from kiota_abstractions.default_query_parameters import QueryParameters
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.method import Method
from kiota_abstractions.request_adapter import RequestAdapter
from kiota_abstractions.request_information import RequestInformation
from kiota_abstractions.request_option import RequestOption
from kiota_abstractions.serialization import Parsable, ParsableFactory
from typing import Any, Optional, TYPE_CHECKING, Union
from warnings import warn

if TYPE_CHECKING:
    from ...models.game_single import GameSingle
    from .achievements.achievements_request_builder import AchievementsRequestBuilder
    from .additions.additions_request_builder import AdditionsRequestBuilder
    from .development_team.development_team_request_builder import DevelopmentTeamRequestBuilder
    from .game_series.game_series_request_builder import GameSeriesRequestBuilder
    from .movies.movies_request_builder import MoviesRequestBuilder
    from .parent_games.parent_games_request_builder import ParentGamesRequestBuilder
    from .reddit.reddit_request_builder import RedditRequestBuilder
    from .screenshots.screenshots_request_builder import ScreenshotsRequestBuilder
    from .stores.stores_request_builder import StoresRequestBuilder
    from .suggested.suggested_request_builder import SuggestedRequestBuilder
    from .twitch.twitch_request_builder import TwitchRequestBuilder
    from .youtube.youtube_request_builder import YoutubeRequestBuilder

class Game_pkItemRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /games/{game_pk-id}
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new Game_pkItemRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/games/{game_pk%2Did}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[GameSingle]:
        """
        Get details of the game.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[GameSingle]
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from ...models.game_single import GameSingle

        return await self.request_adapter.send_async(request_info, GameSingle, None)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> Game_pkItemRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: Game_pkItemRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return Game_pkItemRequestBuilder(self.request_adapter, raw_url)
    
    @property
    def achievements(self) -> AchievementsRequestBuilder:
        """
        The achievements property
        """
        from .achievements.achievements_request_builder import AchievementsRequestBuilder

        return AchievementsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def additions(self) -> AdditionsRequestBuilder:
        """
        The additions property
        """
        from .additions.additions_request_builder import AdditionsRequestBuilder

        return AdditionsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def development_team(self) -> DevelopmentTeamRequestBuilder:
        """
        The developmentTeam property
        """
        from .development_team.development_team_request_builder import DevelopmentTeamRequestBuilder

        return DevelopmentTeamRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def game_series(self) -> GameSeriesRequestBuilder:
        """
        The gameSeries property
        """
        from .game_series.game_series_request_builder import GameSeriesRequestBuilder

        return GameSeriesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def movies(self) -> MoviesRequestBuilder:
        """
        The movies property
        """
        from .movies.movies_request_builder import MoviesRequestBuilder

        return MoviesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def parent_games(self) -> ParentGamesRequestBuilder:
        """
        The parentGames property
        """
        from .parent_games.parent_games_request_builder import ParentGamesRequestBuilder

        return ParentGamesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def reddit(self) -> RedditRequestBuilder:
        """
        The reddit property
        """
        from .reddit.reddit_request_builder import RedditRequestBuilder

        return RedditRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def screenshots(self) -> ScreenshotsRequestBuilder:
        """
        The screenshots property
        """
        from .screenshots.screenshots_request_builder import ScreenshotsRequestBuilder

        return ScreenshotsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def stores(self) -> StoresRequestBuilder:
        """
        The stores property
        """
        from .stores.stores_request_builder import StoresRequestBuilder

        return StoresRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def suggested(self) -> SuggestedRequestBuilder:
        """
        The suggested property
        """
        from .suggested.suggested_request_builder import SuggestedRequestBuilder

        return SuggestedRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def twitch(self) -> TwitchRequestBuilder:
        """
        The twitch property
        """
        from .twitch.twitch_request_builder import TwitchRequestBuilder

        return TwitchRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def youtube(self) -> YoutubeRequestBuilder:
        """
        The youtube property
        """
        from .youtube.youtube_request_builder import YoutubeRequestBuilder

        return YoutubeRequestBuilder(self.request_adapter, self.path_parameters)
    
    @dataclass
    class Game_pkItemRequestBuilderGetRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

