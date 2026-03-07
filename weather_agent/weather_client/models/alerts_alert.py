from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class Alerts_alert(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The areas property
    areas: Optional[str] = None
    # The category property
    category: Optional[str] = None
    # The certainty property
    certainty: Optional[str] = None
    # The desc property
    desc: Optional[str] = None
    # The effective property
    effective: Optional[datetime.datetime] = None
    # The event property
    event: Optional[str] = None
    # The expires property
    expires: Optional[datetime.datetime] = None
    # The headline property
    headline: Optional[str] = None
    # The instruction property
    instruction: Optional[str] = None
    # The msgtype property
    msgtype: Optional[str] = None
    # The note property
    note: Optional[str] = None
    # The severity property
    severity: Optional[str] = None
    # The urgency property
    urgency: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Alerts_alert:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Alerts_alert
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Alerts_alert()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "areas": lambda n : setattr(self, 'areas', n.get_str_value()),
            "category": lambda n : setattr(self, 'category', n.get_str_value()),
            "certainty": lambda n : setattr(self, 'certainty', n.get_str_value()),
            "desc": lambda n : setattr(self, 'desc', n.get_str_value()),
            "effective": lambda n : setattr(self, 'effective', n.get_datetime_value()),
            "event": lambda n : setattr(self, 'event', n.get_str_value()),
            "expires": lambda n : setattr(self, 'expires', n.get_datetime_value()),
            "headline": lambda n : setattr(self, 'headline', n.get_str_value()),
            "instruction": lambda n : setattr(self, 'instruction', n.get_str_value()),
            "msgtype": lambda n : setattr(self, 'msgtype', n.get_str_value()),
            "note": lambda n : setattr(self, 'note', n.get_str_value()),
            "severity": lambda n : setattr(self, 'severity', n.get_str_value()),
            "urgency": lambda n : setattr(self, 'urgency', n.get_str_value()),
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
        writer.write_str_value("areas", self.areas)
        writer.write_str_value("category", self.category)
        writer.write_str_value("certainty", self.certainty)
        writer.write_str_value("desc", self.desc)
        writer.write_datetime_value("effective", self.effective)
        writer.write_str_value("event", self.event)
        writer.write_datetime_value("expires", self.expires)
        writer.write_str_value("headline", self.headline)
        writer.write_str_value("instruction", self.instruction)
        writer.write_str_value("msgtype", self.msgtype)
        writer.write_str_value("note", self.note)
        writer.write_str_value("severity", self.severity)
        writer.write_str_value("urgency", self.urgency)
        writer.write_additional_data_value(self.additional_data)
    

