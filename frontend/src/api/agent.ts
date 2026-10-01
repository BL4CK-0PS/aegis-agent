/**
 * AEGIS Agent & Governance API Layer
 * Connects to agent investigation loop, human authorization, and action simulation.
 */

import { apiClient } from './client';
import type { AgentState, SimulationResult } from '../types';

export interface AgentRunRequest {
  incident_id?: string;
  goal?: string;
  auto_authorize?: boolean;
}

export async function agentInvestigate(req?: AgentRunRequest): Promise<AgentState> {
  return apiClient<AgentState>('/api/v1/agent/investigate', {
    method: 'POST',
    body: JSON.stringify(req || {}),
  });
}

export async function agentStep(autoAuthorize = false): Promise<AgentState> {
  return apiClient<AgentState>(`/api/v1/agent/step?auto_authorize=${autoAuthorize}`, {
    method: 'POST',
  });
}

export async function agentRun(req?: AgentRunRequest): Promise<any> {
  return apiClient<any>('/api/v1/agent/run', {
    method: 'POST',
    body: JSON.stringify(req || {}),
  });
}

export async function authorizeAction(
  actionId: string,
  autoResume = false
): Promise<AgentState> {
  return apiClient<AgentState>('/api/v1/agent/authorize', {
    method: 'POST',
    body: JSON.stringify({ action_id: actionId, auto_resume: autoResume }),
  });
}

export async function simulateAction(actionId: string): Promise<SimulationResult> {
  return apiClient<SimulationResult>('/api/v1/simulate', {
    method: 'POST',
    body: JSON.stringify({ action_id: actionId }),
  });
}
