from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .game_esrb_rating_name import Game_esrb_rating_name
    from .game_esrb_rating_slug import Game_esrb_rating_slug

@dataclass
class Game_esrb_rating(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The id property
    id: Optional[int] = None
    # The name property
    name: Optional[Game_esrb_rating_name] = None
    # The slug property
    slug: Optional[Game_esrb_rating_slug] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Game_esrb_rating:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Game_esrb_rating
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Game_esrb_rating()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .game_esrb_rating_name import Game_esrb_rating_name
        from .game_esrb_rating_slug import Game_esrb_rating_slug

        from .game_esrb_rating_name import Game_esrb_rating_name
        from .game_esrb_rating_slug import Game_esrb_rating_slug

        fields: dict[str, Callable[[Any], None]] = {
            "id": lambda n : setattr(self, 'id', n.get_int_value()),
            "name": lambda n : setattr(self, 'name', n.get_enum_value(Game_esrb_rating_name)),
            "slug": lambda n : setattr(self, 'slug', n.get_enum_value(Game_esrb_rating_slug)),
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
        writer.write_int_value("id", self.id)
        writer.write_enum_value("name", self.name)
        writer.write_enum_value("slug", self.slug)
        writer.write_additional_data_value(self.additional_data)
    

