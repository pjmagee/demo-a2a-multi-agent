"""Schemas for BFF messaging endpoints."""

from pydantic import BaseModel, Field


class SendMessagePayload(BaseModel):
    """Payload for the BFF messaging endpoint."""

    agent_name: str = Field(..., description="Display name from the agent card")
    message: str
    context_id: str | None = None


class MessageResponse(BaseModel):
    """Response from the BFF messaging endpoint."""

    status: str
    context_id: str | None = None
    raw_response: dict[str, object] | None = None
