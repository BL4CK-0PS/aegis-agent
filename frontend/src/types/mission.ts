/**
 * AEGIS Mission & Telemetry Types
 * Matches canonical backend models from app.core.models and app.core.risk
 */

export type NavigationMode = 'GPS_ASSISTED' | 'INERTIAL' | 'SAFE_MODE';

export type MissionStatus =
  | 'NORMAL'
  | 'NOMINAL'
  | 'DEGRADED'
  | 'CRITICAL'
  | 'RECOVERING'
  | 'SAFE_MODE'
  | 'RECOVERED'
  | 'ABORTED'
  | 'SAFE';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Position {
  x: number;
  y: number;
}

export interface Velocity {
  x: number;
  y: number;
}

/**
 * Instantaneous vehicle and telemetry state from GET /api/v1/state
 */
export interface SystemState {
  time: number;
  position: Position;
  velocity: Velocity;
  altitude?: number;
  navigation_mode: NavigationMode;
  gps_trust: number;
  imu_trust: number;
  mission_progress: number;
  mission_status: MissionStatus;
  predicted_position?: Position;
  gps_position?: Position;
  heading?: number;
  residual?: number;
  anomaly_score?: number;
  gps_bias?: number;
  gps_fault_active?: boolean;
  energy?: number;
  communication_health?: number;
}

/**
 * Frontend presentation state for UI components
 */
export interface DroneState {
  time: number;
  position: Position;
  velocity: Velocity;
  altitude: number | 'N/A';
  heading: number;
  navigation_mode: NavigationMode;
  gps_trust: number;
  imu_trust: number;
  barometer_trust: number;
  mission_progress: number;
  mission_status: MissionStatus;
  mission_risk: RiskLevel;
  residual: number;
  anomaly_score: number;
  gps_position?: Position;
  predicted_position?: Position;
  gps_bias?: number;
  gps_fault_active?: boolean;
  energy: number;
}

export interface CapabilityImpact {
  name: string;
  level: 'NOMINAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

/**
 * Matches backend MissionImpact from app.core.models
 */
export interface MissionImpact {
  operational_risk: number;
  risk_level: RiskLevel;
  position_error?: number;
  mission_status: MissionStatus;
  affected_capabilities: string[];
  time_to_critical_seconds: number;
  recommendation_urgency: string;
  summary: string;
}

/**
 * Subsystem dependency graph representations
 */
export interface DependencyNode {
  id: string;
  label: string;
  type: string;
  status: string;
  health: number;
}

export interface DependencyEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface DependencyGraph {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
}
