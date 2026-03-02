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
    from .item.platforms_item_request_builder import PlatformsItemRequestBuilder
    from .lists.lists_request_builder import ListsRequestBuilder
    from .platforms_get_response import PlatformsGetResponse

class PlatformsRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /platforms
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new PlatformsRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/platforms{?ordering*,page*,page_size*}", path_parameters)
    
    def by_id(self,id: int) -> PlatformsItemRequestBuilder:
        """
        Gets an item from the rawg_kiota_client.platforms.item collection
        param id: A unique integer value identifying this Platform.
        Returns: PlatformsItemRequestBuilder
        """
        if id is None:
            raise TypeError("id cannot be null.")
        from .item.platforms_item_request_builder import PlatformsItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["id"] = id
        return PlatformsItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[PlatformsRequestBuilderGetQueryParameters]] = None) -> Optional[PlatformsGetResponse]:
        """
        Get a list of video game platforms.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[PlatformsGetResponse]
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from .platforms_get_response import PlatformsGetResponse

        return await self.request_adapter.send_async(request_info, PlatformsGetResponse, None)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[PlatformsRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> PlatformsRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: PlatformsRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return PlatformsRequestBuilder(self.request_adapter, raw_url)
    
    @property
    def lists(self) -> ListsRequestBuilder:
        """
        The lists property
        """
        from .lists.lists_request_builder import ListsRequestBuilder

        return ListsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @dataclass
    class PlatformsRequestBuilderGetQueryParameters():
        """
        Get a list of video game platforms.
        """
        # Which field to use when ordering the results.
        ordering: Optional[str] = None

        # A page number within the paginated result set.
        page: Optional[int] = None

        # Number of results to return per page.
        page_size: Optional[int] = None

    
    @dataclass
    class PlatformsRequestBuilderGetRequestConfiguration(RequestConfiguration[PlatformsRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

