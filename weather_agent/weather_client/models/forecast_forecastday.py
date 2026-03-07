from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .forecast_forecastday_astro import Forecast_forecastday_astro
    from .forecast_forecastday_day import Forecast_forecastday_day
    from .forecast_forecastday_hour import Forecast_forecastday_hour

@dataclass
class Forecast_forecastday(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The astro property
    astro: Optional[Forecast_forecastday_astro] = None
    # The date property
    date: Optional[datetime.date] = None
    # The date_epoch property
    date_epoch: Optional[int] = None
    # The day property
    day: Optional[Forecast_forecastday_day] = None
    # The hour property
    hour: Optional[list[Forecast_forecastday_hour]] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Forecast_forecastday:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Forecast_forecastday
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Forecast_forecastday()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .forecast_forecastday_astro import Forecast_forecastday_astro
        from .forecast_forecastday_day import Forecast_forecastday_day
        from .forecast_forecastday_hour import Forecast_forecastday_hour

        from .forecast_forecastday_astro import Forecast_forecastday_astro
        from .forecast_forecastday_day import Forecast_forecastday_day
        from .forecast_forecastday_hour import Forecast_forecastday_hour

        fields: dict[str, Callable[[Any], None]] = {
            "astro": lambda n : setattr(self, 'astro', n.get_object_value(Forecast_forecastday_astro)),
            "date": lambda n : setattr(self, 'date', n.get_date_value()),
            "date_epoch": lambda n : setattr(self, 'date_epoch', n.get_int_value()),
            "day": lambda n : setattr(self, 'day', n.get_object_value(Forecast_forecastday_day)),
            "hour": lambda n : setattr(self, 'hour', n.get_collection_of_object_values(Forecast_forecastday_hour)),
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
        writer.write_object_value("astro", self.astro)
        writer.write_date_value("date", self.date)
        writer.write_int_value("date_epoch", self.date_epoch)
        writer.write_object_value("day", self.day)
        writer.write_collection_of_object_values("hour", self.hour)
        writer.write_additional_data_value(self.additional_data)
    

