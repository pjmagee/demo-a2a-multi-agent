/**
 * A2A protocol types for tool-call events and enhanced SSE streaming.
 *
 * These types mirror the metadata conventions from the a2a-ui reference
 * implementation and the BFF SSE protocol.
 */

/** A tool-call event emitted when an agent invokes a tool. */
export interface ToolCallEvent {
  toolCallId: string;
  toolCallName: string;
  arguments?: Record<string, unknown>;
  timestamp?: string;
}

/** A tool-call-result event emitted when a tool returns its result. */
export interface ToolCallResultEvent {
  toolCallId: string;
  toolCallName: string;
  result?: unknown;
  timestamp?: string;
}

/** A tracked tool call that pairs the invocation with its result. */
export interface TrackedToolCall {
  id: string;
  name: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  status: "pending" | "completed";
  startedAt?: string;
  completedAt?: string;
}
