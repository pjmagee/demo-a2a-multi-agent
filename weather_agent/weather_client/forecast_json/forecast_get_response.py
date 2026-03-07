from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..models.alerts import Alerts
    from ..models.current import Current
    from ..models.forecast import Forecast
    from ..models.location import Location

@dataclass
class ForecastGetResponse(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The alerts property
    alerts: Optional[Alerts] = None
    # The current property
    current: Optional[Current] = None
    # The forecast property
    forecast: Optional[Forecast] = None
    # The location property
    location: Optional[Location] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ForecastGetResponse:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ForecastGetResponse
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ForecastGetResponse()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from ..models.alerts import Alerts
        from ..models.current import Current
        from ..models.forecast import Forecast
        from ..models.location import Location

        from ..models.alerts import Alerts
        from ..models.current import Current
        from ..models.forecast import Forecast
        from ..models.location import Location

        fields: dict[str, Callable[[Any], None]] = {
            "alerts": lambda n : setattr(self, 'alerts', n.get_object_value(Alerts)),
            "current": lambda n : setattr(self, 'current', n.get_object_value(Current)),
            "forecast": lambda n : setattr(self, 'forecast', n.get_object_value(Forecast)),
            "location": lambda n : setattr(self, 'location', n.get_object_value(Location)),
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
        writer.write_object_value("alerts", self.alerts)
        writer.write_object_value("current", self.current)
        writer.write_object_value("forecast", self.forecast)
        writer.write_object_value("location", self.location)
        writer.write_additional_data_value(self.additional_data)
    

