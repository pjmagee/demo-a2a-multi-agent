from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class Platform(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The games_count property
    games_count: Optional[int] = None
    # The id property
    id: Optional[int] = None
    # The image property
    image: Optional[str] = None
    # The image_background property
    image_background: Optional[str] = None
    # The name property
    name: Optional[str] = None
    # The slug property
    slug: Optional[str] = None
    # The year_end property
    year_end: Optional[int] = None
    # The year_start property
    year_start: Optional[int] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Platform:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Platform
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Platform()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "games_count": lambda n : setattr(self, 'games_count', n.get_int_value()),
            "id": lambda n : setattr(self, 'id', n.get_int_value()),
            "image": lambda n : setattr(self, 'image', n.get_str_value()),
            "image_background": lambda n : setattr(self, 'image_background', n.get_str_value()),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "slug": lambda n : setattr(self, 'slug', n.get_str_value()),
            "year_end": lambda n : setattr(self, 'year_end', n.get_int_value()),
            "year_start": lambda n : setattr(self, 'year_start', n.get_int_value()),
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
        writer.write_str_value("name", self.name)
        writer.write_int_value("year_end", self.year_end)
        writer.write_int_value("year_start", self.year_start)
        writer.write_additional_data_value(self.additional_data)
    

