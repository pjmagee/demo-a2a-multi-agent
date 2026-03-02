from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .game_added_by_status import Game_added_by_status
    from .game_esrb_rating import Game_esrb_rating
    from .game_platforms import Game_platforms
    from .game_ratings import Game_ratings

@dataclass
class Game(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The added property
    added: Optional[int] = None
    # The added_by_status property
    added_by_status: Optional[Game_added_by_status] = None
    # The background_image property
    background_image: Optional[str] = None
    # The esrb_rating property
    esrb_rating: Optional[Game_esrb_rating] = None
    # The id property
    id: Optional[int] = None
    # The metacritic property
    metacritic: Optional[int] = None
    # The name property
    name: Optional[str] = None
    # The platforms property
    platforms: Optional[list[Game_platforms]] = None
    # in hours
    playtime: Optional[int] = None
    # The rating property
    rating: Optional[float] = None
    # The rating_top property
    rating_top: Optional[int] = None
    # The ratings property
    ratings: Optional[Game_ratings] = None
    # The ratings_count property
    ratings_count: Optional[int] = None
    # The released property
    released: Optional[datetime.date] = None
    # The reviews_text_count property
    reviews_text_count: Optional[str] = None
    # The slug property
    slug: Optional[str] = None
    # The suggestions_count property
    suggestions_count: Optional[int] = None
    # The tba property
    tba: Optional[bool] = None
    # The updated property
    updated: Optional[datetime.datetime] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Game:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Game
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Game()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .game_added_by_status import Game_added_by_status
        from .game_esrb_rating import Game_esrb_rating
        from .game_platforms import Game_platforms
        from .game_ratings import Game_ratings

        from .game_added_by_status import Game_added_by_status
        from .game_esrb_rating import Game_esrb_rating
        from .game_platforms import Game_platforms
        from .game_ratings import Game_ratings

        fields: dict[str, Callable[[Any], None]] = {
            "added": lambda n : setattr(self, 'added', n.get_int_value()),
            "added_by_status": lambda n : setattr(self, 'added_by_status', n.get_object_value(Game_added_by_status)),
            "background_image": lambda n : setattr(self, 'background_image', n.get_str_value()),
            "esrb_rating": lambda n : setattr(self, 'esrb_rating', n.get_object_value(Game_esrb_rating)),
            "id": lambda n : setattr(self, 'id', n.get_int_value()),
            "metacritic": lambda n : setattr(self, 'metacritic', n.get_int_value()),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "platforms": lambda n : setattr(self, 'platforms', n.get_collection_of_object_values(Game_platforms)),
            "playtime": lambda n : setattr(self, 'playtime', n.get_int_value()),
            "rating": lambda n : setattr(self, 'rating', n.get_float_value()),
            "rating_top": lambda n : setattr(self, 'rating_top', n.get_int_value()),
            "ratings": lambda n : setattr(self, 'ratings', n.get_object_value(Game_ratings)),
            "ratings_count": lambda n : setattr(self, 'ratings_count', n.get_int_value()),
            "released": lambda n : setattr(self, 'released', n.get_date_value()),
            "reviews_text_count": lambda n : setattr(self, 'reviews_text_count', n.get_str_value()),
            "slug": lambda n : setattr(self, 'slug', n.get_str_value()),
            "suggestions_count": lambda n : setattr(self, 'suggestions_count', n.get_int_value()),
            "tba": lambda n : setattr(self, 'tba', n.get_bool_value()),
            "updated": lambda n : setattr(self, 'updated', n.get_datetime_value()),
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
        writer.write_object_value("esrb_rating", self.esrb_rating)
        writer.write_collection_of_object_values("platforms", self.platforms)
        writer.write_float_value("rating", self.rating)
        writer.write_additional_data_value(self.additional_data)
    

