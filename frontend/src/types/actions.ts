/**
 * AEGIS Governance, Actions & Verification Types
 * Matches canonical models from app.core.models, policy, and execution
 */

import type { NavigationMode, RiskLevel } from './mission';

export type PolicyStatus =
  | 'PENDING'
  | 'ALLOWED'
  | 'DENIED'
  | 'REQUIRES_AUTHORIZATION'
  | 'APPROVED';

export interface SimulationResult {
  action_id: string;
  action_name?: string;
  predicted_mission_outcome: string;
  predicted_risk: number;
  energy_impact?: number;
  residual_uncertainty?: number;
  expected_recovery_time?: number;
  mission_continuity: number;
  recommendation: string;
  feasible?: boolean;
  predicted_residual?: number;
  mission_success_probability?: number;
  estimated_delay?: number;
  state_delta?: Record<string, any>;
}

export interface CandidateAction {
  id: string;
  name: string;
  description?: string;
  risk: RiskLevel;
  risk_num?: number;
  mission_continuity: number;
  target_mode?: NavigationMode;
  success_rate?: number;
  expected_delay?: string;
  policy_status?: PolicyStatus;
  recommended?: boolean;
  simulation?: SimulationResult;
}

export interface PolicyEvaluation {
  action_id: string;
  status: string;
  allowed: boolean;
  requires_authorization: boolean;
  reason: string;
  risk_tier: string;
}

export interface ExecutionResult {
  action_id: string;
  success: boolean;
  timestamp: number;
  previous_mode: NavigationMode;
  new_mode: NavigationMode;
  details: string;
}

export interface VerificationResult {
  verified: boolean;
  reason: string;
  expected?: string;
  actual?: string;
  next_action_required: boolean;
  status?: string;
  position_residual?: number;
  mission_risk?: number | string;
}
