"use client";
import React, { useMemo } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  SimpleImageAttachmentAdapter,
  SimpleTextAttachmentAdapter,
  CompositeAttachmentAdapter,
  type ChatModelRunOptions,
  type ChatModelRunResult,
} from "@assistant-ui/react";

// Runtime provider using POST /api/chat with rich A2A content rendering.
// Streams SSE frames: message-start, message-delta, file-part, status-update,
// artifact-update, message-complete, error, done.

interface A2ARuntimeProviderProps {
  children: React.ReactNode;
  agentName: string | null;
  token: string;
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

export const A2ARuntimeProvider: React.FC<A2ARuntimeProviderProps> = ({ children, agentName, token }) => {
  const attachmentAdapter = useMemo(
    () =>
      new CompositeAttachmentAdapter([
        new SimpleImageAttachmentAdapter(),
        new SimpleTextAttachmentAdapter(),
      ]),
    [],
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

      const base = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8100";
      const resp = await fetch(`${base}/api/chat?token=${encodeURIComponent(token)}`, {
        method: "POST",
        headers: {
          Accept: "text/event-stream",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages, agent_name: agentName }),
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

      // Progressive content accumulation
      let accumulatedText = "";
      let lastStatus = "";
      const fileParts: ContentPart[] = [];
      const sourceParts: ContentPart[] = [];

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
              const content = data.content as ContentPart[] | undefined;
              if (content && Array.isArray(content) && content.length > 0) {
                yield { content } as unknown as ChatModelRunResult;
                return;
              }
              break;
            }
            case "error": {
              const err = (data.error as string) || "stream error";
              accumulatedText += `\n[error: ${err}]`;
              updated = true;
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
      // Final fallback if nothing was yielded via message-complete
      const finalContent = buildContent();
      if (finalContent.length === 1 && (finalContent[0] as { text?: string }).text === "") {
        yield {
          content: [{ type: "text" as const, text: "[empty response]" }],
        } as unknown as ChatModelRunResult;
      }
    },
  }, {
    adapters: {
      attachments: attachmentAdapter,
    },
  });

  return <AssistantRuntimeProvider runtime={runtime}>{children}</AssistantRuntimeProvider>;
};
