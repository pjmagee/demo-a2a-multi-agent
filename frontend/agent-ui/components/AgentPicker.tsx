"use client";
import React, { useEffect, useState } from "react";

type SkillDefinition = {
  name: string;
  description?: string;
  [key: string]: unknown;
};

interface AgentCard {
  name: string;
  description?: string;
  skills?: Record<string, SkillDefinition> | undefined;
}

interface AgentPickerProps {
  token: string;
  onSelect: (agentName: string | null) => void;
  selected: string | null;
  backendUrl?: string;
}

export const AgentPicker: React.FC<AgentPickerProps> = ({
  token,
  onSelect,
  selected,
  backendUrl,
}) => {
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const base = backendUrl || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8100";

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const resp = await fetch(`${base}/api/agents?token=${encodeURIComponent(token)}`);
        if (!resp.ok) throw new Error(`status ${resp.status}`);
        const json = await resp.json();
        if (!cancelled) setAgents(Array.isArray(json) ? json : []);
      } catch (e: unknown) {
    let msg: string;
    if (typeof e === "object" && e !== null && "message" in e) {
      const maybeMsg = (e as { message?: unknown }).message;
      msg = typeof maybeMsg === "string" ? maybeMsg : String(maybeMsg);
    } else {
      msg = String(e);
    }
        if (!cancelled) setError(msg || "load error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [base, token]);

  return (
    <div className="agent-picker">
      <label className="block text-sm font-medium mb-1">Select Agent</label>
      {loading && <div className="text-xs">Loading agents...</div>}
      {error && <div className="text-xs text-red-600">Error: {error}</div>}
      <select
        className="border rounded px-2 py-1 text-sm w-full"
        value={selected || ""}
        onChange={(e) => onSelect(e.target.value || null)}
        aria-label="Agent selection"
      >
        <option value="">-- choose an agent --</option>
        {agents.map((a) => (
          <option key={a.name} value={a.name}>
            {a.name}
          </option>
        ))}
      </select>
      {selected && (
        <div className="mt-2 text-xs text-gray-600">
          {(agents.find((a) => a.name === selected)?.description || "No description")}
        </div>
      )}
    </div>
  );
};
