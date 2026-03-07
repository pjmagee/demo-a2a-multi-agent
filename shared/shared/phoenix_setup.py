"""Integrated Phoenix + Aspire observability setup for A2A agents.

Provides a single ``setup_phoenix_tracing(service_name)`` function that:

- Instruments the OpenAI Agents SDK, LangGraph/LangChain, and raw OpenAI
  client via the installed openinference auto-instrumentors.
- Exports LLM traces to Phoenix (reads ``PHOENIX_COLLECTOR_ENDPOINT``).
- Dual-exports *all* spans to the Aspire dashboard
  (reads ``OTEL_EXPORTER_OTLP_ENDPOINT``, injected automatically by Aspire).
- Falls back to Aspire-only tracing when Phoenix is unavailable.
- Configures Aspire metrics and structured logging over OTLP gRPC.
- Auto-instruments FastAPI and httpx for HTTP observability.

Usage::

    # app.py – call once, as early as possible (after load_dotenv if present)
    from shared.phoenix_setup import setup_phoenix_tracing
    setup_phoenix_tracing("my-agent")

Environment variables:
    PHOENIX_COLLECTOR_ENDPOINT  Phoenix base URL (e.g. ``http://phoenix:6006``)
                                Set automatically by Aspire via AppHost.cs.
    PHOENIX_PROJECT_NAME        Phoenix project name (default: ``demo-a2a-multi-agent``)
    OTEL_EXPORTER_OTLP_ENDPOINT Aspire OTLP gRPC endpoint (injected by Aspire).
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_initialized = False


class _SessionIdBaggageSpanProcessor:
    """Copy ``session.id`` from OTel baggage onto every new span.

    Executors attach ``session.id`` as OTel baggage via ``a2a_session``.
    This processor reads it on ``on_start`` so *all* child spans – including
    those created by openinference instrumentors inside the SDK – automatically
    carry ``session.id`` without manual plumbing.
    """

    def on_start(self, span, parent_context=None):  # type: ignore[override]
        from opentelemetry import baggage
        from opentelemetry.context import get_current

        ctx = parent_context if parent_context is not None else get_current()
        session_id = baggage.get_baggage("session.id", ctx)
        if session_id:
            span.set_attribute("session.id", session_id)

    def on_end(self, span) -> None:  # type: ignore[override]
        pass

    def _on_ending(self, span) -> None:
        """Required by the OTel SDK internally (called before ``on_end``)."""

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True


def setup_phoenix_tracing(service_name: str) -> None:
    """Configure Phoenix LLM tracing and Aspire telemetry for *service_name*.

    Safe to call multiple times – subsequent calls are no-ops.

    Args:
        service_name: Logical service name used for Aspire resource attributes
                      and Phoenix project grouping (e.g. ``"firebrigade-agent"``).
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    project_name = os.environ.get("PHOENIX_PROJECT_NAME", "demo-a2a-multi-agent")
    phoenix_endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT")
    aspire_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    # Ensure service.name is set for both Phoenix and Aspire dashboard labelling.
    # register() reads OTEL_SERVICE_NAME; Aspire also uses it to identify services.
    os.environ.setdefault("OTEL_SERVICE_NAME", service_name)

    # ── 1. Phoenix LLM Tracing ──────────────────────────────────────────────
    # phoenix.otel.register() reads PHOENIX_COLLECTOR_ENDPOINT and constructs
    # the OTLP HTTP URL (appends /v1/traces).  auto_instrument=True activates
    # every installed openinference instrumentor:
    #   openinference-instrumentation-openai-agents  → OpenAI Agents SDK
    #   openinference-instrumentation-openai         → raw openai client
    #   openinference-instrumentation-langchain      → LangChain + LangGraph
    tracer_provider = None
    if phoenix_endpoint:
        try:
            from phoenix.otel import register

            tracer_provider = register(
                project_name=project_name,
                auto_instrument=True,
                batch=True,
            )
            logger.info(
                "Phoenix tracing configured (project=%s, endpoint=%s)",
                project_name,
                phoenix_endpoint,
            )
        except ImportError:
            logger.warning(
                "arize-phoenix-otel not installed – Phoenix tracing disabled. "
                "Add arize-phoenix-otel to shared/pyproject.toml."
            )
        except Exception as exc:
            logger.warning("Phoenix tracing setup failed: %s", exc)
    else:
        logger.warning("PHOENIX_COLLECTOR_ENDPOINT not set – Phoenix tracing disabled.")

    # ── 2. Aspire span export (dual-export onto the same provider) ──────────
    if aspire_endpoint and tracer_provider is not None:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            # replace_default_processor=False preserves Phoenix's exporter instead of replacing it
            tracer_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=aspire_endpoint)),
                replace_default_processor=False,
            )
            logger.info("Aspire span export added (endpoint=%s)", aspire_endpoint)
        except Exception as exc:
            logger.warning("Could not add Aspire span exporter: %s", exc)

    # ── 3. Fallback: Aspire-only tracing when Phoenix is unavailable ─────────
    if tracer_provider is None and aspire_endpoint:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({"service.name": service_name})
            tracer_provider = TracerProvider(resource=resource)
            tracer_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=aspire_endpoint))
            )
            trace.set_tracer_provider(tracer_provider)
            logger.info("Aspire-only tracing configured (endpoint=%s)", aspire_endpoint)
        except Exception as exc:
            logger.warning("Aspire fallback tracing setup failed: %s", exc)

    # ── 3.5. Session-ID baggage propagation ──────────────────────────────────
    if tracer_provider is not None:
        try:
            tracer_provider.add_span_processor(
                _SessionIdBaggageSpanProcessor(),
                replace_default_processor=False,
            )
        except TypeError:
            # Plain OTel TracerProvider doesn't accept replace_default_processor
            tracer_provider.add_span_processor(_SessionIdBaggageSpanProcessor())  # type: ignore[arg-type]
        except Exception as exc:
            logger.warning("Session-ID baggage processor setup failed: %s", exc)

    # ── 4. Aspire Metrics ────────────────────────────────────────────────────
    if aspire_endpoint:
        try:
            from opentelemetry import metrics
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": service_name})
            metrics.set_meter_provider(
                MeterProvider(
                    resource=resource,
                    metric_readers=[
                        PeriodicExportingMetricReader(
                            OTLPMetricExporter(endpoint=aspire_endpoint),
                            export_interval_millis=5000,
                        )
                    ],
                )
            )
        except Exception as exc:
            logger.warning("Aspire metrics setup failed: %s", exc)

    # ── 5. Aspire Structured Logging ─────────────────────────────────────────
    if aspire_endpoint:
        try:
            from opentelemetry._logs import set_logger_provider
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
            from opentelemetry.instrumentation.logging import LoggingInstrumentor
            from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": service_name})
            log_provider = LoggerProvider(resource=resource)
            log_provider.add_log_record_processor(
                BatchLogRecordProcessor(OTLPLogExporter(endpoint=aspire_endpoint))
            )
            set_logger_provider(log_provider)
            logging.getLogger().addHandler(
                LoggingHandler(level=logging.NOTSET, logger_provider=log_provider)
            )
            LoggingInstrumentor().instrument(set_logging_format=True)
        except Exception as exc:
            logger.warning("Aspire logging setup failed: %s", exc)

    # ── 6. HTTP auto-instrumentation (FastAPI + httpx) ───────────────────────
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        FastAPIInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
    except Exception as exc:
        logger.debug("HTTP auto-instrumentation: %s", exc)

    logger.info("Telemetry setup complete for service=%s", service_name)
