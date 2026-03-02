from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .game_platform_metacritic import GamePlatformMetacritic
    from .game_single_added_by_status import GameSingle_added_by_status
    from .game_single_esrb_rating import GameSingle_esrb_rating
    from .game_single_platforms import GameSingle_platforms
    from .game_single_ratings import GameSingle_ratings
    from .game_single_reactions import GameSingle_reactions

@dataclass
class GameSingle(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The achievements_count property
    achievements_count: Optional[int] = None
    # The added property
    added: Optional[int] = None
    # The added_by_status property
    added_by_status: Optional[GameSingle_added_by_status] = None
    # The additions_count property
    additions_count: Optional[int] = None
    # The alternative_names property
    alternative_names: Optional[list[str]] = None
    # The background_image property
    background_image: Optional[str] = None
    # The background_image_additional property
    background_image_additional: Optional[str] = None
    # The creators_count property
    creators_count: Optional[int] = None
    # The description property
    description: Optional[str] = None
    # The esrb_rating property
    esrb_rating: Optional[GameSingle_esrb_rating] = None
    # The game_series_count property
    game_series_count: Optional[int] = None
    # The id property
    id: Optional[int] = None
    # The metacritic property
    metacritic: Optional[int] = None
    # The metacritic_platforms property
    metacritic_platforms: Optional[list[GamePlatformMetacritic]] = None
    # For example "http://www.metacritic.com/game/playstation-4/the-witcher-3-wild-hunt"
    metacritic_url: Optional[str] = None
    # The movies_count property
    movies_count: Optional[int] = None
    # The name property
    name: Optional[str] = None
    # The name_original property
    name_original: Optional[str] = None
    # The parent_achievements_count property
    parent_achievements_count: Optional[str] = None
    # The parents_count property
    parents_count: Optional[int] = None
    # The platforms property
    platforms: Optional[list[GameSingle_platforms]] = None
    # in hours
    playtime: Optional[int] = None
    # The rating property
    rating: Optional[float] = None
    # The rating_top property
    rating_top: Optional[int] = None
    # The ratings property
    ratings: Optional[GameSingle_ratings] = None
    # The ratings_count property
    ratings_count: Optional[int] = None
    # The reactions property
    reactions: Optional[GameSingle_reactions] = None
    # The reddit_count property
    reddit_count: Optional[int] = None
    # The reddit_description property
    reddit_description: Optional[str] = None
    # The reddit_logo property
    reddit_logo: Optional[str] = None
    # The reddit_name property
    reddit_name: Optional[str] = None
    # For example "https://www.reddit.com/r/uncharted/" or "uncharted"
    reddit_url: Optional[str] = None
    # The released property
    released: Optional[datetime.date] = None
    # The reviews_text_count property
    reviews_text_count: Optional[str] = None
    # The screenshots_count property
    screenshots_count: Optional[int] = None
    # The slug property
    slug: Optional[str] = None
    # The suggestions_count property
    suggestions_count: Optional[int] = None
    # The tba property
    tba: Optional[bool] = None
    # The twitch_count property
    twitch_count: Optional[str] = None
    # The updated property
    updated: Optional[datetime.datetime] = None
    # The website property
    website: Optional[str] = None
    # The youtube_count property
    youtube_count: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> GameSingle:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: GameSingle
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return GameSingle()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .game_platform_metacritic import GamePlatformMetacritic
        from .game_single_added_by_status import GameSingle_added_by_status
        from .game_single_esrb_rating import GameSingle_esrb_rating
        from .game_single_platforms import GameSingle_platforms
        from .game_single_ratings import GameSingle_ratings
        from .game_single_reactions import GameSingle_reactions

        from .game_platform_metacritic import GamePlatformMetacritic
        from .game_single_added_by_status import GameSingle_added_by_status
        from .game_single_esrb_rating import GameSingle_esrb_rating
        from .game_single_platforms import GameSingle_platforms
        from .game_single_ratings import GameSingle_ratings
        from .game_single_reactions import GameSingle_reactions

        fields: dict[str, Callable[[Any], None]] = {
            "achievements_count": lambda n : setattr(self, 'achievements_count', n.get_int_value()),
            "added": lambda n : setattr(self, 'added', n.get_int_value()),
            "added_by_status": lambda n : setattr(self, 'added_by_status', n.get_object_value(GameSingle_added_by_status)),
            "additions_count": lambda n : setattr(self, 'additions_count', n.get_int_value()),
            "alternative_names": lambda n : setattr(self, 'alternative_names', n.get_collection_of_primitive_values(str)),
            "background_image": lambda n : setattr(self, 'background_image', n.get_str_value()),
            "background_image_additional": lambda n : setattr(self, 'background_image_additional', n.get_str_value()),
            "creators_count": lambda n : setattr(self, 'creators_count', n.get_int_value()),
            "description": lambda n : setattr(self, 'description', n.get_str_value()),
            "esrb_rating": lambda n : setattr(self, 'esrb_rating', n.get_object_value(GameSingle_esrb_rating)),
            "game_series_count": lambda n : setattr(self, 'game_series_count', n.get_int_value()),
            "id": lambda n : setattr(self, 'id', n.get_int_value()),
            "metacritic": lambda n : setattr(self, 'metacritic', n.get_int_value()),
            "metacritic_platforms": lambda n : setattr(self, 'metacritic_platforms', n.get_collection_of_object_values(GamePlatformMetacritic)),
            "metacritic_url": lambda n : setattr(self, 'metacritic_url', n.get_str_value()),
            "movies_count": lambda n : setattr(self, 'movies_count', n.get_int_value()),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "name_original": lambda n : setattr(self, 'name_original', n.get_str_value()),
            "parent_achievements_count": lambda n : setattr(self, 'parent_achievements_count', n.get_str_value()),
            "parents_count": lambda n : setattr(self, 'parents_count', n.get_int_value()),
            "platforms": lambda n : setattr(self, 'platforms', n.get_collection_of_object_values(GameSingle_platforms)),
            "playtime": lambda n : setattr(self, 'playtime', n.get_int_value()),
            "rating": lambda n : setattr(self, 'rating', n.get_float_value()),
            "rating_top": lambda n : setattr(self, 'rating_top', n.get_int_value()),
            "ratings": lambda n : setattr(self, 'ratings', n.get_object_value(GameSingle_ratings)),
            "ratings_count": lambda n : setattr(self, 'ratings_count', n.get_int_value()),
            "reactions": lambda n : setattr(self, 'reactions', n.get_object_value(GameSingle_reactions)),
            "reddit_count": lambda n : setattr(self, 'reddit_count', n.get_int_value()),
            "reddit_description": lambda n : setattr(self, 'reddit_description', n.get_str_value()),
            "reddit_logo": lambda n : setattr(self, 'reddit_logo', n.get_str_value()),
            "reddit_name": lambda n : setattr(self, 'reddit_name', n.get_str_value()),
            "reddit_url": lambda n : setattr(self, 'reddit_url', n.get_str_value()),
            "released": lambda n : setattr(self, 'released', n.get_date_value()),
            "reviews_text_count": lambda n : setattr(self, 'reviews_text_count', n.get_str_value()),
            "screenshots_count": lambda n : setattr(self, 'screenshots_count', n.get_int_value()),
            "slug": lambda n : setattr(self, 'slug', n.get_str_value()),
            "suggestions_count": lambda n : setattr(self, 'suggestions_count', n.get_int_value()),
            "tba": lambda n : setattr(self, 'tba', n.get_bool_value()),
            "twitch_count": lambda n : setattr(self, 'twitch_count', n.get_str_value()),
            "updated": lambda n : setattr(self, 'updated', n.get_datetime_value()),
            "website": lambda n : setattr(self, 'website', n.get_str_value()),
            "youtube_count": lambda n : setattr(self, 'youtube_count', n.get_str_value()),
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
    

