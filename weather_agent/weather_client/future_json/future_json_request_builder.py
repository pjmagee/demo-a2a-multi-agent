from __future__ import annotations
import datetime
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
    from ..models.error400 import Error400
    from ..models.error401 import Error401
    from ..models.error403 import Error403
    from .future_get_response import FutureGetResponse

class FutureJsonRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /future.json
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new FutureJsonRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/future.json?q={q}{&dt*,lang*}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[FutureJsonRequestBuilderGetQueryParameters]] = None) -> Optional[FutureGetResponse]:
        """
        Future weather API method returns weather in a 3 hourly interval in future for a date between 14 days and 365 days from today in the future.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[FutureGetResponse]
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        from ..models.error400 import Error400
        from ..models.error401 import Error401
        from ..models.error403 import Error403

        error_mapping: dict[str, type[ParsableFactory]] = {
            "400": Error400,
            "401": Error401,
            "403": Error403,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from .future_get_response import FutureGetResponse

        return await self.request_adapter.send_async(request_info, FutureGetResponse, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[FutureJsonRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        Future weather API method returns weather in a 3 hourly interval in future for a date between 14 days and 365 days from today in the future.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> FutureJsonRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: FutureJsonRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return FutureJsonRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class FutureJsonRequestBuilderGetQueryParameters():
        """
        Future weather API method returns weather in a 3 hourly interval in future for a date between 14 days and 365 days from today in the future.
        """
        # Date should be between 14 days and 300 days from today in the future in yyyy-MM-dd format (i.e. dt=2023-01-01)
        dt: Optional[datetime.date] = None

        # Returns 'condition:text' field in API in the desired language.<br /> Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to check 'lang-code'.
        lang: Optional[str] = None

        # Pass US Zipcode, UK Postcode, Canada Postalcode, IP address, Latitude/Longitude (decimal degree) or city name. Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to learn more.
        q: Optional[str] = None

    
    @dataclass
    class FutureJsonRequestBuilderGetRequestConfiguration(RequestConfiguration[FutureJsonRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

