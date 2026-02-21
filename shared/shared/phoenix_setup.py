"""
Phoenix Observability Setup for A2A Agents

This module provides centralized Phoenix tracing configuration for all agents in the
demo-a2a-multi-agent system. It handles:

- OpenTelemetry instrumentation via Phoenix
- Auto-instrumentation of OpenAI SDK
- Session and project tracking
- Environment-based configuration
- Graceful degradation when Phoenix is unavailable

Usage:
    from shared.phoenix_setup import setup_phoenix_tracing
    
    # In your agent's app.py, before any other imports
    setup_phoenix_tracing()

Environment Variables:
    PHOENIX_COLLECTOR_ENDPOINT: Phoenix endpoint URL (default: http://localhost:6006)
    PHOENIX_PROJECT_NAME: Project name for grouping traces (default: demo-a2a-multi-agent)
    PHOENIX_ENABLED: Enable/disable tracing (default: true)
    PHOENIX_API_KEY: API key for Phoenix Cloud (optional, for self-hosted)
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Track initialization state to prevent double-registration
_phoenix_initialized = False


def setup_phoenix_tracing(
    project_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    enable_tracing: bool = True,
) -> bool:
    """
    Initialize Phoenix tracing for the current agent.

    This function:
    1. Checks if Phoenix is enabled (via environment or parameter)
    2. Configures OpenTelemetry with Phoenix endpoint
    3. Auto-instruments OpenAI SDK for automatic trace capture
    4. Sets up project and session tracking
    5. Handles errors gracefully if Phoenix is unavailable

    Args:
        project_name: Project name for grouping traces. Defaults to PHOENIX_PROJECT_NAME env var
                     or "demo-a2a-multi-agent"
        endpoint: Phoenix endpoint URL. Defaults to PHOENIX_COLLECTOR_ENDPOINT env var
                 or "http://localhost:6006"
        enable_tracing: Whether to enable tracing. Defaults to PHOENIX_ENABLED env var or True

    Returns:
        bool: True if Phoenix was successfully initialized, False otherwise

    Example:
        >>> from shared.phoenix_setup import setup_phoenix_tracing
        >>> setup_phoenix_tracing()
        INFO: Phoenix tracing initialized (project=demo-a2a-multi-agent, endpoint=http://localhost:6006)
        True
    """
    global _phoenix_initialized

    # Prevent double initialization
    if _phoenix_initialized:
        logger.debug("Phoenix tracing already initialized, skipping")
        return True

    # Check if tracing is enabled
    enabled = os.environ.get("PHOENIX_ENABLED", "true").lower() == "true"
    if not enable_tracing or not enabled:
        logger.info("Phoenix tracing is disabled")
        return False

    # Get configuration from environment or parameters
    project_name = (
        project_name
        or os.environ.get("PHOENIX_PROJECT_NAME")
        or "demo-a2a-multi-agent"
    )
    endpoint = (
        endpoint or os.environ.get("PHOENIX_COLLECTOR_ENDPOINT") or "http://localhost:6006"
    )

    try:
        # Import Phoenix OTEL registration
        # This should be done as early as possible, ideally before importing OpenAI
        from phoenix.otel import register

        # Register Phoenix tracing with auto-instrumentation
        tracer_provider = register(
            project_name=project_name,
            endpoint=endpoint,
            auto_instrument=True,  # Auto-instrument OpenAI, LangChain, etc.
            batch=True,  # Use batch span processor (production best practice)
        )

        _phoenix_initialized = True
        logger.info(
            f"Phoenix tracing initialized (project={project_name}, endpoint={endpoint})"
        )
        return True

    except ImportError:
        logger.warning(
            "Phoenix OTEL package not installed. Install with: pip install arize-phoenix-otel"
        )
        return False
    except Exception as e:
        logger.warning(f"Failed to initialize Phoenix tracing: {e}")
        logger.debug("Continuing without Phoenix tracing")
        return False


def add_session_attributes(session_id: str, user_id: Optional[str] = None) -> None:
    """
    Add session and user tracking attributes to Phoenix traces.

    This enriches traces with session context, allowing you to:
    - Group traces by conversation/session
    - Track user interactions
    - Analyze session-level metrics

    Args:
        session_id: Unique identifier for the current session/conversation
        user_id: Optional user identifier

    Example:
        >>> from shared.phoenix_setup import add_session_attributes
        >>> add_session_attributes(session_id="conv_123", user_id="user_456")
    """
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer(__name__)
        span = trace.get_current_span()

        if span and span.is_recording():
            span.set_attribute("session.id", session_id)
            if user_id:
                span.set_attribute("user.id", user_id)
            logger.debug(
                f"Added session attributes (session_id={session_id}, user_id={user_id})"
            )
    except ImportError:
        logger.debug("OpenTelemetry not available, skipping session attributes")
    except Exception as e:
        logger.debug(f"Failed to add session attributes: {e}")


def add_custom_attributes(**attributes) -> None:
    """
    Add custom attributes to the current Phoenix trace span.

    Use this to enrich traces with domain-specific metadata:
    - Agent type/role
    - Request identifiers
    - Business context
    - Feature flags

    Args:
        **attributes: Key-value pairs to add as span attributes

    Example:
        >>> from shared.phoenix_setup import add_custom_attributes
        >>> add_custom_attributes(
        ...     agent_type="emergency_operator",
        ...     priority="high",
        ...     incident_id="INC-2026-001234"
        ... )
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in attributes.items():
                span.set_attribute(f"custom.{key}", str(value))
            logger.debug(f"Added custom attributes: {attributes}")
    except ImportError:
        logger.debug("OpenTelemetry not available, skipping custom attributes")
    except Exception as e:
        logger.debug(f"Failed to add custom attributes: {e}")


def is_phoenix_initialized() -> bool:
    """
    Check if Phoenix tracing has been successfully initialized.

    Returns:
        bool: True if Phoenix is initialized and ready to capture traces
    """
    return _phoenix_initialized


# Optional: Context manager for custom spans
class phoenix_span:
    """
    Context manager for creating custom trace spans in Phoenix.

    Use this when you want to trace specific operations that aren't automatically
    instrumented, such as:
    - Business logic processing
    - Data transformations
    - External API calls (non-LLM)

    Args:
        name: Name of the span (describes the operation)
        attributes: Optional attributes to add to the span

    Example:
        >>> from shared.phoenix_setup import phoenix_span
        >>> with phoenix_span("process_emergency_request", incident_type="fire"):
        ...     result = process_incident(data)
    """

    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
        self.span = None
        self.tracer = None

    def __enter__(self):
        try:
            from opentelemetry import trace

            self.tracer = trace.get_tracer(__name__)
            self.span = self.tracer.start_span(self.name)

            # Add attributes
            for key, value in self.attributes.items():
                self.span.set_attribute(key, str(value))

            return self.span
        except ImportError:
            logger.debug("OpenTelemetry not available, span context is a no-op")
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                # Record exception in span
                self.span.record_exception(exc_val)
                self.span.set_status(trace.Status(trace.StatusCode.ERROR))
            self.span.end()
        return False  # Don't suppress exceptions
