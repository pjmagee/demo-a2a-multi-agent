"use client";
import React, { useRef, useMemo, useCallback, useState } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  SimpleImageAttachmentAdapter,
  SimpleTextAttachmentAdapter,
  CompositeAttachmentAdapter,
  type ChatModelRunOptions,
  type ChatModelRunResult,
} from "@assistant-ui/react";
import type { TrackedToolCall, ToolCallEvent, ToolCallResultEvent } from "../types/a2a";
import { AgentActivityProvider, type AgentActivity } from "../agent-activity";

// Runtime provider using POST /api/chat with rich A2A content rendering.
// Streams SSE frames: message-start, message-delta, file-part, status-update,
// artifact-update, message-complete, error, done.
//
// Tracks A2A context_id per thread so conversation state is maintained across
// messages within the same thread. When switching to a new thread the context_id
// is reset so the backend creates a fresh A2A conversation.

interface A2ARuntimeProviderProps {
  children: React.ReactNode;
  agentName: string | null;
  token: string;
  onTitleSuggestion?: (title: string) => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ContentPart = Record<string, any>;

const boundary = "\n\n";

function parseSSEChunk(
  chunk: string,
): { event: string | null; data: Record<string, unknown> | null } {
  const lines = chunk.split("\n");
  const eventLine = lines.find((l) => l.startsWith("event:")) || null;
  const dataLine = lines.find((l) => l.startsWith("data:")) || null;
  let evt: string | null = null;
  let data: Record<string, unknown> | null = null;
  if (eventLine) evt = eventLine.slice(6).trim();
  if (dataLine) {
    const raw = dataLine.slice(5).trim();
    try {
      data = JSON.parse(raw) as Record<string, unknown>;
    } catch {
      data = { text: raw };
    }
  }
  return { event: evt, data };
}

const STATUS_LABELS: Record<string, string> = {
  submitted: "📋 Submitted",
  working: "⏳ Working",
  "input-required": "✋ Input Required",
  completed: "✅ Completed",
  canceled: "🚫 Canceled",
  failed: "❌ Failed",
  rejected: "🚷 Rejected",
  "auth-required": "🔐 Auth Required",
  unknown: "❓ Unknown",
};

export const A2ARuntimeProvider: React.FC<A2ARuntimeProviderProps> = ({ children, agentName, token, onTitleSuggestion }) => {
  // Map thread key (first message ID) → A2A context_id so we maintain
  // conversation context across messages within the same thread.
  const contextIdMapRef = useRef<Map<string, string>>(new Map());
  // Track which threads have already had a title generated
  const titledThreadsRef = useRef<Set<string>>(new Set());

  // Live activity state exposed to sibling components (e.g. agent sidebar)
  const [activity, setActivity] = useState<AgentActivity>({ isStreaming: false, toolCalls: [] });

  const attachmentAdapter = useMemo(
    () =>
      new CompositeAttachmentAdapter([
        new SimpleImageAttachmentAdapter(),
        new SimpleTextAttachmentAdapter(),
      ]),
    [],
  );

  const stableOnTitleSuggestion = useCallback(
    (title: string) => onTitleSuggestion?.(title),
    [onTitleSuggestion],
  );

  const runtime = useLocalRuntime({
    async *run({ messages, abortSignal }: ChatModelRunOptions): AsyncGenerator<ChatModelRunResult, void> {
      if (!agentName) {
        yield {
          content: [
            {
              type: "text" as const,
              text: "Please select an agent from the right sidebar before continuing.",
            },
          ],
        } as unknown as ChatModelRunResult;
        return;
      }

      // Derive a stable key from the first message to identify the thread.
      // A new thread starts with the first user message; subsequent messages
      // in the same thread share the same first message ID.
      const threadKey = messages[0]?.id ?? null;
      const contextId = threadKey ? (contextIdMapRef.current.get(threadKey) ?? null) : null;

      const base = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8100";
      const resp = await fetch(`${base}/api/chat?token=${encodeURIComponent(token)}`, {
        method: "POST",
        headers: {
          Accept: "text/event-stream",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages, agent_name: agentName, context_id: contextId }),
        signal: abortSignal,
      });

      if (!resp.ok) {
        const errorText = await resp.text().catch(() => "");
        yield {
          content: [
            { type: "text" as const, text: `Request failed: ${errorText || `HTTP ${resp.status}`}` },
          ],
        } as unknown as ChatModelRunResult;
        return;
      }
      if (!resp.body) {
        yield {
          content: [{ type: "text" as const, text: "Stream unavailable" }],
        } as unknown as ChatModelRunResult;
        return;
      }

      // Signal streaming start
      setActivity({ isStreaming: true, toolCalls: [] });

      // Progressive content accumulation
      let accumulatedText = "";
      let lastStatus = "";
      let responseContextId: string | null = contextId;
      const fileParts: ContentPart[] = [];
      const sourceParts: ContentPart[] = [];
      const toolCalls: TrackedToolCall[] = [];

      function buildContent(): ContentPart[] {
        const parts: ContentPart[] = [];
        // Show status as text when no content has arrived yet
        if (lastStatus && !accumulatedText && fileParts.length === 0) {
          parts.push({ type: "text" as const, text: lastStatus });
        }
        if (accumulatedText) {
          parts.push({ type: "text" as const, text: accumulatedText });
        }
        parts.push(...fileParts, ...sourceParts);
        // Append individual tool-call parts (standard @assistant-ui/react type)
        for (const tc of toolCalls) {
          parts.push({
            type: "tool-call" as const,
            toolCallId: tc.id,
            toolName: tc.name,
            args: tc.arguments ?? {},
            result: tc.result,
          });
        }
        return parts.length > 0 ? parts : [{ type: "text" as const, text: "" }];
      }

      const reader = resp.body.getReader();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += new TextDecoder().decode(value);
        let idx: number;
        let updated = false;
        while ((idx = buffer.indexOf(boundary)) >= 0) {
          const rawChunk = buffer.slice(0, idx).trim();
          buffer = buffer.slice(idx + boundary.length);
          if (!rawChunk) continue;
          const { event, data } = parseSSEChunk(rawChunk);
          if (!event || !data) continue;

          switch (event) {
            case "message-start": {
              // Capture context_id from the agent's initial frame
              const ctx = data.context_id as string | undefined;
              if (ctx) responseContextId = ctx;
              break;
            }
            case "message-delta": {
              const deltaText = (data.delta as Record<string, unknown> | undefined)?.text;
              if (typeof deltaText === "string") {
                accumulatedText += deltaText;
                lastStatus = "";
                updated = true;
              }
              break;
            }
            case "status-update": {
              const state = data.state as string;
              lastStatus = STATUS_LABELS[state] || `⏳ ${state}`;
              updated = true;
              break;
            }
            case "file-part": {
              if (data.type === "file") {
                fileParts.push({
                  type: "file" as const,
                  data: data.data as string,
                  mimeType: (data.mimeType as string) || "application/octet-stream",
                  filename: data.name as string | undefined,
                });
                updated = true;
              } else if (data.type === "file_uri") {
                sourceParts.push({
                  type: "source" as const,
                  sourceType: "url",
                  id: (data.name as string) || (data.uri as string),
                  url: data.uri as string,
                  title: data.name as string | undefined,
                });
                updated = true;
              }
              break;
            }
            case "message-complete": {
              // Use server's authoritative content if available
              const ctx = data.context_id as string | undefined;
              if (ctx) responseContextId = ctx;
              const content = data.content as ContentPart[] | undefined;
              if (content && Array.isArray(content) && content.length > 0) {
                // Merge tool-call parts so they persist in chat history
                const toolCallParts = toolCalls.map((tc) => ({
                  type: "tool-call" as const,
                  toolCallId: tc.id,
                  toolName: tc.name,
                  args: tc.arguments ?? {},
                  result: tc.result,
                }));
                const merged = [...toolCallParts, ...fileParts, ...content];
                // Persist context_id for this thread before returning
                if (threadKey && responseContextId) {
                  contextIdMapRef.current.set(threadKey, responseContextId);
                }
                setActivity({ isStreaming: false, toolCalls: [] });
                yield { content: merged } as unknown as ChatModelRunResult;
                // Trigger title generation for first exchange
                if (threadKey && !titledThreadsRef.current.has(threadKey)) {
                  titledThreadsRef.current.add(threadKey);
                  _requestTitleSuggestion(base, token, [...messages], content, stableOnTitleSuggestion);
                }
                return;
              }
              break;
            }
            case "artifact-update": {
              // Artifact with inline text content → offer as downloadable file
              const artifactContent = data.content as string | undefined;
              if (artifactContent) {
                const artifactName = (data.name as string) || "artifact";
                const artifactMime = (data.mimeType as string) || "text/plain";
                // Derive a filename from the artifact name
                const ext = artifactMime === "text/markdown" ? ".md" : ".txt";
                const safeName = artifactName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+$/, "");
                const filename = `${safeName}${ext}`;
                // Encode text as base64 for the file content part
                const base64 = btoa(unescape(encodeURIComponent(artifactContent)));
                fileParts.push({
                  type: "file" as const,
                  data: base64,
                  mimeType: artifactMime,
                  filename,
                });
                updated = true;
              }
              break;
            }
            case "done": {
              const ctx = data.context_id as string | undefined;
              if (ctx) responseContextId = ctx;
              break;
            }
            case "error": {
              const err = (data.error as string) || "stream error";
              accumulatedText += `\n[error: ${err}]`;
              updated = true;
              break;
            }
            case "tool-call": {
              const tc = data as unknown as ToolCallEvent;
              toolCalls.push({
                id: tc.toolCallId,
                name: tc.toolCallName,
                arguments: tc.arguments,
                status: "pending",
                startedAt: tc.timestamp,
              });
              setActivity({ isStreaming: true, toolCalls: [...toolCalls] });
              updated = true;
              break;
            }
            case "tool-call-result": {
              const tr = data as unknown as ToolCallResultEvent;
              const existing = toolCalls.find((t) => t.id === tr.toolCallId);
              if (existing) {
                existing.result = tr.result;
                existing.status = "completed";
                existing.completedAt = tr.timestamp;
              } else {
                toolCalls.push({
                  id: tr.toolCallId,
                  name: tr.toolCallName,
                  result: tr.result,
                  status: "completed",
                  completedAt: tr.timestamp,
                });
              }
              setActivity({ isStreaming: true, toolCalls: [...toolCalls] });
              updated = true;
              break;
            }
            case "data-part": {
              // Data parts from non-tool-call DataPart; ignore for now
              break;
            }
            default:
              break;
          }
        }
        if (updated) {
          yield { content: buildContent() } as unknown as ChatModelRunResult;
        }
      }
      // Persist context_id learned during this exchange
      if (threadKey && responseContextId) {
        contextIdMapRef.current.set(threadKey, responseContextId);
      }
      // Final fallback if nothing was yielded via message-complete
      const finalContent = buildContent();
      if (finalContent.length === 1 && (finalContent[0] as { text?: string }).text === "") {
        yield {
          content: [{ type: "text" as const, text: "[empty response]" }],
        } as unknown as ChatModelRunResult;
      }
      // Signal streaming end
      setActivity({ isStreaming: false, toolCalls: [] });
      // Trigger title generation for the first exchange in this thread
      if (threadKey && !titledThreadsRef.current.has(threadKey) && accumulatedText) {
        titledThreadsRef.current.add(threadKey);
        _requestTitleSuggestion(base, token, [...messages], finalContent, stableOnTitleSuggestion);
      }
    },
  }, {
    adapters: {
      attachments: attachmentAdapter,
    },
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <AgentActivityProvider value={activity}>
        {children}
      </AgentActivityProvider>
    </AssistantRuntimeProvider>
  );
};

/**
 * Fire-and-forget: request a short title for the conversation from the backend
 * summarise agent and deliver it via callback. Non-critical – failures are
 * silently swallowed so they never interrupt the chat flow.
 */
function _requestTitleSuggestion(
  base: string,
  token: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  messages: any[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  assistantContent: any[],
  callback: (title: string) => void,
): void {
  // Build a lightweight summary payload
  const summaryMessages = [
    ...messages.map((m) => ({
      role: m.role as string,
      content:
        typeof m.content === "string"
          ? m.content
          : Array.isArray(m.content)
            ? m.content
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                .filter((p: any) => p.type === "text")
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                .map((p: any) => p.text)
                .join(" ")
            : "",
    })),
    {
      role: "assistant",
      content: assistantContent
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .filter((p: any) => p.type === "text")
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((p: any) => p.text)
        .join(" "),
    },
  ];

  fetch(`${base}/api/chat/summarise?token=${encodeURIComponent(token)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: summaryMessages }),
  })
    .then((r) => (r.ok ? r.json() : null))
    .then((data) => {
      if (data?.title) callback(data.title);
    })
    .catch(() => {
      // Non-critical – silently ignore
    });
}
