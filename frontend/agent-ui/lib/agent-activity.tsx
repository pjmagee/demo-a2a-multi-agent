"use client";

import { createContext, useContext } from "react";
import type { TrackedToolCall } from "./types/a2a";

/** Live activity state published by the runtime during streaming. */
export interface AgentActivity {
  /** Whether the runtime is currently streaming a response. */
  isStreaming: boolean;
  /** Tool calls tracked during the current streaming response. */
  toolCalls: TrackedToolCall[];
}

const defaultActivity: AgentActivity = { isStreaming: false, toolCalls: [] };

const AgentActivityContext = createContext<AgentActivity>(defaultActivity);

export const AgentActivityProvider = AgentActivityContext.Provider;

/** Read the current agent activity (streaming state + tracked tool calls). */
export function useAgentActivity(): AgentActivity {
  return useContext(AgentActivityContext);
}
