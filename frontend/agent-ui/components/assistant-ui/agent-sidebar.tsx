"use client";

import React, { useState } from "react";
import { AgentPills } from "../../components/AgentPills";
import { PanelLeftIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentSidebarProps {
  token: string;
  agentName: string | null;
  onSelect: (name: string) => void;
  className?: string;
}

// A lightweight independent sidebar (right side) mimicking the visual style
// of the left ThreadListSidebar but with its own collapsed state.
// We do not reuse SidebarProvider here to avoid coupling both sidebars.
export const AgentSidebar: React.FC<AgentSidebarProps> = ({
  token,
  agentName,
  onSelect,
  className,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div
      data-side="right"
      data-state={collapsed ? "collapsed" : "expanded"}
      className={cn(
        "relative hidden md:block h-full transition-[width] duration-200 ease-linear",
        collapsed ? "w-0" : "w-64",
        "bg-sidebar text-sidebar-foreground border-l",
        className,
      )}
    >
      {/* Removed narrow rail button to satisfy accessibility lint; single floating toggle retained */}
      <div
        className={cn(
          "absolute top-2 -left-10 hidden md:flex",
          collapsed && "left-0",
        )}
      >
        <button
          type="button"
          aria-label={collapsed ? "Expand agents sidebar" : "Collapse agents sidebar"}
          title={collapsed ? "Expand agents sidebar" : "Collapse agents sidebar"}
          onClick={() => setCollapsed(c => !c)}
          className={cn(
            "size-8 rounded-lg border bg-sidebar-primary text-sidebar-primary-foreground flex items-center justify-center shadow-sm",
            "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            collapsed && "rotate-180",
          )}
        >
          <PanelLeftIcon className="size-4" />
          <span className="sr-only">{collapsed ? "Expand agents sidebar" : "Collapse agents sidebar"}</span>
        </button>
      </div>
      {/* Inner content container */}
      <div
        className={cn(
          "flex h-full flex-col", // hide content when collapsed via width=0
          collapsed && "pointer-events-none opacity-0",
        )}
      >
        <div className="aui-sidebar-header mb-2 border-b p-2 flex items-center justify-between">
          <span className="text-sm font-semibold">Agents</span>
          {agentName && (
            <span className="text-[11px] text-sidebar-foreground/70 truncate max-w-[8rem]" title={agentName}>
              {agentName}
            </span>
          )}
        </div>
        <div className="flex-1 overflow-auto px-2 pb-4">
          <AgentPills
            token={token}
            chosenAgent={agentName}
            onChoose={onSelect}
          />
        </div>
      </div>
    </div>
  );
};
