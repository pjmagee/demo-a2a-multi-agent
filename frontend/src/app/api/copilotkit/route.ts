import { CopilotRuntime, EmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";

const remoteEndpoint =
  process.env.COPILOTKIT_REMOTE_ENDPOINT ?? "http://localhost:8100/copilotkit_remote";
const remoteAuthHeader = process.env.COPILOTKIT_REMOTE_TOKEN;

const runtime = new CopilotRuntime({
  remoteEndpoints: [
    {
      url: remoteEndpoint,
      onBeforeRequest: () => ({
        headers: remoteAuthHeader
          ? {
              Authorization: `Bearer ${remoteAuthHeader}`,
            }
          : undefined,
      }),
    },
  ],
});

const serviceAdapter = new EmptyAdapter();

const { POST, OPTIONS } = copilotRuntimeNextJSAppRouterEndpoint({
  runtime,
  serviceAdapter,
  endpoint: "/api/copilotkit",
});

export { POST, OPTIONS };
