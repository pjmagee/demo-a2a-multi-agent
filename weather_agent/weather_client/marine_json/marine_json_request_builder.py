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
    from .marine_get_response import MarineGetResponse

class MarineJsonRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /marine.json
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new MarineJsonRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/marine.json?days={days}&q={q}{&dt*,hour*,lang*,unixdt*}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[MarineJsonRequestBuilderGetQueryParameters]] = None) -> Optional[MarineGetResponse]:
        """
        Marine weather API method returns upto next 7 day (depending upon your price plan level) marine and sailing weather forecast and tide data (depending upon your price plan level) as json or xml. The data is returned as a Marine Object.<br /><br />Marine object, depending upon your price plan level, contains astronomy data, day weather forecast and hourly interval weather information and tide data for a given sea/ocean point.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[MarineGetResponse]
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
        from .marine_get_response import MarineGetResponse

        return await self.request_adapter.send_async(request_info, MarineGetResponse, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[MarineJsonRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        Marine weather API method returns upto next 7 day (depending upon your price plan level) marine and sailing weather forecast and tide data (depending upon your price plan level) as json or xml. The data is returned as a Marine Object.<br /><br />Marine object, depending upon your price plan level, contains astronomy data, day weather forecast and hourly interval weather information and tide data for a given sea/ocean point.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> MarineJsonRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: MarineJsonRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return MarineJsonRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class MarineJsonRequestBuilderGetQueryParameters():
        """
        Marine weather API method returns upto next 7 day (depending upon your price plan level) marine and sailing weather forecast and tide data (depending upon your price plan level) as json or xml. The data is returned as a Marine Object.<br /><br />Marine object, depending upon your price plan level, contains astronomy data, day weather forecast and hourly interval weather information and tide data for a given sea/ocean point.
        """
        # Number of days of weather forecast. Value ranges from 1 to 7
        days: Optional[int] = None

        # Date should be between today and next 7 day in yyyy-MM-dd format. e.g. '2023-05-20'
        dt: Optional[datetime.date] = None

        # Must be in 24 hour. For example 5 pm should be hour=17, 6 am as hour=6
        hour: Optional[int] = None

        # Returns 'condition:text' field in API in the desired language.<br /> Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to check 'lang-code'.
        lang: Optional[str] = None

        # Pass Latitude/Longitude (decimal degree) which is on a sea/ocean. Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to learn more.
        q: Optional[str] = None

        # Please either pass 'dt' or 'unixdt' and not both in same request. unixdt should be between today and next 7 day in Unix format. e.g. 1490227200
        unixdt: Optional[int] = None

    
    @dataclass
    class MarineJsonRequestBuilderGetRequestConfiguration(RequestConfiguration[MarineJsonRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

