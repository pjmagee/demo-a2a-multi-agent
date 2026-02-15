"use client";
import React, { useState } from "react";
import { AgentPicker } from "../../components/AgentPicker";
import { A2ARuntimeProvider } from "../../lib/assistant/runtime";
import dynamic from "next/dynamic";

// Dynamically import assistant-ui Chat component (placeholder - adjust to actual component name)
const ChatUI = dynamic(() => import("../../components/ChatUI").catch(() => ({ default: () => <div>Chat component missing</div> })), { ssr: false });

export default function ChatPage() {
  const [agentName, setAgentName] = useState<string | null>(null);
  const [token, setToken] = useState<string>("");

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Multi-Agent Chat</h1>
      <div className="flex flex-col gap-4 md:flex-row">
        <div className="md:w-1/3 space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium">Auth Token</label>
            <input
              type="text"
              className="border rounded px-2 py-1 text-sm w-full"
              placeholder="Paste token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </div>
          <AgentPicker token={token} selected={agentName} onSelect={setAgentName} />
        </div>
        <div className="md:w-2/3 border rounded p-3 min-h-[300px]">
          {agentName ? (
            <A2ARuntimeProvider agentName={agentName} token={token}>
              <ChatUI />
            </A2ARuntimeProvider>
          ) : (
            <div className="text-sm text-gray-600">Select an agent to begin.</div>
          )}
        </div>
      </div>
    </div>
  );
}
