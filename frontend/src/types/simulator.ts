export type NavigationMode = 'GPS_ASSISTED' | 'INERTIAL' | 'SAFE_MODE';
export type MissionStatus = 'NORMAL' | 'DEGRADED' | 'CRITICAL' | 'SAFE' | 'RECOVERED';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export type LifecyclePhase =
  | 'NORMAL'
  | 'INCIDENT_DETECTED'
  | 'INVESTIGATING'
  | 'EVIDENCE_GATHERED'
  | 'HYPOTHESIS_FORMED'
  | 'ACTION_SIMULATED'
  | 'POLICY_CHECK'
  | 'AUTHORIZED'
  | 'EXECUTED'
  | 'VERIFICATION_FAILED'
  | 'REPLAN'
  | 'SAFE_MODE';

export interface DroneState {
  time: number;
  position: { x: number; y: number };
  velocity: { x: number; y: number };
  navigation_mode: NavigationMode;
  gps_trust: number;
  imu_trust: number;
  barometer_trust?: number;
  mission_progress: number;
  mission_status: MissionStatus;
  mission_risk: RiskLevel;
  residual?: number;
  anomaly_score?: number;
}

export interface AgentEvent {
  step: number;
  tool: string;
  status: 'pending' | 'completed' | 'failed' | 'awaiting_authorization';
  summary: string;
  details?: Record<string, any>;
  subdetails?: string[];
}

export interface Evidence {
  id: string;
  metric: string;
  value: string;
  confidence: number;
  description: string;
  source: string;
  severity?: 'NOMINAL' | 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface Hypothesis {
  id: string;
  description: string;
  confidence: number;
  supportingEvidence?: number;
  contradictingEvidence?: number;
}

export interface CandidateAction {
  id: string;
  name: string;
  risk: RiskLevel;
  mission_continuity: number;
  success_rate?: number;
  expected_delay?: string;
  policy_status?: 'ALLOWED' | 'REQUIRES_AUTH' | 'DENIED';
  recommended?: boolean;
}

export interface VerificationResult {
  verified: boolean;
  reason: string;
  expected?: string;
  actual?: string;
  next_action_required: boolean;
}

export interface CapabilityImpact {
  name: string;
  level: 'NOMINAL' | 'MEDIUM' | 'HIGH';
}
