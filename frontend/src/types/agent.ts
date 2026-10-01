/**
 * AEGIS Agent & Investigation Types
 * Matches canonical models from app.agent.state, app.core.models, and app.core.evidence
 */

export type AgentEventStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'awaiting_authorization'
  | 'error';

export interface AgentEvent {
  step: number;
  tool: string;
  status: AgentEventStatus;
  summary: string;
  timestamp?: number;
  details?: Record<string, any>;
  subdetails?: string[];
}

export interface Evidence {
  id: string;
  source: string;
  metric: string;
  value: string | number;
  confidence: number;
  description: string;
  severity: 'NOMINAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  relationship?: string;
}

export interface Hypothesis {
  id: string;
  title?: string;
  name?: string;
  description: string;
  confidence: number;
  likelihood?: number;
  explanation?: string;
  supporting_evidence?: string[];
  supportingEvidence?: number;
  contradictingEvidence?: number;
}

export interface AgentState {
  incident_id: string;
  goal: string;
  current_step: number;
  max_steps: number;
  completed: boolean;
  waiting_for_authorization: boolean;
  pending_action: string | null;
  policy_blocked: boolean;
  events: AgentEvent[];
  replan_count: number;
  last_action: string | null;
  last_execution_result: Record<string, any> | null;
  last_verification_result: Record<string, any> | null;
  final_summary: string | null;
}

export type DemoPhase =
  | 'NORMAL'
  | 'INCIDENT'
  | 'INVESTIGATING'
  | 'EVIDENCE'
  | 'HYPOTHESIS'
  | 'IMPACT'
  | 'ACTION'
  | 'SIMULATION'
  | 'POLICY'
  | 'EXECUTION'
  | 'VERIFICATION'
  | 'REPLANNING'
  | 'RECOVERY';

export type LifecyclePhase =
  | 'IDLE'
  | 'NORMAL'
  | 'INCIDENT'
  | 'INCIDENT_DETECTED'
  | 'INVESTIGATING'
  | 'ANALYZING'
  | 'EVIDENCE_GATHERED'
  | 'HYPOTHESIS_FORMED'
  | 'PLANNING'
  | 'SIMULATING'
  | 'ACTION_SIMULATED'
  | 'POLICY_CHECK'
  | 'AUTHORIZATION'
  | 'AUTHORIZED'
  | 'EXECUTING'
  | 'EXECUTED'
  | 'VERIFYING'
  | 'VERIFICATION_FAILED'
  | 'REPLANNING'
  | 'REPLAN'
  | 'RECOVERING'
  | 'SAFE_MODE'
  | 'COMPLETED'
  | 'FAILED';
