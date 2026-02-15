"""Data models for the A2A Registry."""

from datetime import UTC, datetime

from a2a.types import AgentCard
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Request to register an agent."""

    address: str = Field(
        ...,
        description="Base URL of the agent (e.g., http://127.0.0.1:8011)",
    )
    agent_card: AgentCard = Field(
        ...,
        description="Agent card containing agent metadata",
    )


class RegisterResponse(BaseModel):
    """Response from agent registration."""

    status: str = Field(default="registered")
    agent_name: str = Field(..., description="Name of the registered agent")
    address: str = Field(..., description="Address of the registered agent")


class UnregisterResponse(BaseModel):
    """Response from agent unregistration."""

    status: str = Field(default="unregistered")
    address: str = Field(..., description="Address of the unregistered agent")


class AgentEntry(BaseModel):
    """Entry for a registered agent."""

    address: str = Field(..., description="Base URL of the agent")
    agent_card: AgentCard = Field(..., description="Agent card metadata")
    registered_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO timestamp of registration",
    )


class AgentsListResponse(BaseModel):
    """Response listing all registered agents."""

    agents: list[AgentEntry] = Field(
        default_factory=list,
        description="List of registered agents",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    agent_count: int = Field(..., description="Number of registered agents")
