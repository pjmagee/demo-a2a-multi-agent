"use client";
import React, { useEffect, useState, useCallback } from "react";

interface SkillDefinition { name: string; description?: string; [k: string]: unknown }
interface AgentCard { name: string; description?: string; tags?: string[]; skills?: Record<string, SkillDefinition> }

interface AgentPillsProps {
  token: string;
  onChoose: (agentName: string) => void;
  chosenAgent: string | null;
  backendUrl?: string;
}

// Agent list styled similar to thread list items (vertical list, selectable rows)
export const AgentPills: React.FC<AgentPillsProps> = ({ token, onChoose, chosenAgent, backendUrl }) => {
  const base = backendUrl || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8100";
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<AgentCard | null>(null);

  // Auto select first agent after load if none chosen
  useEffect(() => {
    if (agents.length > 0 && !chosenAgent) {
      onChoose(agents[0].name);
    }
  }, [agents, chosenAgent, onChoose]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true); setError(null);
      try {
        const resp = await fetch(`${base}/api/agents?token=${encodeURIComponent(token)}`);
        if (!resp.ok) throw new Error(`status ${resp.status}`);
        const json = await resp.json();
        if (!cancelled) setAgents(Array.isArray(json) ? json : []);
      } catch (e: unknown) {
        const msg = (typeof e === "object" && e && "message" in e) ? String((e as { message?: unknown }).message) : String(e);
        if (!cancelled) setError(msg || "load error");
      } finally { if (!cancelled) setLoading(false); }
    }
    load();
    return () => { cancelled = true; };
  }, [base, token]);

  const handleRowClick = useCallback((agent: AgentCard) => {
    onChoose(agent.name); // direct select without modal
  }, [onChoose]);

  const handleContextMenu = useCallback((e: React.MouseEvent, agent: AgentCard) => {
    e.preventDefault();
    setDetail(agent);
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-semibold">Agents</span>
        {loading && <span className="text-[10px]">…</span>}
      </div>
      {error && <div className="text-[11px] text-red-600 mb-2 px-1">{error}</div>}
      <div className="flex-1 overflow-auto">
        <ul className="space-y-1 pr-1">
          {agents.map(a => {
            const active = a.name === chosenAgent;
            return (
              <li key={a.name}>
                <button
                  type="button"
                  onClick={() => handleRowClick(a)}
                  onContextMenu={(e) => handleContextMenu(e, a)}
                  className={`group w-full text-left px-2 py-2 rounded border flex flex-col gap-1 transition relative ${active ? "border-blue-600 bg-blue-50 ring-1 ring-blue-300" : "border-transparent hover:border-gray-300 hover:bg-gray-50"}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-medium truncate ${active ? "text-blue-700" : "text-gray-800"}`}>{a.name}</span>
                    {active && <span className="text-[10px] text-blue-600">Selected</span>}
                  </div>
                  {a.description && (
                    <p className="text-[11px] text-gray-600 line-clamp-2">{a.description}</p>
                  )}
                  {a.tags && a.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {a.tags.slice(0,3).map(t => <span key={t} className="px-1 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px]">{t}</span>)}
                      {a.tags.length > 3 && <span className="px-1 py-0.5 text-[10px] text-gray-500">+{a.tags.length - 3}</span>}
                    </div>
                  )}
                </button>
              </li>
            );
          })}
          {agents.length === 0 && !loading && <li className="text-[11px] text-gray-500 px-2">No agents.</li>}
        </ul>
      </div>
      {detail && (
        <AgentDetailModal
          agent={detail}
          onClose={() => setDetail(null)}
          chosen={chosenAgent}
          onChoose={(name) => { onChoose(name); setDetail(null); }}
        />
      )}
    </div>
  );
};

interface AgentDetailModalProps { agent: AgentCard; onClose: () => void; onChoose: (name: string) => void; chosen: string | null }
const AgentDetailModal: React.FC<AgentDetailModalProps> = ({ agent, onClose, onChoose, chosen }) => {
  const skills = agent.skills ? Object.values(agent.skills) : [];
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-neutral-900 rounded shadow-lg w-full max-w-xl p-5 space-y-5">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold">{agent.name}</h3>
          <button type="button" onClick={onClose} aria-label="Close" className="text-gray-500 hover:text-gray-800">✕</button>
        </div>
        <p className="text-sm whitespace-pre-wrap">{agent.description || "No description."}</p>
        {agent.tags && agent.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {agent.tags.map(t => <span key={t} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-[11px] border border-blue-200">{t}</span>)}
          </div>
        )}
        <div>
          <h4 className="text-sm font-medium mb-2">Skills</h4>
          {skills.length === 0 && <div className="text-xs text-gray-500">No skills listed.</div>}
          <div className="space-y-2 max-h-48 overflow-auto pr-1">
            {skills.map(s => (
              <div key={s.name} className="border rounded p-2">
                <div className="text-xs font-semibold">{s.name}</div>
                {s.description && <div className="text-[11px] text-gray-600 mt-1">{s.description}</div>}
              </div>
            ))}
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100">Cancel</button>
          <button
            type="button"
            disabled={chosen === agent.name}
            onClick={() => onChoose(agent.name)}
            className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >{chosen === agent.name ? "Chosen" : "Select Agent"}</button>
        </div>
      </div>
    </div>
  );
};
