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
    from .games_get_response import GamesGetResponse
    from .item.game_pk_item_request_builder import Game_pkItemRequestBuilder

class GamesRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /games
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new GamesRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/games{?creators*,dates*,developers*,exclude_additions*,exclude_collection*,exclude_game_series*,exclude_parents*,exclude_stores*,genres*,metacritic*,ordering*,page*,page_size*,parent_platforms*,platforms*,platforms_count*,publishers*,search*,search_exact*,search_precise*,stores*,tags*,updated*}", path_parameters)
    
    def by_game_pk_id(self,game_pk_id: str) -> Game_pkItemRequestBuilder:
        """
        Gets an item from the rawg_kiota_client.games.item collection
        param game_pk_id: An ID or a slug identifying this Game.
        Returns: Game_pkItemRequestBuilder
        """
        if game_pk_id is None:
            raise TypeError("game_pk_id cannot be null.")
        from .item.game_pk_item_request_builder import Game_pkItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["game_pk%2Did"] = game_pk_id
        return Game_pkItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[GamesRequestBuilderGetQueryParameters]] = None) -> Optional[GamesGetResponse]:
        """
        Get a list of games.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[GamesGetResponse]
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from .games_get_response import GamesGetResponse

        return await self.request_adapter.send_async(request_info, GamesGetResponse, None)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[GamesRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> GamesRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: GamesRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return GamesRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class GamesRequestBuilderGetQueryParameters():
        """
        Get a list of games.
        """
        # Filter by creators, for example: `78,28` or `cris-velasco,mike-morasky`.
        creators: Optional[str] = None

        # Filter by a release date, for example: `2010-01-01,2018-12-31.1960-01-01,1969-12-31`.
        dates: Optional[str] = None

        # Filter by developers, for example: `1612,18893` or `valve-software,feral-interactive`.
        developers: Optional[str] = None

        # Exclude additions.
        exclude_additions: Optional[bool] = None

        # Exclude games from a particular collection, for example: `123`.
        exclude_collection: Optional[int] = None

        # Exclude games which included in a game series.
        exclude_game_series: Optional[bool] = None

        # Exclude games which have additions.
        exclude_parents: Optional[bool] = None

        # Exclude stores, for example: `5,6`.
        exclude_stores: Optional[str] = None

        # Filter by genres, for example: `4,51` or `action,indie`.
        genres: Optional[str] = None

        # Filter by a metacritic rating, for example: `80,100`.
        metacritic: Optional[str] = None

        # Available fields: `name`, `released`, `added`, `created`, `updated`, `rating`, `metacritic`. You can reverse the sort order adding a hyphen, for example: `-released`.
        ordering: Optional[str] = None

        # A page number within the paginated result set.
        page: Optional[int] = None

        # Number of results to return per page.
        page_size: Optional[int] = None

        # Filter by parent platforms, for example: `1,2,3`.
        parent_platforms: Optional[str] = None

        # Filter by platforms, for example: `4,5`.
        platforms: Optional[str] = None

        # Filter by platforms count, for example: `1`.
        platforms_count: Optional[int] = None

        # Filter by publishers, for example: `354,20987` or `electronic-arts,microsoft-studios`.
        publishers: Optional[str] = None

        # Search query.
        search: Optional[str] = None

        # Mark the search query as exact.
        search_exact: Optional[bool] = None

        # Disable fuzziness for the search query.
        search_precise: Optional[bool] = None

        # Filter by stores, for example: `5,6`.
        stores: Optional[str] = None

        # Filter by tags, for example: `31,7` or `singleplayer,multiplayer`.
        tags: Optional[str] = None

        # Filter by an update date, for example: `2020-12-01,2020-12-31`.
        updated: Optional[str] = None

    
    @dataclass
    class GamesRequestBuilderGetRequestConfiguration(RequestConfiguration[GamesRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

