from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class Current_air_quality(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The co property
    co: Optional[float] = None
    # The gbDefraIndex property
    gb_defra_index: Optional[int] = None
    # The no2 property
    no2: Optional[float] = None
    # The o3 property
    o3: Optional[float] = None
    # The pm10 property
    pm10: Optional[float] = None
    # The pm2_5 property
    pm2_5: Optional[float] = None
    # The so2 property
    so2: Optional[float] = None
    # The usEpaIndex property
    us_epa_index: Optional[int] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Current_air_quality:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Current_air_quality
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Current_air_quality()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "co": lambda n : setattr(self, 'co', n.get_float_value()),
            "gb-defra-index": lambda n : setattr(self, 'gb_defra_index', n.get_int_value()),
            "no2": lambda n : setattr(self, 'no2', n.get_float_value()),
            "o3": lambda n : setattr(self, 'o3', n.get_float_value()),
            "pm10": lambda n : setattr(self, 'pm10', n.get_float_value()),
            "pm2_5": lambda n : setattr(self, 'pm2_5', n.get_float_value()),
            "so2": lambda n : setattr(self, 'so2', n.get_float_value()),
            "us-epa-index": lambda n : setattr(self, 'us_epa_index', n.get_int_value()),
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
        writer.write_float_value("co", self.co)
        writer.write_int_value("gb-defra-index", self.gb_defra_index)
        writer.write_float_value("no2", self.no2)
        writer.write_float_value("o3", self.o3)
        writer.write_float_value("pm10", self.pm10)
        writer.write_float_value("pm2_5", self.pm2_5)
        writer.write_float_value("so2", self.so2)
        writer.write_int_value("us-epa-index", self.us_epa_index)
        writer.write_additional_data_value(self.additional_data)
    

