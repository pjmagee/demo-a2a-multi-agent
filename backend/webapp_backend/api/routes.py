"""HTTP routes exposed by the BFF."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from webapp_backend.clients.a2a_client import A2AAgentClient
from webapp_backend.deps import get_agent_client
from webapp_backend.schemas.agents import AgentCardSchema, AgentSkillSchema
from webapp_backend.schemas.messages import MessageResponse, SendMessagePayload

router = APIRouter(prefix="/api")

AgentClientDependency = Annotated[A2AAgentClient, Depends(dependency=get_agent_client)]

if TYPE_CHECKING:
    from a2a.types import AgentCard, AgentSkill
else:
    AgentCard = AgentSkill = Any


def _map_skill(skill: AgentSkill) -> AgentSkillSchema:
    return AgentSkillSchema(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        input_modes=list(skill.input_modes or []),
        output_modes=list(skill.output_modes or []),
    )


def _map_card(card: AgentCard) -> AgentCardSchema:
    return AgentCardSchema(
        name=card.name,
        description=card.description,
        version=getattr(card, "version", None),
        url=card.url,
        skills=[_map_skill(skill) for skill in card.skills or []],
    )


@router.get("/agents", response_model=list[AgentCardSchema])
async def list_agents(client: AgentClientDependency) -> list[AgentCardSchema]:
    """Return metadata for all configured agents."""
    cards = await client.list_agents()
    return [_map_card(card) for card in cards]


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    payload: SendMessagePayload,
    client: AgentClientDependency,
) -> MessageResponse:
    """Send a user message to the given agent."""
    response = await client.send_message(
        agent_name=payload.agent_name,
        message=payload.message,
        context_id=payload.context_id,
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Agent failed to respond",
        )

    response_dict: dict[str, Any] | None = None
    if hasattr(response, "model_dump"):
        response_dict = response.model_dump(exclude_none=True)  # type: ignore[assignment]

    context_id = payload.context_id
    try:
        result = response_dict or {}
        context_id = (
            result.get("result", {})
            .get("message", {})
            .get("context_id", context_id)
        )
    except AttributeError:
        context_id = payload.context_id

    return MessageResponse(
        status="ok",
        context_id=context_id,
        raw_response=response_dict,
    )
