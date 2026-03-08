"use client";

import { useCallback, useRef } from "react";
import { useAssistantRuntime } from "@assistant-ui/react";

/**
 * Invisible component that listens for title suggestions from the runtime
 * and renames the current thread in the thread list.
 *
 * Must be placed inside <AssistantRuntimeProvider>.
 */
export function ThreadTitleManager({
  onTitleSuggestion,
}: {
  onTitleSuggestion: React.MutableRefObject<((title: string) => void) | null>;
}) {
  const runtime = useAssistantRuntime();
  const renamedThreadsRef = useRef<Set<string>>(new Set());

  // Stable callback that renames the current thread
  const handleTitle = useCallback(
    (title: string) => {
      try {
        const mainThreadId = runtime.threads.getState().mainThreadId;
        if (mainThreadId && !renamedThreadsRef.current.has(mainThreadId)) {
          renamedThreadsRef.current.add(mainThreadId);
          const item = runtime.threads.getItemById(mainThreadId);
          item.rename(title);
        }
      } catch {
        // Thread management is non-critical; swallow errors
      }
    },
    [runtime],
  );

  // Expose the handler via the ref so the parent can wire it into A2ARuntimeProvider
  onTitleSuggestion.current = handleTitle;

  return null;
}
