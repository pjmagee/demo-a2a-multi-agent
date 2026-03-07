from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .forecast_forecastday_day_condition import Forecast_forecastday_day_condition

@dataclass
class Forecast_forecastday_day(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The avghumidity property
    avghumidity: Optional[float] = None
    # The avgtemp_c property
    avgtemp_c: Optional[float] = None
    # The avgtemp_f property
    avgtemp_f: Optional[float] = None
    # The avgvis_km property
    avgvis_km: Optional[float] = None
    # The avgvis_miles property
    avgvis_miles: Optional[float] = None
    # The condition property
    condition: Optional[Forecast_forecastday_day_condition] = None
    # The daily_chance_of_rain property
    daily_chance_of_rain: Optional[float] = None
    # The daily_chance_of_snow property
    daily_chance_of_snow: Optional[float] = None
    # The daily_will_it_rain property
    daily_will_it_rain: Optional[int] = None
    # The daily_will_it_snow property
    daily_will_it_snow: Optional[int] = None
    # The maxtemp_c property
    maxtemp_c: Optional[float] = None
    # The maxtemp_f property
    maxtemp_f: Optional[float] = None
    # The maxwind_kph property
    maxwind_kph: Optional[float] = None
    # The maxwind_mph property
    maxwind_mph: Optional[float] = None
    # The mintemp_c property
    mintemp_c: Optional[float] = None
    # The mintemp_f property
    mintemp_f: Optional[float] = None
    # The totalprecip_in property
    totalprecip_in: Optional[float] = None
    # The totalprecip_mm property
    totalprecip_mm: Optional[float] = None
    # The uv property
    uv: Optional[int] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Forecast_forecastday_day:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Forecast_forecastday_day
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Forecast_forecastday_day()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .forecast_forecastday_day_condition import Forecast_forecastday_day_condition

        from .forecast_forecastday_day_condition import Forecast_forecastday_day_condition

        fields: dict[str, Callable[[Any], None]] = {
            "avghumidity": lambda n : setattr(self, 'avghumidity', n.get_float_value()),
            "avgtemp_c": lambda n : setattr(self, 'avgtemp_c', n.get_float_value()),
            "avgtemp_f": lambda n : setattr(self, 'avgtemp_f', n.get_float_value()),
            "avgvis_km": lambda n : setattr(self, 'avgvis_km', n.get_float_value()),
            "avgvis_miles": lambda n : setattr(self, 'avgvis_miles', n.get_float_value()),
            "condition": lambda n : setattr(self, 'condition', n.get_object_value(Forecast_forecastday_day_condition)),
            "daily_chance_of_rain": lambda n : setattr(self, 'daily_chance_of_rain', n.get_float_value()),
            "daily_chance_of_snow": lambda n : setattr(self, 'daily_chance_of_snow', n.get_float_value()),
            "daily_will_it_rain": lambda n : setattr(self, 'daily_will_it_rain', n.get_int_value()),
            "daily_will_it_snow": lambda n : setattr(self, 'daily_will_it_snow', n.get_int_value()),
            "maxtemp_c": lambda n : setattr(self, 'maxtemp_c', n.get_float_value()),
            "maxtemp_f": lambda n : setattr(self, 'maxtemp_f', n.get_float_value()),
            "maxwind_kph": lambda n : setattr(self, 'maxwind_kph', n.get_float_value()),
            "maxwind_mph": lambda n : setattr(self, 'maxwind_mph', n.get_float_value()),
            "mintemp_c": lambda n : setattr(self, 'mintemp_c', n.get_float_value()),
            "mintemp_f": lambda n : setattr(self, 'mintemp_f', n.get_float_value()),
            "totalprecip_in": lambda n : setattr(self, 'totalprecip_in', n.get_float_value()),
            "totalprecip_mm": lambda n : setattr(self, 'totalprecip_mm', n.get_float_value()),
            "uv": lambda n : setattr(self, 'uv', n.get_int_value()),
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
        writer.write_float_value("avghumidity", self.avghumidity)
        writer.write_float_value("avgtemp_c", self.avgtemp_c)
        writer.write_float_value("avgtemp_f", self.avgtemp_f)
        writer.write_float_value("avgvis_km", self.avgvis_km)
        writer.write_float_value("avgvis_miles", self.avgvis_miles)
        writer.write_object_value("condition", self.condition)
        writer.write_float_value("daily_chance_of_rain", self.daily_chance_of_rain)
        writer.write_float_value("daily_chance_of_snow", self.daily_chance_of_snow)
        writer.write_int_value("daily_will_it_rain", self.daily_will_it_rain)
        writer.write_int_value("daily_will_it_snow", self.daily_will_it_snow)
        writer.write_float_value("maxtemp_c", self.maxtemp_c)
        writer.write_float_value("maxtemp_f", self.maxtemp_f)
        writer.write_float_value("maxwind_kph", self.maxwind_kph)
        writer.write_float_value("maxwind_mph", self.maxwind_mph)
        writer.write_float_value("mintemp_c", self.mintemp_c)
        writer.write_float_value("mintemp_f", self.mintemp_f)
        writer.write_float_value("totalprecip_in", self.totalprecip_in)
        writer.write_float_value("totalprecip_mm", self.totalprecip_mm)
        writer.write_int_value("uv", self.uv)
        writer.write_additional_data_value(self.additional_data)
    

