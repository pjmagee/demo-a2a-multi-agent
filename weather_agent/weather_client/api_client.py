from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.api_client_builder import enable_backing_store_for_serialization_writer_factory, register_default_deserializer, register_default_serializer
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from kiota_abstractions.serialization import ParseNodeFactoryRegistry, SerializationWriterFactoryRegistry
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .astronomy_json.astronomy_json_request_builder import AstronomyJsonRequestBuilder
    from .current_json.current_json_request_builder import CurrentJsonRequestBuilder
    from .forecast_json.forecast_json_request_builder import ForecastJsonRequestBuilder
    from .future_json.future_json_request_builder import FutureJsonRequestBuilder
    from .history_json.history_json_request_builder import HistoryJsonRequestBuilder
    from .ip_json.ip_json_request_builder import IpJsonRequestBuilder
    from .marine_json.marine_json_request_builder import MarineJsonRequestBuilder
    from .search_json.search_json_request_builder import SearchJsonRequestBuilder
    from .timezone_json.timezone_json_request_builder import TimezoneJsonRequestBuilder

class ApiClient(BaseRequestBuilder):
    """
    The main entry point of the SDK, exposes the configuration and the fluent API.
    """
    def __init__(self,request_adapter: RequestAdapter) -> None:
        """
        Instantiates a new ApiClient and sets the default values.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        if request_adapter is None:
            raise TypeError("request_adapter cannot be null.")
        super().__init__(request_adapter, "{+baseurl}", None)
        if not self.request_adapter.base_url:
            self.request_adapter.base_url = "https://api.weatherapi.com/v1"
        self.path_parameters["base_url"] = self.request_adapter.base_url
    
    @property
    def astronomy_json(self) -> AstronomyJsonRequestBuilder:
        """
        The astronomyJson property
        """
        from .astronomy_json.astronomy_json_request_builder import AstronomyJsonRequestBuilder

        return AstronomyJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def current_json(self) -> CurrentJsonRequestBuilder:
        """
        The currentJson property
        """
        from .current_json.current_json_request_builder import CurrentJsonRequestBuilder

        return CurrentJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def forecast_json(self) -> ForecastJsonRequestBuilder:
        """
        The forecastJson property
        """
        from .forecast_json.forecast_json_request_builder import ForecastJsonRequestBuilder

        return ForecastJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def future_json(self) -> FutureJsonRequestBuilder:
        """
        The futureJson property
        """
        from .future_json.future_json_request_builder import FutureJsonRequestBuilder

        return FutureJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def history_json(self) -> HistoryJsonRequestBuilder:
        """
        The historyJson property
        """
        from .history_json.history_json_request_builder import HistoryJsonRequestBuilder

        return HistoryJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def ip_json(self) -> IpJsonRequestBuilder:
        """
        The ipJson property
        """
        from .ip_json.ip_json_request_builder import IpJsonRequestBuilder

        return IpJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def marine_json(self) -> MarineJsonRequestBuilder:
        """
        The marineJson property
        """
        from .marine_json.marine_json_request_builder import MarineJsonRequestBuilder

        return MarineJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def search_json(self) -> SearchJsonRequestBuilder:
        """
        The searchJson property
        """
        from .search_json.search_json_request_builder import SearchJsonRequestBuilder

        return SearchJsonRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def timezone_json(self) -> TimezoneJsonRequestBuilder:
        """
        The timezoneJson property
        """
        from .timezone_json.timezone_json_request_builder import TimezoneJsonRequestBuilder

        return TimezoneJsonRequestBuilder(self.request_adapter, self.path_parameters)
    

