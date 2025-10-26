"""Pydantic models for agent metadata."""

from pydantic import BaseModel


class AgentSkillSchema(BaseModel):
    """Pydantic model for agent skill metadata."""

    id: str
    name: str
    description: str
    input_modes: list[str]
    output_modes: list[str]


class AgentCardSchema(BaseModel):
    """Pydantic model for agent metadata."""

    name: str
    description: str
    version: str | None = None
    url: str
    skills: list[AgentSkillSchema]
