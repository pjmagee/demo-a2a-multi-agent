"use client";

import { useState } from "react";
import { ChevronDownIcon, ChevronRightIcon, LoaderIcon, CheckCircle2Icon, WrenchIcon } from "lucide-react";
import type { TrackedToolCall } from "@/lib/types/a2a";

interface ToolCallAccordionProps {
  toolCalls: TrackedToolCall[];
}

export function ToolCallAccordion({ toolCalls }: ToolCallAccordionProps) {
  if (toolCalls.length === 0) return null;

  return (
    <div className="my-2 space-y-1">
      {toolCalls.map((tc) => (
        <ToolCallItem key={tc.id} toolCall={tc} />
      ))}
    </div>
  );
}

function ToolCallItem({ toolCall }: { toolCall: TrackedToolCall }) {
  const [expanded, setExpanded] = useState(false);
  const isPending = toolCall.status === "pending";

  return (
    <div className="rounded-lg border border-border bg-muted/30 overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted/50 transition-colors"
      >
        {isPending ? (
          <LoaderIcon className="size-3.5 animate-spin text-muted-foreground" />
        ) : (
          <CheckCircle2Icon className="size-3.5 text-green-500" />
        )}
        <WrenchIcon className="size-3.5 text-muted-foreground" />
        <span className="font-medium text-foreground">{toolCall.name}</span>
        <span className="ml-auto text-muted-foreground">
          {expanded ? (
            <ChevronDownIcon className="size-4" />
          ) : (
            <ChevronRightIcon className="size-4" />
          )}
        </span>
      </button>
      {expanded && (
        <div className="border-t border-border px-3 py-2 space-y-2">
          {toolCall.arguments && Object.keys(toolCall.arguments).length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Arguments</p>
              <pre className="text-xs bg-muted rounded p-2 overflow-x-auto whitespace-pre-wrap break-all">
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
          )}
          {toolCall.result !== undefined && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Result</p>
              <pre className="text-xs bg-muted rounded p-2 overflow-x-auto whitespace-pre-wrap break-all max-h-64 overflow-y-auto">
                {typeof toolCall.result === "string"
                  ? toolCall.result
                  : JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}
          {isPending && toolCall.result === undefined && (
            <p className="text-xs text-muted-foreground italic">Waiting for result…</p>
          )}
        </div>
      )}
    </div>
  );
}
