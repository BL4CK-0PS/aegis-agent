/**
 * AEGIS State & Simulation API Layer
 * Connects to simulator state, fault injection, telemetry, and subsystem analysis.
 */

import { apiClient } from './client';
import type {
  SystemState,
  DroneState,
  DependencyGraph,
  MissionImpact,
  RiskLevel,
  MissionStatus,
  CandidateAction,
  Evidence,
  Hypothesis,
} from '../types';

export async function fetchState(): Promise<SystemState> {
  return apiClient<SystemState>('/api/v1/state');
}

export async function resetSystem(seed = 42): Promise<{ status: string; state: SystemState }> {
  return apiClient<{ status: string; state: SystemState }>(`/api/v1/reset?seed=${seed}`, {
    method: 'POST',
  });
}

export async function injectGpsFault(
  bias = 6.5
): Promise<{ status: string; scenario: string; initial_bias: number; state: SystemState }> {
  return apiClient<{ status: string; scenario: string; initial_bias: number; state: SystemState }>(
    `/api/v1/scenario/gps-integrity?bias=${bias}`,
    {
      method: 'POST',
    }
  );
}

export async function tickSimulation(): Promise<SystemState> {
  return apiClient<SystemState>('/api/v1/tick', {
    method: 'POST',
  });
}

export async function fetchDependencyGraph(): Promise<DependencyGraph> {
  return apiClient<DependencyGraph>('/api/v1/dependency-graph');
}

export async function fetchMissionImpact(): Promise<MissionImpact> {
  return apiClient<MissionImpact>('/api/v1/mission-impact');
}

export async function fetchEvidenceAndHypotheses(): Promise<{
  evidence: Evidence[];
  hypotheses: Hypothesis[];
}> {
  return apiClient<{ evidence: Evidence[]; hypotheses: Hypothesis[] }>('/api/v1/evidence');
}

export async function fetchCandidateActions(): Promise<{ actions: CandidateAction[] }> {
  return apiClient<{ actions: CandidateAction[] }>('/api/v1/actions');
}

/**
 * Maps authoritative backend SystemState to presentation-ready DroneState
 */
export function mapSystemStateToDroneState(backend: SystemState): DroneState {
  const rawProgress = backend.mission_progress ?? 0;
  const progress = rawProgress > 1 ? rawProgress : Math.round(rawProgress * 100);

  // Authoritative risk mapping derived from backend telemetry invariants
  let risk: RiskLevel = 'LOW';
  if (backend.navigation_mode === 'SAFE_MODE') {
    risk = 'LOW';
  } else if (
    (backend.anomaly_score ?? 0) > 0.6 ||
    backend.gps_trust < 0.4 ||
    backend.mission_status === 'CRITICAL'
  ) {
    risk = 'CRITICAL';
  } else if (
    (backend.residual ?? 0) > 2.0 ||
    backend.gps_trust < 0.75 ||
    backend.mission_status === 'DEGRADED' ||
    backend.mission_status === 'RECOVERING'
  ) {
    risk = 'HIGH';
  } else if (backend.navigation_mode === 'INERTIAL') {
    risk = 'MEDIUM';
  }

  // Authoritative mission status mapping
  let status: MissionStatus = backend.mission_status;
  if (backend.navigation_mode === 'SAFE_MODE') {
    status = 'SAFE_MODE';
  }

  const alt = typeof backend.altitude === 'number' ? backend.altitude : 'N/A';

  return {
    time: backend.time ?? 0,
    position: backend.position ?? { x: 100, y: 50 },
    velocity: backend.velocity ?? { x: 8, y: 4 },
    altitude: alt,
    heading: backend.heading ?? 0.46,
    navigation_mode: backend.navigation_mode ?? 'GPS_ASSISTED',
    gps_trust: backend.gps_trust ?? 1.0,
    imu_trust: backend.imu_trust ?? 1.0,
    barometer_trust: backend.communication_health ? Math.round(backend.communication_health * 95) / 100 : 0.95,
    mission_progress: progress,
    mission_status: status,
    mission_risk: risk,
    residual: backend.residual ?? 0.0,
    anomaly_score: backend.anomaly_score ?? 0.0,
    gps_position: backend.gps_position,
    predicted_position: backend.predicted_position,
    gps_bias: backend.gps_bias,
    gps_fault_active: backend.gps_fault_active,
    energy: backend.energy ?? 100,
  };
}
