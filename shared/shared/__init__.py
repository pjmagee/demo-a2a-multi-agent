"""Shared utilities for the multi-agent workspace."""

from shared.mongodb_task_store import MongoDBTaskStore
from shared.openai_session_helpers import ensure_context_id, get_or_create_session
from shared.otel_config import configure_telemetry
from shared.peer_tools import default_peer_tools, peer_message_context
from shared.phoenix_setup import setup_phoenix_tracing
from shared.registry_client import register_with_registry, unregister_from_registry
from shared.traced_executor import a2a_session, tag_a2a_span

__all__: list[str] = [
    "MongoDBTaskStore",
    "a2a_session",
    "configure_telemetry",
    "default_peer_tools",
    "ensure_context_id",
    "get_or_create_session",
    "peer_message_context",
    "register_with_registry",
    "setup_phoenix_tracing",
    "tag_a2a_span",
    "unregister_from_registry",
]
