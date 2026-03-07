from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class Location(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The country property
    country: Optional[str] = None
    # The lat property
    lat: Optional[float] = None
    # The localtime property
    localtime: Optional[str] = None
    # The localtime_epoch property
    localtime_epoch: Optional[int] = None
    # The lon property
    lon: Optional[float] = None
    # The name property
    name: Optional[str] = None
    # The region property
    region: Optional[str] = None
    # The tz_id property
    tz_id: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Location:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Location
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Location()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "country": lambda n : setattr(self, 'country', n.get_str_value()),
            "lat": lambda n : setattr(self, 'lat', n.get_float_value()),
            "localtime": lambda n : setattr(self, 'localtime', n.get_str_value()),
            "localtime_epoch": lambda n : setattr(self, 'localtime_epoch', n.get_int_value()),
            "lon": lambda n : setattr(self, 'lon', n.get_float_value()),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "region": lambda n : setattr(self, 'region', n.get_str_value()),
            "tz_id": lambda n : setattr(self, 'tz_id', n.get_str_value()),
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
        writer.write_str_value("country", self.country)
        writer.write_float_value("lat", self.lat)
        writer.write_str_value("localtime", self.localtime)
        writer.write_int_value("localtime_epoch", self.localtime_epoch)
        writer.write_float_value("lon", self.lon)
        writer.write_str_value("name", self.name)
        writer.write_str_value("region", self.region)
        writer.write_str_value("tz_id", self.tz_id)
        writer.write_additional_data_value(self.additional_data)
    

