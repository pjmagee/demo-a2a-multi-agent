"""OpenTelemetry configuration for Aspire dashboard integration.

This module configures OpenTelemetry tracing, metrics, and logging to work
seamlessly with the Aspire dashboard. It automatically reads the OTLP endpoint
from the environment variable injected by Aspire orchestration.
"""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def configure_telemetry(service_name: str) -> None:
    """Configure OpenTelemetry for Aspire dashboard integration.

    This function sets up tracing, metrics, and logging to send telemetry
    to the Aspire dashboard. It reads the OTLP endpoint from the
    OTEL_EXPORTER_OTLP_ENDPOINT environment variable, which is automatically
    set by Aspire orchestration.

    Args:
        service_name: The name of the service for telemetry identification.
                     Should match the service name in AppHost.cs.

    Note:
        If OTEL_EXPORTER_OTLP_ENDPOINT is not set, telemetry will be disabled
        and a warning will be logged. This is expected when running services
        outside of Aspire orchestration.
    """
    # Aspire automatically sets OTEL_EXPORTER_OTLP_ENDPOINT
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if not otlp_endpoint:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT not set - telemetry disabled. "
            "This is expected when running outside Aspire orchestration."
        )
        return

    logger.info(f"Configuring OpenTelemetry for {service_name} -> {otlp_endpoint}")

    # Create resource with service identification
    resource = Resource.create({"service.name": service_name})

    # Configure Tracing
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(trace_provider)

    # Configure Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint),
        export_interval_millis=5000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Configure Logging
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=otlp_endpoint)))
    set_logger_provider(logger_provider)

    # Add logging handler for structured logs
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)

    # Auto-instrument FastAPI and httpx
    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=True)

    logger.info(f"✅ OpenTelemetry configured for {service_name}")
