"""
AEGIS Deterministic Drone Simulator
Maintains simulated vehicle state, sensor telemetry, fault injection,
and physical/mission progression.
"""

from __future__ import annotations
import math
import random
from typing import Optional, Tuple
from app.core.models import (
    MissionStatus,
    NavigationMode,
    Position,
    SystemState,
    Velocity,
)


class DroneSimulator:
    """
    Deterministic simulator modeling a waypoint-following autonomous drone
    with multi-sensor navigation (GPS + IMU), fault injection, and state degradation.
    """

    def __init__(self, seed: int = 42, deliberate_failure_enabled: bool = True):
        self.initial_seed = seed
        self.deliberate_failure_enabled = deliberate_failure_enabled
        self.reset()

    def reset(self, seed: Optional[int] = None) -> None:
        """Resets the simulator to clean nominal state."""
        if seed is not None:
            self.initial_seed = seed
        self._rng = random.Random(self.initial_seed)

        self.time: float = 0.0
        self.dt: float = 1.0

        # Position and kinematic state
        self.x: float = 100.0
        self.y: float = 50.0
        self.vx: float = 8.0
        self.vy: float = 4.0
        self.heading: float = math.atan2(self.vy, self.vx)

        # Predicted / dead-reckoning position (inertial model)
        self.pred_x: float = self.x
        self.pred_y: float = self.y

        # GPS sensor state
        self.gps_x: float = self.x
        self.gps_y: float = self.y
        self.gps_bias: float = 0.0
        self.gps_fault_active: bool = False

        # Subsystems & trust
        self.navigation_mode: NavigationMode = NavigationMode.GPS_ASSISTED
        self.gps_trust: float = 0.98
        self.imu_trust: float = 0.95
        self.communication_health: float = 1.0
        self.energy: float = 100.0

        # Mission state
        self.mission_progress: float = 0.10
        self.mission_status: MissionStatus = MissionStatus.NOMINAL

        # Anomaly metrics
        self.residual: float = 0.0
        self.anomaly_score: float = 0.0
        self.fault_tick_counter: int = 0

        # Verification failure tracking
        self.has_triggered_deliberate_failure: bool = False
        self.replan_count: int = 0

    def inject_gps_fault(self, initial_bias: float = 6.0) -> None:
        """
        Injects a GPS integrity fault (spoofing / multipath / ephemeris corruption).
        """
        self.gps_fault_active = True
        self.gps_bias = initial_bias
        self.fault_tick_counter = 1
        self.mission_status = MissionStatus.DEGRADED
        self._update_telemetry_residuals()

    def tick(self) -> SystemState:
        """
        Advances the simulation forward by one time step dt.
        """
        self.time += self.dt

        # Kinematic updates based on navigation mode
        if self.navigation_mode == NavigationMode.SAFE_MODE:
            # Safe mode: slow descent / hover, velocity decays to 0
            self.vx *= 0.3
            self.vy *= 0.3
            if abs(self.vx) < 0.1:
                self.vx = 0.0
            if abs(self.vy) < 0.1:
                self.vy = 0.0
            self.x += self.vx * self.dt
            self.y += self.vy * self.dt
            self.pred_x = self.x
            self.pred_y = self.y
            self.energy = max(0.0, self.energy - 0.05)
            self.mission_status = MissionStatus.RECOVERED
        else:
            # Normal or Inertial flight
            self.x += self.vx * self.dt
            self.y += self.vy * self.dt
            self.pred_x += self.vx * self.dt
            self.pred_y += self.vy * self.dt
            self.energy = max(0.0, self.energy - 0.2)
            self.mission_progress = min(1.0, self.mission_progress + 0.03)

        # Fault propagation
        if self.gps_fault_active:
            self.fault_tick_counter += 1
            # Bias grows over time
            self.gps_bias += 2.5
            # Trust degrades as bias persists
            decay = 0.12 * math.log1p(self.fault_tick_counter)
            self.gps_trust = max(0.05, 0.98 - (self.gps_bias * 0.04) - decay)

            if self.navigation_mode == NavigationMode.GPS_ASSISTED:
                if self.gps_trust < 0.35:
                    self.mission_status = MissionStatus.CRITICAL
                else:
                    self.mission_status = MissionStatus.DEGRADED

        self._update_telemetry_residuals()
        return self.get_state()

    def _update_telemetry_residuals(self) -> None:
        """
        Computes GPS reading with noise + bias, and computes residual against inertial prediction.
        """
        # Controlled pseudo-random noise for reproducibility
        noise_x = self._rng.uniform(-0.15, 0.15)
        noise_y = self._rng.uniform(-0.15, 0.15)

        if self.gps_fault_active:
            # GPS corrupted by directional bias
            self.gps_x = self.x + self.gps_bias + noise_x
            self.gps_y = self.y + (self.gps_bias * 0.7) + noise_y
        else:
            self.gps_x = self.x + noise_x
            self.gps_y = self.y + noise_y

        # Residual is euclidean divergence between GPS and inertial dead-reckoning
        dx = self.gps_x - self.pred_x
        dy = self.gps_y - self.pred_y
        self.residual = round(math.sqrt(dx * dx + dy * dy), 2)

        # Normalized anomaly score [0.0 - 1.0] using sigmoid-like curve
        # A residual of 5m produces ~0.6, 10m+ produces >0.9
        self.anomaly_score = round(min(1.0, 1.0 - math.exp(-self.residual / 5.5)), 3)

        # Keep heading synchronized
        if abs(self.vx) > 0.01 or abs(self.vy) > 0.01:
            self.heading = round(math.atan2(self.vy, self.vx), 3)

    def apply_action(self, action_id: str) -> Tuple[bool, str]:
        """
        Authoritative application mutation. Mutates simulator state strictly
        through validated actions.
        """
        normalized = action_id.lower().strip()
        if normalized in ("switch_to_inertial", "switch_inertial"):
            self.navigation_mode = NavigationMode.INERTIAL
            # When switching to inertial, drone ignores corrupt GPS
            # IMU trust stays high, GPS trust remains low
            self.mission_status = MissionStatus.DEGRADED
            return True, "Navigation switched to INERTIAL dead-reckoning mode."
        elif normalized in ("safe_mode", "enter_safe_mode"):
            self.navigation_mode = NavigationMode.SAFE_MODE
            self.mission_status = MissionStatus.RECOVERED
            return True, "Vehicle transitioned to SAFE_MODE (controlled hover / station keep)."
        elif normalized in ("continue_gps", "continue_gps_assisted"):
            self.navigation_mode = NavigationMode.GPS_ASSISTED
            return True, "Maintained GPS_ASSISTED navigation mode."
        else:
            return False, f"Unknown action: '{action_id}'."

    def get_state(self) -> SystemState:
        """Returns the canonical SystemState object for API and agent inspection."""
        return SystemState(
            time=round(self.time, 1),
            position=Position(x=round(self.x, 2), y=round(self.y, 2)),
            velocity=Velocity(x=round(self.vx, 2), y=round(self.vy, 2)),
            navigation_mode=self.navigation_mode,
            gps_trust=round(self.gps_trust, 2),
            imu_trust=round(self.imu_trust, 2),
            mission_progress=round(self.mission_progress, 2),
            mission_status=self.mission_status,
            predicted_position=Position(x=round(self.pred_x, 2), y=round(self.pred_y, 2)),
            gps_position=Position(x=round(self.gps_x, 2), y=round(self.gps_y, 2)),
            heading=self.heading,
            residual=self.residual,
            anomaly_score=self.anomaly_score,
            gps_bias=round(self.gps_bias, 2),
            gps_fault_active=self.gps_fault_active,
            energy=round(self.energy, 1),
            communication_health=round(self.communication_health, 2),
        )
