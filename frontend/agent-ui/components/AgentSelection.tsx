"use client";
import React, { useEffect, useState } from "react";

interface SkillDefinition {
  name: string;
  description?: string;
  [key: string]: unknown;
}

interface AgentCard {
  name: string;
  description?: string;
  tags?: string[];
  skills?: Record<string, SkillDefinition>;
}

interface AgentSelectionProps {
  token: string;
  backendUrl?: string;
  onChoose: (agentName: string) => void;
  chosenAgent: string | null;
}

export const AgentSelection: React.FC<AgentSelectionProps> = ({
  token,
  backendUrl,
  onChoose,
  chosenAgent,
}) => {
  const base = backendUrl || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8100";
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<AgentCard | null>(null);

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
        const msg = typeof e === "object" && e && "message" in e ? (e as { message?: unknown }).message : String(e);
        setError(typeof msg === "string" ? msg : "load error");
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
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Agents</h2>
        {loading && <span className="text-xs">Loading...</span>}
      </div>
      {error && <div className="text-xs text-red-600">Error: {error}</div>}
  <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {agents.map((a) => {
          const isChosen = a.name === chosenAgent;
          return (
            <button
              key={a.name}
              type="button"
              onClick={() => setDetail(a)}
              className={`text-left border rounded p-2 hover:border-blue-500 transition focus:outline-none focus:ring-2 focus:ring-blue-400 ${isChosen ? "border-blue-600" : "border-gray-300"}`}
            >
              <div className="font-medium text-sm truncate" title={a.name}>{a.name}</div>
              <div className="text-[11px] text-gray-600 line-clamp-3 mt-1">{a.description || "No description"}</div>
              {isChosen && <div className="mt-1 text-[10px] text-blue-600">Selected</div>}
            </button>
          );
        })}
        {agents.length === 0 && !loading && <div className="text-xs text-gray-500">No agents found.</div>}
      </div>
      {detail && (
        <AgentDetailModal
          agent={detail}
          onClose={() => setDetail(null)}
          onChoose={(name) => {
            onChoose(name);
            setDetail(null);
          }}
          chosen={chosenAgent}
        />
      )}
    </div>
  );
};

interface AgentDetailModalProps {
  agent: AgentCard;
  onClose: () => void;
  onChoose: (agentName: string) => void;
  chosen: string | null;
}

const AgentDetailModal: React.FC<AgentDetailModalProps> = ({ agent, onClose, onChoose, chosen }) => {
  const skills = agent.skills ? Object.values(agent.skills) : [];
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-neutral-900 rounded shadow-lg w-full max-w-lg p-4 space-y-4">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold">{agent.name}</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 text-sm"
            aria-label="Close agent details"
          >
            ✕
          </button>
        </div>
        <p className="text-sm whitespace-pre-wrap">{agent.description || "No description provided."}</p>
        {agent.tags && agent.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {agent.tags.map((t) => (
              <span key={t} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-[11px] border border-blue-200">
                {t}
              </span>
            ))}
          </div>
        )}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Skills</h4>
          {skills.length === 0 && <div className="text-xs text-gray-500">No skills listed.</div>}
          {skills.map((s) => (
            <div key={s.name} className="border rounded p-2">
              <div className="text-xs font-semibold">{s.name}</div>
              {s.description && <div className="text-[11px] text-gray-600 mt-1">{s.description}</div>}
            </div>
          ))}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onChoose(agent.name)}
            className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            disabled={chosen === agent.name}
          >
            {chosen === agent.name ? "Chosen" : "Choose Agent"}
          </button>
        </div>
      </div>
    </div>
  );
};
