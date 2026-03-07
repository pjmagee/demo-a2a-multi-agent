from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .forecast_forecastday_hour_condition import Forecast_forecastday_hour_condition

@dataclass
class Forecast_forecastday_hour(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The chance_of_rain property
    chance_of_rain: Optional[float] = None
    # The chance_of_snow property
    chance_of_snow: Optional[float] = None
    # The cloud property
    cloud: Optional[float] = None
    # The condition property
    condition: Optional[Forecast_forecastday_hour_condition] = None
    # The dewpoint_c property
    dewpoint_c: Optional[float] = None
    # The dewpoint_f property
    dewpoint_f: Optional[float] = None
    # The feelslike_c property
    feelslike_c: Optional[float] = None
    # The feelslike_f property
    feelslike_f: Optional[float] = None
    # The gust_kph property
    gust_kph: Optional[float] = None
    # The gust_mph property
    gust_mph: Optional[float] = None
    # The heatindex_c property
    heatindex_c: Optional[float] = None
    # The heatindex_f property
    heatindex_f: Optional[float] = None
    # The humidity property
    humidity: Optional[float] = None
    # The is_day property
    is_day: Optional[int] = None
    # The precip_in property
    precip_in: Optional[float] = None
    # The precip_mm property
    precip_mm: Optional[float] = None
    # The pressure_in property
    pressure_in: Optional[float] = None
    # The pressure_mb property
    pressure_mb: Optional[float] = None
    # The temp_c property
    temp_c: Optional[float] = None
    # The temp_f property
    temp_f: Optional[float] = None
    # The time property
    time: Optional[str] = None
    # The time_epoch property
    time_epoch: Optional[int] = None
    # The uv property
    uv: Optional[int] = None
    # The vis_km property
    vis_km: Optional[float] = None
    # The vis_miles property
    vis_miles: Optional[float] = None
    # The will_it_rain property
    will_it_rain: Optional[int] = None
    # The will_it_snow property
    will_it_snow: Optional[int] = None
    # The wind_degree property
    wind_degree: Optional[float] = None
    # The wind_dir property
    wind_dir: Optional[str] = None
    # The wind_kph property
    wind_kph: Optional[float] = None
    # The wind_mph property
    wind_mph: Optional[float] = None
    # The windchill_c property
    windchill_c: Optional[float] = None
    # The windchill_f property
    windchill_f: Optional[float] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Forecast_forecastday_hour:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Forecast_forecastday_hour
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Forecast_forecastday_hour()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .forecast_forecastday_hour_condition import Forecast_forecastday_hour_condition

        from .forecast_forecastday_hour_condition import Forecast_forecastday_hour_condition

        fields: dict[str, Callable[[Any], None]] = {
            "chance_of_rain": lambda n : setattr(self, 'chance_of_rain', n.get_float_value()),
            "chance_of_snow": lambda n : setattr(self, 'chance_of_snow', n.get_float_value()),
            "cloud": lambda n : setattr(self, 'cloud', n.get_float_value()),
            "condition": lambda n : setattr(self, 'condition', n.get_object_value(Forecast_forecastday_hour_condition)),
            "dewpoint_c": lambda n : setattr(self, 'dewpoint_c', n.get_float_value()),
            "dewpoint_f": lambda n : setattr(self, 'dewpoint_f', n.get_float_value()),
            "feelslike_c": lambda n : setattr(self, 'feelslike_c', n.get_float_value()),
            "feelslike_f": lambda n : setattr(self, 'feelslike_f', n.get_float_value()),
            "gust_kph": lambda n : setattr(self, 'gust_kph', n.get_float_value()),
            "gust_mph": lambda n : setattr(self, 'gust_mph', n.get_float_value()),
            "heatindex_c": lambda n : setattr(self, 'heatindex_c', n.get_float_value()),
            "heatindex_f": lambda n : setattr(self, 'heatindex_f', n.get_float_value()),
            "humidity": lambda n : setattr(self, 'humidity', n.get_float_value()),
            "is_day": lambda n : setattr(self, 'is_day', n.get_int_value()),
            "precip_in": lambda n : setattr(self, 'precip_in', n.get_float_value()),
            "precip_mm": lambda n : setattr(self, 'precip_mm', n.get_float_value()),
            "pressure_in": lambda n : setattr(self, 'pressure_in', n.get_float_value()),
            "pressure_mb": lambda n : setattr(self, 'pressure_mb', n.get_float_value()),
            "temp_c": lambda n : setattr(self, 'temp_c', n.get_float_value()),
            "temp_f": lambda n : setattr(self, 'temp_f', n.get_float_value()),
            "time": lambda n : setattr(self, 'time', n.get_str_value()),
            "time_epoch": lambda n : setattr(self, 'time_epoch', n.get_int_value()),
            "uv": lambda n : setattr(self, 'uv', n.get_int_value()),
            "vis_km": lambda n : setattr(self, 'vis_km', n.get_float_value()),
            "vis_miles": lambda n : setattr(self, 'vis_miles', n.get_float_value()),
            "will_it_rain": lambda n : setattr(self, 'will_it_rain', n.get_int_value()),
            "will_it_snow": lambda n : setattr(self, 'will_it_snow', n.get_int_value()),
            "wind_degree": lambda n : setattr(self, 'wind_degree', n.get_float_value()),
            "wind_dir": lambda n : setattr(self, 'wind_dir', n.get_str_value()),
            "wind_kph": lambda n : setattr(self, 'wind_kph', n.get_float_value()),
            "wind_mph": lambda n : setattr(self, 'wind_mph', n.get_float_value()),
            "windchill_c": lambda n : setattr(self, 'windchill_c', n.get_float_value()),
            "windchill_f": lambda n : setattr(self, 'windchill_f', n.get_float_value()),
        }
        return fields
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        writer.write_float_value("chance_of_rain", self.chance_of_rain)
        writer.write_float_value("chance_of_snow", self.chance_of_snow)
        writer.write_float_value("cloud", self.cloud)
        writer.write_object_value("condition", self.condition)
        writer.write_float_value("dewpoint_c", self.dewpoint_c)
        writer.write_float_value("dewpoint_f", self.dewpoint_f)
        writer.write_float_value("feelslike_c", self.feelslike_c)
        writer.write_float_value("feelslike_f", self.feelslike_f)
        writer.write_float_value("gust_kph", self.gust_kph)
        writer.write_float_value("gust_mph", self.gust_mph)
        writer.write_float_value("heatindex_c", self.heatindex_c)
        writer.write_float_value("heatindex_f", self.heatindex_f)
        writer.write_float_value("humidity", self.humidity)
        writer.write_int_value("is_day", self.is_day)
        writer.write_float_value("precip_in", self.precip_in)
        writer.write_float_value("precip_mm", self.precip_mm)
        writer.write_float_value("pressure_in", self.pressure_in)
        writer.write_float_value("pressure_mb", self.pressure_mb)
        writer.write_float_value("temp_c", self.temp_c)
        writer.write_float_value("temp_f", self.temp_f)
        writer.write_str_value("time", self.time)
        writer.write_int_value("time_epoch", self.time_epoch)
        writer.write_int_value("uv", self.uv)
        writer.write_float_value("vis_km", self.vis_km)
        writer.write_float_value("vis_miles", self.vis_miles)
        writer.write_int_value("will_it_rain", self.will_it_rain)
        writer.write_int_value("will_it_snow", self.will_it_snow)
        writer.write_float_value("wind_degree", self.wind_degree)
        writer.write_str_value("wind_dir", self.wind_dir)
        writer.write_float_value("wind_kph", self.wind_kph)
        writer.write_float_value("wind_mph", self.wind_mph)
        writer.write_float_value("windchill_c", self.windchill_c)
        writer.write_float_value("windchill_f", self.windchill_f)
        writer.write_additional_data_value(self.additional_data)
    

