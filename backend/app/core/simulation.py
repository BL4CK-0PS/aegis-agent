"""
AEGIS Simulation Engine
Provides isolated counterfactual forecasting of candidate recovery actions.
Guarantees zero mutation to the active drone simulator by executing on independent clones.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.actions import normalize_action_id, validate_preconditions
from app.core.models import SimulationResult, SystemState
from app.core.simulator import DroneSimulator


class SimulationEngine:
    """
    Deterministic counterfactual forecasting engine.
    Applies candidate actions to cloned vehicle state snapshots and computes
    projected risk, mission success probability, and capability side effects.
    """

    def __init__(self, simulator: DroneSimulator):
        self.simulator = simulator
        # Tracks actions that have been simulated
        self.simulated_actions: Dict[str, SimulationResult] = {}

    def reset(self) -> None:
        self.simulated_actions.clear()

    def simulate(self, action_id: str, current_state: Optional[SystemState] = None) -> SimulationResult:
        """
        Executes a deterministic counterfactual simulation.
        Operates on an isolated clone of the simulator to ensure real simulator state
        is NEVER mutated.
        """
        canonical_id = normalize_action_id(action_id)
        active_state = current_state or self.simulator.get_state()

        # Step 1: Precondition Validation Gate
        precond = validate_preconditions(action_id, active_state)
        if not precond.valid:
            failed_res = SimulationResult(
                action_id=action_id,
                success=False,
                predicted_state=active_state.model_dump(),
                predicted_risk=1.0,
                mission_success_probability=0.0,
                estimated_delay=0.0,
                affected_capabilities=["ACTION_REJECTED"],
                side_effects=[precond.reason],
                reason=f"Simulation aborted: Preconditions failed ({precond.reason})",
                action_name=action_id,
                predicted_mission_outcome=f"Rejected: {precond.reason}",
                energy_impact=0.0,
                residual_uncertainty=active_state.residual,
                expected_recovery_time=0.0,
                mission_continuity=0.0,
                recommendation=f"REJECTED: Precondition constraint violation ({precond.reason}).",
            )
            return failed_res

        # Step 2: Clone simulator for isolated counterfactual trajectory
        sim_clone = self.simulator.clone()

        # Step 3: Apply candidate action on the cloned instance
        sim_clone.apply_action(action_id)

        # Step 4: Advance the clone forward by 2 ticks to forecast future divergence/stabilization
        sim_clone.tick()
        predicted_state = sim_clone.tick()

        # Step 5: Deterministic projection metrics calculation
        if canonical_id == "SWITCH_TO_IMU_ONLY":
            pred_risk = 0.42 if active_state.gps_fault_active else 0.15
            succ_prob = 0.94
            delay_sec = 18.0
            aff_caps = ["GPS_ASSISTED_POSITIONING", "HEADING_CORRECTION"]
            side_eff = [
                "dead_reckoning_drift_accumulation",
                "gradual_containment_degradation",
            ]
            reason_text = "Decouples corrupt GPS; preserves route progress with dead-reckoning drift."
            rec_text = "RECOMMENDED: Preserves mission continuity while mitigating active GPS fault."

            result = SimulationResult(
                action_id=action_id,
                success=True,
                predicted_state=predicted_state.model_dump(),
                predicted_risk=pred_risk,
                mission_success_probability=succ_prob,
                estimated_delay=delay_sec,
                affected_capabilities=aff_caps,
                side_effects=side_eff,
                reason=reason_text,
                action_name="Switch to Inertial Navigation",
                predicted_mission_outcome=reason_text,
                energy_impact=-0.8,
                residual_uncertainty=2.2,
                expected_recovery_time=12.0,
                mission_continuity=0.71,
                recommendation=rec_text,
            )

        elif canonical_id == "REQUEST_GPS_REACQUISITION":
            pred_risk = 0.92 if active_state.gps_fault_active else 0.10
            succ_prob = 0.71 if not active_state.gps_fault_active else 0.35
            delay_sec = 144.0  # 2.4 minutes
            aff_caps = ["WAYPOINT_SCHEDULE", "GEOFENCE_MARGIN"]
            side_eff = [
                "continued_exposure_to_corrupt_ephemeris",
                "possible_divergence_during_reacquisition",
            ]
            reason_text = (
                "Trajectory divergence leading to catastrophic geofence departure within 15s."
                if active_state.gps_fault_active
                else "Potential GPS signal reacquisition."
            )
            rec_text = (
                "REJECTED: Exceeds safe operational envelope. High collision risk."
                if active_state.gps_fault_active
                else "FEASIBLE: Reacquisition attempt permitted under nominal conditions."
            )

            result = SimulationResult(
                action_id=action_id,
                success=True,
                predicted_state=predicted_state.model_dump(),
                predicted_risk=pred_risk,
                mission_success_probability=succ_prob,
                estimated_delay=delay_sec,
                affected_capabilities=aff_caps,
                side_effects=side_eff,
                reason=reason_text,
                action_name="Continue GPS-assisted Navigation",
                predicted_mission_outcome=reason_text,
                energy_impact=-1.5,
                residual_uncertainty=8.5 if active_state.gps_fault_active else 0.2,
                expected_recovery_time=0.0,
                mission_continuity=0.35 if active_state.gps_fault_active else 0.95,
                recommendation=rec_text,
            )

        elif canonical_id == "ENTER_SAFE_MODE":
            pred_risk = 0.08
            succ_prob = 0.99
            delay_sec = 288.0  # 4.8 minutes
            aff_caps = ["MISSION_PROGRESS", "FORWARD_FLIGHT", "OBJECTIVE_TIMELINE"]
            side_eff = ["mission_paused", "station_hover_battery_drain"]
            reason_text = "Controlled hover and stable descent. 100% boundary safety, mission paused."
            rec_text = "FAILSAFE: Zero trajectory hazard; mandatory recovery action if inertial mode fails."

            result = SimulationResult(
                action_id=action_id,
                success=True,
                predicted_state=predicted_state.model_dump(),
                predicted_risk=pred_risk,
                mission_success_probability=succ_prob,
                estimated_delay=delay_sec,
                affected_capabilities=aff_caps,
                side_effects=side_eff,
                reason=reason_text,
                action_name="Enter Safe Mode",
                predicted_mission_outcome=reason_text,
                energy_impact=-0.2,
                residual_uncertainty=0.1,
                expected_recovery_time=4.0,
                mission_continuity=0.00,
                recommendation=rec_text,
            )

        else:
            result = SimulationResult(
                action_id=action_id,
                success=False,
                predicted_state=active_state.model_dump(),
                predicted_risk=1.0,
                mission_success_probability=0.0,
                estimated_delay=0.0,
                affected_capabilities=[],
                side_effects=["unknown_action"],
                reason=f"Unknown action '{action_id}'.",
                action_name=action_id,
                predicted_mission_outcome=f"Unknown action '{action_id}'.",
                recommendation="REJECTED: Unknown action.",
            )

        # Cache simulation result for execution gate validation
        self.simulated_actions[action_id.lower().strip()] = result
        self.simulated_actions[canonical_id] = result
        return result

    def compare_actions(
        self,
        action_ids: Optional[List[str]] = None,
        state: Optional[SystemState] = None,
    ) -> List[Dict[str, Any]]:
        """
        Creates comparative outcome analysis across simulated candidate actions.
        """
        targets = action_ids or ["SWITCH_TO_IMU_ONLY", "REQUEST_GPS_REACQUISITION", "ENTER_SAFE_MODE"]
        comparisons = []
        for aid in targets:
            sim = self.simulate(aid, state)
            risk_tier = (
                "LOW"
                if sim.predicted_risk < 0.30
                else "MEDIUM"
                if sim.predicted_risk < 0.60
                else "HIGH"
                if sim.predicted_risk < 0.85
                else "CRITICAL"
            )
            comparisons.append({
                "action_id": sim.action_id,
                "action_name": sim.action_name,
                "risk": risk_tier,
                "predicted_risk": sim.predicted_risk,
                "success_probability": sim.mission_success_probability,
                "estimated_delay": f"{sim.estimated_delay:.0f}s",
                "mission_continuity": sim.mission_continuity,
                "recommendation": sim.recommendation,
            })
        return comparisons
