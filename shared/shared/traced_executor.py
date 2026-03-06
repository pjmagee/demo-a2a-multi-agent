"""OTEL helper for tagging the active span with A2A request metadata.

``FastAPIInstrumentor`` already creates an HTTP root span for every A2A
request.  Using ``a2a_session`` from within an executor's ``execute()``
enriches that span with A2A metadata *and* propagates ``session.id`` via
OTel baggage so every child LLM / tool span is automatically grouped into
the same Phoenix session.

Usage::

    from a2a.server.agent_execution.context import RequestContext
    from shared.traced_executor import a2a_session

    async def execute(self, context: RequestContext, ...) -> None:
        with a2a_session(context, type(self).__name__) as context_id:
            ...
"""

from collections.abc import Iterator
from contextlib import contextmanager

from a2a.server.agent_execution.context import RequestContext
from opentelemetry import baggage, trace
from opentelemetry.context import attach, detach

from .openai_session_helpers import ensure_context_id


@contextmanager
def a2a_session(context: RequestContext, executor_name: str) -> Iterator[str]:
    """Enrich the active OTEL span with A2A attributes and propagate session.id.

    Sets ``a2a.task_id``, ``a2a.context_id``, ``a2a.executor``, and
    ``session.id`` on the currently active span (typically the FastAPI HTTP
    span).  Attaches ``session.id`` as OTel baggage so every child span
    created inside the ``with`` block inherits the attribute via
    ``_SessionIdBaggageSpanProcessor`` in phoenix_setup.

    Args:
        context: The A2A request context.
        executor_name: ``type(self).__name__`` of the calling executor.

    Yields:
        The canonical context_id string.
    """
    context_id = ensure_context_id(context)
    span = trace.get_current_span()
    if span.is_recording():
        if context.task_id:
            span.set_attribute("a2a.task_id", context.task_id)
        if context.context_id:
            span.set_attribute("a2a.context_id", context.context_id)
        span.set_attribute("a2a.executor", executor_name)
        span.set_attribute("session.id", context_id)
    token = attach(baggage.set_baggage("session.id", context_id))
    try:
        yield context_id
    finally:
        detach(token)


# ---------------------------------------------------------------------------
# Back-compat shim – prefer a2a_session for new code.
# ---------------------------------------------------------------------------

def tag_a2a_span(context: RequestContext, executor_name: str) -> None:
    """Enrich the current active OTEL span with A2A request attributes.

    Deprecated: use the ``a2a_session`` context manager instead.
    """
    span = trace.get_current_span()
    if not span.is_recording():
        return
    if context.task_id:
        span.set_attribute("a2a.task_id", context.task_id)
    if context.context_id:
        span.set_attribute("a2a.context_id", context.context_id)
    span.set_attribute("a2a.executor", executor_name)
