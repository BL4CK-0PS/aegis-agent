import type { DroneState, RiskLevel, MissionStatus } from '../types/simulator';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface BackendSystemState {
  time: number;
  position: { x: number; y: number };
  velocity: { x: number; y: number };
  navigation_mode: 'GPS_ASSISTED' | 'INERTIAL' | 'SAFE_MODE';
  gps_trust: number;
  imu_trust: number;
  mission_progress: number;
  mission_status: MissionStatus;
  residual?: number;
  anomaly_score?: number;
  gps_fault_active?: boolean;
}

export interface BackendAgentEvent {
  step: number;
  tool: string;
  status: 'pending' | 'completed' | 'failed' | 'awaiting_authorization';
  summary: string;
  details?: Record<string, any>;
}

export interface BackendAgentState {
  incident_id: string;
  goal: string;
  current_step: number;
  max_steps: number;
  completed: boolean;
  waiting_for_authorization: boolean;
  pending_action: string | null;
  policy_blocked: boolean;
  events: BackendAgentEvent[];
  last_action: string | null;
  last_execution_result: Record<string, any> | null;
  last_verification_result: Record<string, any> | null;
  final_summary: string | null;
}

export function mapBackendToDroneState(backend: BackendSystemState): DroneState {
  const rawProgress = backend.mission_progress ?? 0;
  const progress = rawProgress > 1 ? rawProgress : Math.round(rawProgress * 100);

  let risk: RiskLevel = 'LOW';
  if (backend.navigation_mode === 'SAFE_MODE') {
    risk = 'LOW';
  } else if ((backend.anomaly_score ?? 0) > 0.5 || backend.gps_trust < 0.5 || backend.mission_status === 'CRITICAL' || backend.mission_status === 'DEGRADED') {
    risk = 'HIGH';
  } else if (backend.navigation_mode === 'INERTIAL') {
    risk = 'MEDIUM';
  }

  let status: MissionStatus = backend.mission_status;
  if (backend.navigation_mode === 'SAFE_MODE') {
    status = 'RECOVERED';
  }

  return {
    time: backend.time ?? 0,
    position: backend.position ?? { x: 100, y: 50 },
    velocity: backend.velocity ?? { x: 8, y: 4 },
    navigation_mode: backend.navigation_mode ?? 'GPS_ASSISTED',
    gps_trust: backend.gps_trust ?? 1.0,
    imu_trust: backend.imu_trust ?? 1.0,
    mission_progress: progress,
    mission_status: status,
    mission_risk: risk,
  };
}

export async function fetchState(): Promise<BackendSystemState> {
  const res = await fetch(`${API_BASE}/state`);
  if (!res.ok) throw new Error(`Failed to fetch state: ${res.statusText}`);
  return res.json();
}

export async function resetSystem(seed = 42): Promise<{ status: string; state: BackendSystemState }> {
  const res = await fetch(`${API_BASE}/reset?seed=${seed}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to reset system: ${res.statusText}`);
  return res.json();
}

export async function injectGpsFault(bias = 6.5): Promise<{ status: string; scenario: string; state: BackendSystemState }> {
  const res = await fetch(`${API_BASE}/scenario/gps-integrity?bias=${bias}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to inject GPS fault: ${res.statusText}`);
  return res.json();
}

export async function tickSimulation(): Promise<BackendSystemState> {
  const res = await fetch(`${API_BASE}/tick`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to tick simulation: ${res.statusText}`);
  return res.json();
}

export async function agentStep(autoAuthorize = false): Promise<BackendAgentState> {
  const res = await fetch(`${API_BASE}/agent/step?auto_authorize=${autoAuthorize}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to step agent: ${res.statusText}`);
  return res.json();
}

export async function authorizeAction(actionId: string, autoResume = false): Promise<BackendAgentState> {
  const res = await fetch(`${API_BASE}/agent/authorize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action_id: actionId, auto_resume: autoResume }),
  });
  if (!res.ok) throw new Error(`Failed to authorize action: ${res.statusText}`);
  return res.json();
}
