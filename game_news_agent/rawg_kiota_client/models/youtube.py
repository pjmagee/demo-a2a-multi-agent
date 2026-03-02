from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .youtube_thumbnails import Youtube_thumbnails

@dataclass
class Youtube(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The channel_id property
    channel_id: Optional[str] = None
    # The channel_title property
    channel_title: Optional[str] = None
    # The comments_count property
    comments_count: Optional[int] = None
    # The created property
    created: Optional[datetime.datetime] = None
    # The description property
    description: Optional[str] = None
    # The dislike_count property
    dislike_count: Optional[int] = None
    # The external_id property
    external_id: Optional[str] = None
    # The favorite_count property
    favorite_count: Optional[int] = None
    # The id property
    id: Optional[int] = None
    # The like_count property
    like_count: Optional[int] = None
    # The name property
    name: Optional[str] = None
    # The thumbnails property
    thumbnails: Optional[Youtube_thumbnails] = None
    # The view_count property
    view_count: Optional[int] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Youtube:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Youtube
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Youtube()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .youtube_thumbnails import Youtube_thumbnails

        from .youtube_thumbnails import Youtube_thumbnails

        fields: dict[str, Callable[[Any], None]] = {
            "channel_id": lambda n : setattr(self, 'channel_id', n.get_str_value()),
            "channel_title": lambda n : setattr(self, 'channel_title', n.get_str_value()),
            "comments_count": lambda n : setattr(self, 'comments_count', n.get_int_value()),
            "created": lambda n : setattr(self, 'created', n.get_datetime_value()),
            "description": lambda n : setattr(self, 'description', n.get_str_value()),
            "dislike_count": lambda n : setattr(self, 'dislike_count', n.get_int_value()),
            "external_id": lambda n : setattr(self, 'external_id', n.get_str_value()),
            "favorite_count": lambda n : setattr(self, 'favorite_count', n.get_int_value()),
            "id": lambda n : setattr(self, 'id', n.get_int_value()),
            "like_count": lambda n : setattr(self, 'like_count', n.get_int_value()),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "thumbnails": lambda n : setattr(self, 'thumbnails', n.get_object_value(Youtube_thumbnails)),
            "view_count": lambda n : setattr(self, 'view_count', n.get_int_value()),
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
        writer.write_additional_data_value(self.additional_data)
    

