from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .astronomy_astro import Astronomy_astro

@dataclass
class Astronomy(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The astro property
    astro: Optional[Astronomy_astro] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Astronomy:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Astronomy
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Astronomy()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .astronomy_astro import Astronomy_astro

        from .astronomy_astro import Astronomy_astro

        fields: dict[str, Callable[[Any], None]] = {
            "astro": lambda n : setattr(self, 'astro', n.get_object_value(Astronomy_astro)),
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
        writer.write_additional_data_value(self.additional_data)
    

