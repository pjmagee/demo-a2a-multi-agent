"""Helper functions for managing OpenAI Agents SDK sessions."""

import uuid

from a2a.server.agent_execution.context import RequestContext
from agents import SQLiteSession
from agents.memory.session import Session


def ensure_context_id(context: RequestContext) -> str:
    """Ensure RequestContext has a context_id, creating one if needed.

    According to A2A protocol, the SERVER should create context_id
    if not provided by the client. This should be called in the
    executor before invoking the agent.

    Args:
        context: RequestContext that may or may not have context_id

    Returns:
        A valid context_id string (either from context or newly created)

    """
    if isinstance(context.context_id, str) and context.context_id:
        return context.context_id
    return str(object=uuid.uuid4())


def get_or_create_session(
    sessions: dict[str, Session],
    context_id: str,
) -> Session:
    """Get or create a session for the given context ID.

    Args:
        sessions: Dictionary to store sessions (modified in-place)
        context_id: Unique identifier for the session

    Returns:
        Session object for the given context_id

    """
    if context_id not in sessions:
        sessions[context_id] = SQLiteSession(session_id=context_id)
    return sessions[context_id]


def get_or_create_session_from_context(
    sessions: dict[str, Session],
    context: RequestContext,
) -> Session | None:
    """Get or create a session from a RequestContext.

    Args:
        sessions: Dictionary to store sessions (modified in-place)
        context: RequestContext containing context_id

    Returns:
        Session object if context_id is valid, None otherwise

    """
    if isinstance(context.context_id, str):
        return get_or_create_session(sessions, context.context_id)
    return None
