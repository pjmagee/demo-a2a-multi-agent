"""Shared utilities for the multi-agent workspace."""

from shared.mongodb_task_store import MongoDBTaskStore
from shared.openai_session_helpers import ensure_context_id, get_or_create_session
from shared.otel_config import configure_telemetry
from shared.peer_tools import default_peer_tools, peer_message_context
from shared.registry_client import register_with_registry, unregister_from_registry

__all__: list[str] = [
    "MongoDBTaskStore",
    "configure_telemetry",
    "default_peer_tools",
    "ensure_context_id",
    "get_or_create_session",
    "peer_message_context",
    "register_with_registry",
    "unregister_from_registry",
]
