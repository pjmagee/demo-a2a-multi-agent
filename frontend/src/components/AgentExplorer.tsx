"use client";

import { useEffect, useMemo, useState } from "react";

import { BFF_BASE_URL } from "@/lib/config";
import type {
  AgentCard,
  AgentMessageRequest,
  AgentMessageResponse,
} from "@/types/agent";

import styles from "./AgentExplorer.module.css";

interface AgentWithState extends AgentCard {
  contextId?: string | null;
  isSending?: boolean;
  error?: string | null;
  lastResponse?: AgentMessageResponse | null;
}

async function fetchAgents(): Promise<AgentCard[]> {
  const response = await fetch(`${BFF_BASE_URL}/agents`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Unable to load agents (${response.status})`);
  }
  return response.json();
}

async function sendMessage(payload: AgentMessageRequest): Promise<AgentMessageResponse> {
  const response = await fetch(`${BFF_BASE_URL}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Agent call failed (${response.status})`);
  }
  return response.json();
}

export function AgentExplorer() {
  const [agents, setAgents] = useState<AgentWithState[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setIsLoading(true);
        const data = await fetchAgents();
        if (!mounted) {
          return;
        }
        setAgents(data);
        if (data.length > 0) {
          setSelectedAgent(data[0].name);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const activeAgent = useMemo(
    () => agents.find((agent) => agent.name === selectedAgent),
    [agents, selectedAgent],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeAgent || !message.trim()) {
      return;
    }

    setAgents((current) =>
      current.map((agent) =>
        agent.name === activeAgent.name
          ? { ...agent, isSending: true, error: null }
          : agent,
      ),
    );

    try {
      const response = await sendMessage({
        agent_name: activeAgent.name,
        message,
        context_id: activeAgent.contextId,
      });

      setAgents((current) =>
        current.map((agent) =>
          agent.name === activeAgent.name
            ? {
                ...agent,
                contextId: response.context_id ?? agent.contextId,
                lastResponse: response,
                isSending: false,
              }
            : agent,
        ),
      );
      setMessage("");
    } catch (err) {
      setAgents((current) =>
        current.map((agent) =>
          agent.name === activeAgent.name
            ? {
                ...agent,
                isSending: false,
                error: err instanceof Error ? err.message : String(err),
              }
            : agent,
        ),
      );
    }
  }

  if (isLoading) {
    return <p className={styles.info}>Loading agents…</p>;
  }

  if (error) {
    return <p className={styles.error}>{error}</p>;
  }

  if (agents.length === 0) {
    return (
      <p className={styles.info}>
        No agents discovered. Configure WEBAPP_AGENT_ADDRESSES in the backend.
      </p>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.agentList}>
        {agents.map((agent) => (
          <button
            key={agent.name}
            type="button"
            onClick={() => setSelectedAgent(agent.name)}
            className={`${styles.agentButton} ${
              agent.name === selectedAgent ? styles.agentButtonActive : ""
            }`}
          >
            {agent.name}
          </button>
        ))}
      </div>

      {activeAgent && (
        <div className={styles.container}>
          <div className={styles.agentCard}>
            <h2 className={styles.agentCardTitle}>{activeAgent.name}</h2>
            <p className={styles.agentCardDescription}>{activeAgent.description}</p>
            <div className={styles.skillList}>
              {activeAgent.skills.map((skill) => (
                <div key={skill.id} className={styles.skillItem}>
                  <span className={styles.skillName}>{skill.name}</span>: {skill.description}
                </div>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className={styles.form}>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              rows={3}
              className={styles.textarea}
              placeholder={`Message ${activeAgent.name}`}
              disabled={activeAgent.isSending}
            />
            <button
              type="submit"
              className={styles.sendButton}
              disabled={activeAgent.isSending || !message.trim()}
            >
              {activeAgent.isSending ? "Sending…" : "Send"}
            </button>
          </form>

          {activeAgent.lastResponse && (
            <pre className={styles.response}>
              {JSON.stringify(activeAgent.lastResponse.raw_response ?? {}, null, 2)}
            </pre>
          )}

          {activeAgent.error && <p className={styles.error}>{activeAgent.error}</p>}
        </div>
      )}
    </div>
  );
}
