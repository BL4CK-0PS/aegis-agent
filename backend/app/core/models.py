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
    RECOVERING = "RECOVERING"
    SAFE_MODE = "SAFE_MODE"
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
    altitude: Optional[float] = 120.0
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
    confidence: float = 0.95
    relationship: Optional[str] = None


class MissionImpact(BaseModel):
    operational_risk: float
    mission_status: MissionStatus
    affected_capabilities: List[str]
    time_to_critical_seconds: float
    recommendation_urgency: str
    summary: str
    risk_level: str = "LOW"
    position_error: Optional[float] = None


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


class ActionCategory(str, Enum):
    SENSOR_MANAGEMENT = "SENSOR_MANAGEMENT"
    NAVIGATION_RECONFIGURATION = "NAVIGATION_RECONFIGURATION"
    FAILSAFE = "FAILSAFE"
    MISSION_CONTROL = "MISSION_CONTROL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    MINIMAL = "MINIMAL"


class AuthorizationStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class PreconditionCheck(BaseModel):
    name: str
    required: Any
    actual: Any
    passed: bool
    description: str = ""


class PreconditionResult(BaseModel):
    valid: bool
    reason: str = ""
    checks: List[PreconditionCheck] = Field(default_factory=list)


class CandidateAction(BaseModel):
    id: str
    name: str
    description: str = ""
    category: str = "NAVIGATION_RECONFIGURATION"
    required_capabilities: List[str] = Field(default_factory=list)
    risk_level: str = "MEDIUM"
    requires_authorization: bool = False
    preconditions: List[str] = Field(default_factory=list)
    expected_effects: List[str] = Field(default_factory=list)

    # Backwards compatibility fields
    risk: float = 0.42
    mission_continuity: float = 0.71
    target_mode: Optional[NavigationMode] = None

    def model_post_init(self, __context: Any) -> None:
        # Synchronize risk_level and numeric risk if needed
        if self.risk_level == "LOW" and self.risk > 0.4:
            self.risk = 0.25
        elif self.risk_level == "CRITICAL" and self.risk < 0.7:
            self.risk = 0.90


class SimulationResult(BaseModel):
    action_id: str
    success: bool = True
    predicted_state: Optional[Dict[str, Any]] = None
    predicted_risk: float = 0.5
    mission_success_probability: float = 0.85
    estimated_delay: float = 0.0
    affected_capabilities: List[str] = Field(default_factory=list)
    side_effects: List[str] = Field(default_factory=list)
    reason: str = ""

    # Backwards compatibility fields
    action_name: str = ""
    predicted_mission_outcome: str = ""
    energy_impact: float = -0.5
    residual_uncertainty: float = 1.0
    expected_recovery_time: float = 10.0
    mission_continuity: float = 0.7
    recommendation: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.action_name:
            self.action_name = self.action_id
        if not self.predicted_mission_outcome and self.reason:
            self.predicted_mission_outcome = self.reason
        if not self.reason and self.predicted_mission_outcome:
            self.reason = self.predicted_mission_outcome


class PolicyEvaluation(BaseModel):
    action_id: str
    status: PolicyStatus = PolicyStatus.ALLOW
    allowed: bool = True
    requires_authorization: bool = False
    reason: str = ""
    risk_tier: str = "LOW"
    risk_level: str = "LOW"
    authorization_status: AuthorizationStatus = AuthorizationStatus.NOT_REQUIRED
    violations: List[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if self.risk_level and not self.risk_tier:
            self.risk_tier = self.risk_level
        elif self.risk_tier and not self.risk_level:
            self.risk_level = self.risk_tier


# Alias PolicyResult for Phase 3 naming consistency
PolicyResult = PolicyEvaluation


class ExecutionResult(BaseModel):
    action_id: str
    status: str = "COMPLETED"  # READY, EXECUTING, COMPLETED, FAILED
    started_at: float = 0.0
    completed_at: float = 0.0
    state_changes: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""

    # Backwards compatibility fields
    success: bool = True
    timestamp: float = 0.0
    previous_mode: NavigationMode = NavigationMode.GPS_ASSISTED
    new_mode: NavigationMode = NavigationMode.INERTIAL
    details: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.details and self.message:
            self.details = self.message
        elif not self.message and self.details:
            self.message = self.details
        if self.status == "FAILED" and self.success:
            self.success = False
        elif self.status == "COMPLETED" and not self.success:
            self.status = "FAILED"


class VerificationCheck(BaseModel):
    name: str
    expected: str
    actual: str
    passed: bool


class VerificationResult(BaseModel):
    """
    Contract object shared with Person B for verification outcomes.
    """
    success: bool = True
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    failed_checks: List[str] = Field(default_factory=list)
    message: str = ""

    # Backwards compatibility fields
    verified: bool = True
    reason: str = ""
    next_action_required: bool = False
    status: str = "nominal"
    position_residual: float = 0.0
    mission_risk: float = 0.0

    def model_post_init(self, __context: Any) -> None:
        if not self.success and self.verified:
            self.verified = False
        elif not self.verified and self.success:
            self.success = False
        if not self.message and self.reason:
            self.message = self.reason
        elif not self.reason and self.message:
            self.reason = self.message


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
