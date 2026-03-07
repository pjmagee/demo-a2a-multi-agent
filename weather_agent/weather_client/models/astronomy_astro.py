from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class Astronomy_astro(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The moon_illumination property
    moon_illumination: Optional[str] = None
    # The moon_phase property
    moon_phase: Optional[str] = None
    # The moonrise property
    moonrise: Optional[str] = None
    # The moonset property
    moonset: Optional[str] = None
    # The sunrise property
    sunrise: Optional[str] = None
    # The sunset property
    sunset: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Astronomy_astro:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Astronomy_astro
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Astronomy_astro()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "moon_illumination": lambda n : setattr(self, 'moon_illumination', n.get_str_value()),
            "moon_phase": lambda n : setattr(self, 'moon_phase', n.get_str_value()),
            "moonrise": lambda n : setattr(self, 'moonrise', n.get_str_value()),
            "moonset": lambda n : setattr(self, 'moonset', n.get_str_value()),
            "sunrise": lambda n : setattr(self, 'sunrise', n.get_str_value()),
            "sunset": lambda n : setattr(self, 'sunset', n.get_str_value()),
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
        writer.write_str_value("moon_illumination", self.moon_illumination)
        writer.write_str_value("moon_phase", self.moon_phase)
        writer.write_str_value("moonrise", self.moonrise)
        writer.write_str_value("moonset", self.moonset)
        writer.write_str_value("sunrise", self.sunrise)
        writer.write_str_value("sunset", self.sunset)
        writer.write_additional_data_value(self.additional_data)
    

