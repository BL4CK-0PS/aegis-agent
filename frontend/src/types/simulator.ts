export type NavigationMode = 'GPS_ASSISTED' | 'INERTIAL' | 'SAFE_MODE';
export type MissionStatus = 'NORMAL' | 'DEGRADED' | 'CRITICAL' | 'SAFE' | 'RECOVERED';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface DroneState {
  time: number;
  position: { x: number; y: number };
  velocity: { x: number; y: number };
  navigation_mode: NavigationMode;
  gps_trust: number;
  imu_trust: number;
  mission_progress: number;
  mission_status: MissionStatus;
  mission_risk: RiskLevel;
}

export interface AgentEvent {
  step: number;
  tool: string;
  status: 'pending' | 'completed' | 'failed';
  summary: string;
}

export interface Evidence {
  id: string;
  description: string;
  source: string;
}

export interface Hypothesis {
  id: string;
  description: string;
  confidence: number;
}

export interface CandidateAction {
  id: string;
  name: string;
  risk: RiskLevel;
  mission_continuity: number;
  recommended?: boolean;
}

export interface VerificationResult {
  verified: boolean;
  reason: string;
  next_action_required: boolean;
}
