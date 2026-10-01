"""
AEGIS Core Models
Defines domain structures, integration objects, telemetry schemas,
and typed contracts for the decision intelligence loop.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NavigationMode(str, Enum):
    GPS_ASSISTED = "GPS_ASSISTED"
    INERTIAL = "INERTIAL"
    SAFE_MODE = "SAFE_MODE"


class MissionStatus(str, Enum):
    NORMAL = "NORMAL"
    NOMINAL = "NORMAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    RECOVERED = "RECOVERED"
    ABORTED = "ABORTED"


class PolicyStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_HUMAN_AUTHORIZATION = "REQUIRES_HUMAN_AUTHORIZATION"


class Position(BaseModel):
    x: float
    y: float


class Velocity(BaseModel):
    x: float
    y: float


class SystemState(BaseModel):
    """
    Contract object shared with Person B (UI / Frontend).
    Represents instantaneous drone and mission state.
    """
    time: float
    position: Position
    velocity: Velocity
    navigation_mode: NavigationMode
    gps_trust: float
    imu_trust: float
    mission_progress: float
    mission_status: MissionStatus

    # Extended telemetry attributes
    predicted_position: Optional[Position] = None
    gps_position: Optional[Position] = None
    heading: float = 0.0
    residual: float = 0.0
    anomaly_score: float = 0.0
    gps_bias: float = 0.0
    gps_fault_active: bool = False
    energy: float = 100.0
    communication_health: float = 1.0


class Observations(BaseModel):
    gps_position: Position
    predicted_position: Position
    residual: float
    anomaly_score: float
    provenance: List[str]
    timestamp: float
    description: str = ""


class TrustSnapshot(BaseModel):
    gps_trust: float
    imu_trust: float
    communication_trust: float
    reasons: List[str]
    timestamp: float


class Hypothesis(BaseModel):
    id: str
    title: str
    likelihood: float
    explanation: str
    supporting_evidence: List[str]
    name: Optional[str] = None
    confidence: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        if self.name is None:
            self.name = self.title
        if self.confidence is None:
            self.confidence = self.likelihood


class EvidenceItem(BaseModel):
    id: str
    source: str
    metric: str
    value: Any
    interpretation: str
    severity: str


class MissionImpact(BaseModel):
    operational_risk: float
    mission_status: MissionStatus
    affected_capabilities: List[str]
    time_to_critical_seconds: float
    recommendation_urgency: str
    summary: str


class DependencyNode(BaseModel):
    id: str
    label: str
    type: str  # sensor, navigation, objective
    status: str  # nominal, degraded, critical
    health: float


class DependencyEdge(BaseModel):
    source: str
    target: str
    relationship: str


class DependencyGraph(BaseModel):
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]


class CandidateAction(BaseModel):
    id: str
    name: str
    risk: float
    mission_continuity: float
    description: str = ""
    target_mode: Optional[NavigationMode] = None


class SimulationResult(BaseModel):
    action_id: str
    action_name: str
    predicted_mission_outcome: str
    predicted_risk: float
    energy_impact: float
    residual_uncertainty: float
    expected_recovery_time: float
    mission_continuity: float
    recommendation: str


class PolicyEvaluation(BaseModel):
    action_id: str
    status: PolicyStatus
    allowed: bool
    requires_authorization: bool
    reason: str
    risk_tier: str


class ExecutionResult(BaseModel):
    action_id: str
    success: bool
    timestamp: float
    previous_mode: NavigationMode
    new_mode: NavigationMode
    details: str


class VerificationResult(BaseModel):
    """
    Contract object shared with Person B for verification outcomes.
    """
    verified: bool
    reason: str
    next_action_required: bool
    status: str = "nominal"
    position_residual: float = 0.0
    mission_risk: float = 0.0


class AgentEvent(BaseModel):
    """
    Event emitted during step-by-step agent investigation.
    """
    step: int
    tool: str
    status: str  # pending, running, completed, failed
    summary: str
    timestamp: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
