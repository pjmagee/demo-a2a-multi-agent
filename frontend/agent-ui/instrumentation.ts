/**
 * OpenTelemetry instrumentation for Next.js application.
 *
 * This file is automatically loaded by Next.js 15+ to configure OpenTelemetry
 * for the Aspire dashboard. It reads the OTLP endpoint from the environment
 * variable automatically injected by Aspire orchestration.
 *
 * @see https://nextjs.org/docs/app/building-your-application/optimizing/instrumentation
 */

export async function register() {
  // Only instrument on the Node.js runtime (server-side)
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { NodeSDK } = await import("@opentelemetry/sdk-node");
    const { getNodeAutoInstrumentations } = await import(
      "@opentelemetry/auto-instrumentations-node"
    );
    const { OTLPTraceExporter } = await import(
      "@opentelemetry/exporter-trace-otlp-grpc"
    );
    const { OTLPMetricExporter } = await import(
      "@opentelemetry/exporter-metrics-otlp-grpc"
    );
    const { PeriodicExportingMetricReader } = await import(
      "@opentelemetry/sdk-metrics"
    );

    // Aspire automatically sets OTEL_EXPORTER_OTLP_ENDPOINT
    const otlpEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;

    if (otlpEndpoint) {
      const sdk = new NodeSDK({
        serviceName: "frontend",
        traceExporter: new OTLPTraceExporter({
          url: otlpEndpoint,
        }),
        metricReader: new PeriodicExportingMetricReader({
          exporter: new OTLPMetricExporter({
            url: otlpEndpoint,
          }),
          exportIntervalMillis: 5000,
        }),
        instrumentations: [getNodeAutoInstrumentations()],
      });

      sdk.start();
      console.log("✅ OpenTelemetry initialized for frontend");
    } else {
      console.warn(
        "OTEL_EXPORTER_OTLP_ENDPOINT not set - telemetry disabled. " +
          "This is expected when running outside Aspire orchestration."
      );
    }
  }
}
