export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  input_modes: string[];
  output_modes: string[];
}

export interface AgentCard {
  name: string;
  description: string;
  version?: string | null;
  url: string;
  skills: AgentSkill[];
}

export interface AgentMessageRequest {
  agent_name: string;
  message: string;
  context_id?: string | null;
}

export interface AgentMessageResponse {
  status: string;
  context_id?: string | null;
  raw_response?: Record<string, unknown> | null;
}
