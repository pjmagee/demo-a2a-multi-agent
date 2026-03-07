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
    from .forecast_get_response import ForecastGetResponse

class ForecastJsonRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /forecast.json
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new ForecastJsonRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/forecast.json?days={days}&q={q}{&alerts*,aqi*,dt*,hour*,lang*,tp*,unixdt*}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[ForecastJsonRequestBuilderGetQueryParameters]] = None) -> Optional[ForecastGetResponse]:
        """
        Forecast weather API method returns, depending upon your price plan level, upto next 14 day weather forecast and weather alert as json or xml. The data is returned as a Forecast Object.<br /><br />Forecast object contains astronomy data, day weather forecast and hourly interval weather information for a given city.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[ForecastGetResponse]
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
        from .forecast_get_response import ForecastGetResponse

        return await self.request_adapter.send_async(request_info, ForecastGetResponse, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[ForecastJsonRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        Forecast weather API method returns, depending upon your price plan level, upto next 14 day weather forecast and weather alert as json or xml. The data is returned as a Forecast Object.<br /><br />Forecast object contains astronomy data, day weather forecast and hourly interval weather information for a given city.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> ForecastJsonRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: ForecastJsonRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return ForecastJsonRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class ForecastJsonRequestBuilderGetQueryParameters():
        """
        Forecast weather API method returns, depending upon your price plan level, upto next 14 day weather forecast and weather alert as json or xml. The data is returned as a Forecast Object.<br /><br />Forecast object contains astronomy data, day weather forecast and hourly interval weather information for a given city.
        """
        # Enable/Disable alerts in forecast API output. Example, alerts=yes or alerts=no.
        alerts: Optional[str] = None

        # Enable/Disable Air Quality data in forecast API output. Example, aqi=yes or aqi=no.
        aqi: Optional[str] = None

        # Number of days of weather forecast. Value ranges from 1 to 14
        days: Optional[int] = None

        # Date should be between today and next 14 day in yyyy-MM-dd format. e.g. '2015-01-01'
        dt: Optional[datetime.date] = None

        # Must be in 24 hour. For example 5 pm should be hour=17, 6 am as hour=6
        hour: Optional[int] = None

        # Returns 'condition:text' field in API in the desired language.<br /> Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to check 'lang-code'.
        lang: Optional[str] = None

        # Pass US Zipcode, UK Postcode, Canada Postalcode, IP address, Latitude/Longitude (decimal degree) or city name. Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to learn more.
        q: Optional[str] = None

        # Get 15 min interval or 24 hour average data for Forecast and History API. Available for Enterprise clients only. E.g:- tp=15
        tp: Optional[int] = None

        # Please either pass 'dt' or 'unixdt' and not both in same request. unixdt should be between today and next 14 day in Unix format. e.g. 1490227200
        unixdt: Optional[int] = None

    
    @dataclass
    class ForecastJsonRequestBuilderGetRequestConfiguration(RequestConfiguration[ForecastJsonRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

