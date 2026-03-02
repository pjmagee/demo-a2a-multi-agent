from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .game_single_platforms_platform import GameSingle_platforms_platform
    from .game_single_platforms_requirements import GameSingle_platforms_requirements

@dataclass
class GameSingle_platforms(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The platform property
    platform: Optional[GameSingle_platforms_platform] = None
    # The released_at property
    released_at: Optional[str] = None
    # The requirements property
    requirements: Optional[GameSingle_platforms_requirements] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> GameSingle_platforms:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: GameSingle_platforms
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return GameSingle_platforms()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .game_single_platforms_platform import GameSingle_platforms_platform
        from .game_single_platforms_requirements import GameSingle_platforms_requirements

        from .game_single_platforms_platform import GameSingle_platforms_platform
        from .game_single_platforms_requirements import GameSingle_platforms_requirements

        fields: dict[str, Callable[[Any], None]] = {
            "platform": lambda n : setattr(self, 'platform', n.get_object_value(GameSingle_platforms_platform)),
            "released_at": lambda n : setattr(self, 'released_at', n.get_str_value()),
            "requirements": lambda n : setattr(self, 'requirements', n.get_object_value(GameSingle_platforms_requirements)),
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
        writer.write_object_value("platform", self.platform)
        writer.write_str_value("released_at", self.released_at)
        writer.write_object_value("requirements", self.requirements)
        writer.write_additional_data_value(self.additional_data)
    

