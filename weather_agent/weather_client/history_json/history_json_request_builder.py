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
    from .history_get_response import HistoryGetResponse

class HistoryJsonRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /history.json
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new HistoryJsonRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/history.json?dt={dt}&q={q}{&end_dt*,hour*,lang*,unixdt*,unixend_dt*}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[HistoryJsonRequestBuilderGetQueryParameters]] = None) -> Optional[HistoryGetResponse]:
        """
        History weather API method returns historical weather for a date on or after 1st Jan, 2010 as json. The data is returned as a Forecast Object.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[HistoryGetResponse]
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
        from .history_get_response import HistoryGetResponse

        return await self.request_adapter.send_async(request_info, HistoryGetResponse, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[HistoryJsonRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        History weather API method returns historical weather for a date on or after 1st Jan, 2010 as json. The data is returned as a Forecast Object.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> HistoryJsonRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: HistoryJsonRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return HistoryJsonRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class HistoryJsonRequestBuilderGetQueryParameters():
        """
        History weather API method returns historical weather for a date on or after 1st Jan, 2010 as json. The data is returned as a Forecast Object.
        """
        # Date on or after 1st Jan, 2015 in yyyy-MM-dd format
        dt: Optional[datetime.date] = None

        # Date on or after 1st Jan, 2015 in yyyy-MM-dd format<br />'end_dt' should be greater than 'dt' parameter and difference should not be more than 30 days between the two dates.
        end_dt: Optional[datetime.date] = None

        # Must be in 24 hour. For example 5 pm should be hour=17, 6 am as hour=6
        hour: Optional[int] = None

        # Returns 'condition:text' field in API in the desired language.<br /> Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to check 'lang-code'.
        lang: Optional[str] = None

        # Pass US Zipcode, UK Postcode, Canada Postalcode, IP address, Latitude/Longitude (decimal degree) or city name. Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to learn more.
        q: Optional[str] = None

        # Please either pass 'dt' or 'unixdt' and not both in same request.<br />unixdt should be on or after 1st Jan, 2015 in Unix format
        unixdt: Optional[int] = None

        # Date on or after 1st Jan, 2015 in Unix Timestamp format<br />unixend_dt has same restriction as 'end_dt' parameter. Please either pass 'end_dt' or 'unixend_dt' and not both in same request. e.g. unixend_dt=1490227200
        unixend_dt: Optional[int] = None

    
    @dataclass
    class HistoryJsonRequestBuilderGetRequestConfiguration(RequestConfiguration[HistoryJsonRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

