from pydantic import BaseModel
from typing import Any

class StartRunInput(BaseModel):
    agent_id: str
    messages: list[dict[str, Any]] = []
    state: dict[str, Any] = {}

class AddMessageInput(BaseModel):
    content: str
    role: str = "user"

class RunInfo(BaseModel):
    run_id: str
    agent_id: str
    created_at: int
    status: str
    messages: list[dict[str, Any]] = []
    state: dict[str, Any] = {}