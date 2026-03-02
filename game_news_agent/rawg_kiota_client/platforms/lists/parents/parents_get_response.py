from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ....models.platform_parent_single import PlatformParentSingle

@dataclass
class ParentsGetResponse(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The count property
    count: Optional[int] = None
    # The next property
    next: Optional[str] = None
    # The previous property
    previous: Optional[str] = None
    # The results property
    results: Optional[list[PlatformParentSingle]] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ParentsGetResponse:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ParentsGetResponse
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ParentsGetResponse()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from ....models.platform_parent_single import PlatformParentSingle

        from ....models.platform_parent_single import PlatformParentSingle

        fields: dict[str, Callable[[Any], None]] = {
            "count": lambda n : setattr(self, 'count', n.get_int_value()),
            "next": lambda n : setattr(self, 'next', n.get_str_value()),
            "previous": lambda n : setattr(self, 'previous', n.get_str_value()),
            "results": lambda n : setattr(self, 'results', n.get_collection_of_object_values(PlatformParentSingle)),
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
        writer.write_int_value("count", self.count)
        writer.write_str_value("next", self.next)
        writer.write_str_value("previous", self.previous)
        writer.write_collection_of_object_values("results", self.results)
        writer.write_additional_data_value(self.additional_data)
    

