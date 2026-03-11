"""Pydantic models for the Group Chat API."""

from pydantic import BaseModel, Field


class AgentDefinition(BaseModel):
    """An agent participant in the group chat."""

    name: str = Field(description="Unique name for the agent")
    system_prompt: str = Field(description="System prompt / instructions for the agent")


class AgentListResponse(BaseModel):
    """Response containing all configured agents."""

    agents: list[AgentDefinition]


class AgUiMessage(BaseModel):
    """A message in the AG-UI protocol format."""

    id: str
    role: str
    content: str


class RunAgentInput(BaseModel):
    """Input payload for the AG-UI SSE endpoint."""

    thread_id: str = Field(alias="threadId", default="")
    run_id: str = Field(alias="runId", default="")
    messages: list[AgUiMessage] = Field(default_factory=list[AgUiMessage])

    model_config = {"populate_by_name": True}
