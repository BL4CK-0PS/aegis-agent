"""
AEGIS Mission Risk & Dependency Graph Engine
Maps telemetry residuals and sensor trust degradation to system dependency graphs
and mission-level operational risk impact.
"""

from __future__ import annotations
from typing import List
from app.core.models import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    MissionImpact,
    MissionStatus,
    NavigationMode,
    SystemState,
)


class RiskEngine:
    """
    Computes operational impact, affected mission capabilities, time to boundary hazard,
    and structured dependency graph propagation.
    """

    @classmethod
    def evaluate_mission_impact(cls, state: SystemState) -> MissionImpact:
        if state.navigation_mode == NavigationMode.SAFE_MODE:
            return MissionImpact(
                operational_risk=0.08,
                mission_status=MissionStatus.RECOVERED,
                affected_capabilities=["Waypoint Traversal (Vehicle safely holding position / landed)"],
                time_to_critical_seconds=999.0,
                recommendation_urgency="RESOLVED",
                summary="Vehicle is secured in SAFE_MODE. Operational risk is minimized to ground/hover safety baseline.",
            )

        if state.navigation_mode == NavigationMode.INERTIAL:
            # Inertial mode: GPS ignored, but gyro drift slowly accumulates
            return MissionImpact(
                operational_risk=0.42,
                mission_status=MissionStatus.DEGRADED,
                affected_capabilities=["Extended Precision Navigation (Dead-reckoning drift ~0.5m/min)"],
                time_to_critical_seconds=120.0,
                recommendation_urgency="EVALUATE",
                summary="Operating on inertial dead-reckoning. GPS bias decoupled, but navigation requires verification.",
            )

        # GPS_ASSISTED mode
        if state.residual > 5.0 or state.gps_trust < 0.40:
            return MissionImpact(
                operational_risk=0.88,
                mission_status=MissionStatus.CRITICAL,
                affected_capabilities=[
                    "Precision Waypoint Traversal",
                    "Geofence Boundary Enforcement",
                    "Obstacle Avoidance Alignment",
                    "Autonomous Return-to-Home Guidance",
                ],
                time_to_critical_seconds=15.0,
                recommendation_urgency="IMMEDIATE",
                summary=(
                    f"CRITICAL: GPS trust is {state.gps_trust:.2f} with {state.residual:.1f}m divergence. "
                    "Continued GPS flight will cause immediate trajectory departure or geofence violation."
                ),
            )
        elif state.residual > 2.0 or state.gps_trust < 0.70:
            return MissionImpact(
                operational_risk=0.55,
                mission_status=MissionStatus.DEGRADED,
                affected_capabilities=["Precision Waypoint Traversal"],
                time_to_critical_seconds=45.0,
                recommendation_urgency="HIGH",
                summary="DEGRADED: Telemetry residual exceeds nominal variance. Mission guidance stability impaired.",
            )
        else:
            return MissionImpact(
                operational_risk=0.05,
                mission_status=MissionStatus.NOMINAL,
                affected_capabilities=[],
                time_to_critical_seconds=999.0,
                recommendation_urgency="NONE",
                summary="NOMINAL: All flight systems and sensor margins within operational envelope.",
            )

    @classmethod
    def get_dependency_graph(cls, state: SystemState) -> DependencyGraph:
        gps_status = "nominal"
        if state.gps_trust < 0.40:
            gps_status = "critical"
        elif state.gps_trust < 0.75:
            gps_status = "degraded"

        nav_status = "nominal"
        if state.navigation_mode == NavigationMode.SAFE_MODE:
            nav_status = "safe_mode"
        elif state.residual > 5.0 and state.navigation_mode == NavigationMode.GPS_ASSISTED:
            nav_status = "critical"
        elif state.residual > 2.0 or state.navigation_mode == NavigationMode.INERTIAL:
            nav_status = "degraded"

        mission_status = "nominal"
        if state.mission_status in (MissionStatus.CRITICAL, MissionStatus.DEGRADED):
            mission_status = state.mission_status.value.lower()
        elif state.mission_status == MissionStatus.RECOVERED:
            mission_status = "recovered"

        nodes = [
            DependencyNode(
                id="sensor_gps",
                label="GPS Receiver Solution",
                type="sensor",
                status=gps_status,
                health=state.gps_trust,
            ),
            DependencyNode(
                id="sensor_imu",
                label="IMU Tri-Axial Accelerometer/Gyro",
                type="sensor",
                status="nominal",
                health=state.imu_trust,
            ),
            DependencyNode(
                id="subsystem_estimation",
                label="Kalman State Estimator",
                type="subsystem",
                status=nav_status,
                health=round((state.gps_trust + state.imu_trust) / 2.0, 2),
            ),
            DependencyNode(
                id="capability_navigation",
                label="Navigation & Flight Guidance",
                type="capability",
                status=nav_status,
                health=0.40 if nav_status == "critical" else (0.75 if nav_status == "degraded" else 0.98),
            ),
            DependencyNode(
                id="objective_mission",
                label="Mission Route Execution",
                type="objective",
                status=mission_status,
                health=round(1.0 - (0.88 if mission_status == "critical" else (0.45 if mission_status == "degraded" else 0.05)), 2),
            ),
            DependencyNode(
                id="objective_containment",
                label="Geofence Safety Containment",
                type="objective",
                status=mission_status,
                health=0.25 if mission_status == "critical" else 0.95,
            ),
        ]

        edges = [
            DependencyEdge(source="sensor_gps", target="subsystem_estimation", relationship="feeds_measurement"),
            DependencyEdge(source="sensor_imu", target="subsystem_estimation", relationship="feeds_measurement"),
            DependencyEdge(source="subsystem_estimation", target="capability_navigation", relationship="enables_guidance"),
            DependencyEdge(source="capability_navigation", target="objective_mission", relationship="traverses_waypoints"),
            DependencyEdge(source="capability_navigation", target="objective_containment", relationship="enforces_boundary"),
        ]

        return DependencyGraph(nodes=nodes, edges=edges)
