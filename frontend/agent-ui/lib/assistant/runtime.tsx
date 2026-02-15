"use client";
import React from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelRunOptions,
  type ChatModelRunResult,
} from "@assistant-ui/react";

// Runtime provider that can speak to either legacy /api/messages/stream (GET)
// or the new /api/chat (POST) Data Stream style endpoint depending on env flag.
// Set NEXT_PUBLIC_USE_CHAT_ENDPOINT=1 to use /api/chat.

interface A2ARuntimeProviderProps {
  children: React.ReactNode;
  agentName: string | null;
  token: string;
}

interface GenericMessagePart { type?: string; kind?: string; text?: string; value?: string }
interface AssistantUIMessage { id?: string; role?: string; content?: GenericMessagePart[] | string }
interface ThreadMessageLike { role?: string; content?: unknown }

const boundary = "\n\n";

function parseSSEChunk(
  chunk: string,
): { event: string | null; data: unknown | null } {
  const lines = chunk.split("\n");
  const eventLine = lines.find((l) => l.startsWith("event:")) || null;
  const dataLine = lines.find((l) => l.startsWith("data:")) || null;
  let evt: string | null = null;
  let data: unknown | null = null;
  if (eventLine) evt = eventLine.slice(6).trim();
  if (dataLine) {
    const raw = dataLine.slice(5).trim();
    try {
      data = JSON.parse(raw);
    } catch {
      data = raw;
    }
  }
  return { event: evt, data };
}

export const A2ARuntimeProvider: React.FC<A2ARuntimeProviderProps> = ({ children, agentName, token }) => {
  const runtime = useLocalRuntime({
    async run({ messages, abortSignal }: ChatModelRunOptions): Promise<ChatModelRunResult> {
      if (!agentName) {
        const lastUser = [...messages].reverse().find((m) => (m as ThreadMessageLike).role === "user") as ThreadMessageLike | undefined;
        const echoed = lastUser && typeof lastUser.content === "string" ? (lastUser.content as string) : "";
        return {
          messages: [
            {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              content: [
                {
                  type: "text",
                  text: `Please select an agent from the right sidebar before continuing.${echoed ? `\n\n(You said: ${echoed})` : ""}`,
                },
              ],
            },
          ],
        } as ChatModelRunResult;
      }

      const base = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8100";
      const useChat = process.env.NEXT_PUBLIC_USE_CHAT_ENDPOINT === "1";
      let resp: Response;
      if (useChat) {
        resp = await fetch(`${base}/api/chat?token=${encodeURIComponent(token)}`, {
          method: "POST",
          headers: {
            Accept: "text/event-stream",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ messages, agent_name: agentName }),
          signal: abortSignal,
        });
      } else {
        const lastUser = [...messages].reverse().find((m) => (m as ThreadMessageLike).role === "user") as ThreadMessageLike | undefined;
        let userText = "";
        if (lastUser) {
          const content = lastUser.content;
          if (typeof content === "string") userText = content;
          else if (Array.isArray(content)) {
            userText = content
              .filter((p: GenericMessagePart) => p.type === "text" && typeof p.text === "string")
              .map((p: GenericMessagePart) => p.text || "")
              .join("");
          }
        }
        const params = new URLSearchParams({ agent_name: agentName, message: userText });
        params.set("token", token);
        resp = await fetch(`${base}/api/messages/stream?${params.toString()}`, {
          signal: abortSignal,
          headers: { Accept: "text/event-stream" },
        });
      }

      if (!resp.ok) {
        const errorText = await resp.text().catch(() => "");
        const info = errorText || `HTTP ${resp.status}`;
        return {
          messages: [
            {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              content: [
                { type: "text", text: `Request failed before streaming started: ${info}` },
              ],
            },
          ],
        } as ChatModelRunResult;
      }
      if (!resp.body) {
        return {
          messages: [
            { id: `assistant-${Date.now()}`, role: "assistant", content: [{ type: "text", text: "Stream unavailable" }] },
          ],
        } as ChatModelRunResult;
      }

      const reader = resp.body.getReader();
      let buffer = "";
      let accumulated = "";
      let finalText = "";
      let completeReceived = false;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += new TextDecoder().decode(value);
        let idx: number;
        while ((idx = buffer.indexOf(boundary)) >= 0) {
          const rawChunk = buffer.slice(0, idx).trim();
          buffer = buffer.slice(idx + boundary.length);
          if (!rawChunk) continue;
          const { event, data } = parseSSEChunk(rawChunk);
          if (!event) continue;
          if (event === "error") {
            const err = (data as { error?: string } | null)?.error || "stream error";
            accumulated += `\n[error: ${err}]`;
          } else if (event === "stream" && !useChat) {
            const d = data as { parts?: GenericMessagePart[]; artifact?: { parts?: GenericMessagePart[] }; status?: { message?: { parts?: GenericMessagePart[] } } } | null;
            const parts: GenericMessagePart[] = (d?.parts || d?.artifact?.parts || d?.status?.message?.parts || []) as GenericMessagePart[];
            accumulated += (Array.isArray(parts)
              ? parts
                  .filter((p: GenericMessagePart) => (p.kind === "text" || p.type === "text") && typeof (p.text ?? p.value) === "string")
                  .map((p: GenericMessagePart) => (p.text || p.value || ""))
                  .join("")
              : "");
          } else if (useChat) {
            if (event === "message-delta") {
              const deltaText = (data as { delta?: { text?: string } } | null)?.delta?.text;
              if (deltaText) accumulated += deltaText;
            } else if (event === "message-complete") {
              completeReceived = true;
              const msg = data as AssistantUIMessage;
              const parts = Array.isArray(msg?.content) ? (msg.content as GenericMessagePart[]) : [];
              finalText = parts
                .filter((p) => p.type === "text" && typeof p.text === "string")
                .map((p) => p.text || "")
                .join("");
            }
          }
        }
      }
      const textOut = completeReceived ? (finalText || accumulated) : (accumulated || finalText);
      return {
        messages: [
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: [ { type: "text", text: textOut || "[empty response]" } ],
          },
        ],
      } as ChatModelRunResult;
    },
  });

  return <AssistantRuntimeProvider runtime={runtime}>{children}</AssistantRuntimeProvider>;
};
