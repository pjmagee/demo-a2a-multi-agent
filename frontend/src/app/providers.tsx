"use client";

import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";

const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL ?? "/api/copilotkit";
const publicApiKey = process.env.NEXT_PUBLIC_COPILOTKIT_PUBLIC_API_KEY;

export function Providers({ children }: { children: ReactNode }) {
  return (
    <CopilotKit runtimeUrl={runtimeUrl} publicApiKey={publicApiKey}>
      {children}
    </CopilotKit>
  );
}
