"use client";

// Using custom A2ARuntimeProvider instead of assistant-ui default runtime wiring.
import { Thread } from "@/components/assistant-ui/thread";
import { AgentPills } from "../components/AgentPills";
import { A2ARuntimeProvider } from "../lib/assistant/runtime";
import { ThreadTitleManager } from "../components/ThreadTitleManager";
import React, { useRef, useState } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Users } from "lucide-react";
import { ThreadListSidebar } from "@/components/assistant-ui/threadlist-sidebar";
import { Separator } from "@/components/ui/separator";

export const Assistant = () => {
  const [token] = useState("test-token");
  const [agentName, setAgentName] = useState<string | null>(null);
  const [showAgents, setShowAgents] = useState<boolean>(true);

  // Ref that ThreadTitleManager populates with its rename handler.
  // A2ARuntimeProvider calls through this ref when a title suggestion arrives.
  const titleHandlerRef = useRef<((title: string) => void) | null>(null);

  return (
    <A2ARuntimeProvider
      agentName={agentName}
      token={token}
      onTitleSuggestion={(title) => titleHandlerRef.current?.(title)}
    >
      <ThreadTitleManager onTitleSuggestion={titleHandlerRef} />
      <SidebarProvider>
        <div className="flex h-dvh w-full overflow-hidden">
          {/* Left thread sidebar */}
          <ThreadListSidebar />
          {/* Middle + Right container */}
          <div className="flex flex-row flex-1 min-w-0">
            {/* Middle chat area */}
            <div className="flex flex-col flex-1 min-w-0">
              <div className="h-12 flex items-center px-3 border-b justify-between">
                <div className="flex items-center gap-2">
                  <SidebarTrigger />
                  <Separator orientation="vertical" className="h-4" />
                  <span className="text-sm font-medium">Chat</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    aria-label={showAgents ? "Hide agents" : "Show agents"}
                    onClick={() => setShowAgents(s => !s)}
                    className="p-2 rounded border border-gray-300 hover:bg-gray-100 flex items-center"
                    title={showAgents ? "Hide agents" : "Show agents"}
                  >
                    <Users className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-hidden">
                <Thread />
              </div>
            </div>
            {showAgents && (
              <aside className="hidden md:flex flex-col h-full w-64 shrink-0 bg-sidebar text-sidebar-foreground border-l">
                <div className="aui-sidebar-header mb-2 border-b p-2 flex items-center justify-between">
                  <span className="text-sm font-semibold">Agents</span>
                  {agentName && (
                    <span className="text-[11px] text-sidebar-foreground/70 truncate max-w-[8rem]" title={agentName}>{agentName}</span>
                  )}
                </div>
                <div className="flex-1 overflow-auto px-2 pb-4">
                  <AgentPills
                    token={token}
                    chosenAgent={agentName}
                    onChoose={setAgentName}
                  />
                </div>
              </aside>
            )}
          </div>
        </div>
      </SidebarProvider>
    </A2ARuntimeProvider>
  );
};
