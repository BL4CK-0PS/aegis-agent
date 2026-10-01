"""
Tests for DroneSimulator and Kinematic Telemetry
"""

import pytest
from app.core.models import MissionStatus, NavigationMode
from app.core.simulator import DroneSimulator


def test_nominal_simulation_progression():
    sim = DroneSimulator(seed=42)
    initial_state = sim.get_state()

    assert initial_state.navigation_mode == NavigationMode.GPS_ASSISTED
    assert initial_state.mission_status == MissionStatus.NOMINAL
    assert initial_state.gps_trust >= 0.95
    assert initial_state.imu_trust >= 0.90
    assert initial_state.residual < 1.0
    assert initial_state.anomaly_score < 0.2

    # Advance 3 ticks
    for _ in range(3):
        sim.tick()

    state = sim.get_state()
    assert state.time == 3.0
    assert state.position.x > initial_state.position.x
    assert state.residual < 1.5
    assert state.mission_status == MissionStatus.NOMINAL


def test_gps_integrity_fault_injection():
    sim = DroneSimulator(seed=42)
    sim.inject_gps_fault(initial_bias=6.0)

    state = sim.get_state()
    assert state.gps_fault_active is True
    assert state.gps_bias >= 6.0
    assert state.residual > 4.0
    assert state.anomaly_score > 0.5
    assert state.mission_status in (MissionStatus.DEGRADED, MissionStatus.CRITICAL)

    # Subsequent ticks increase bias and further degrade trust
    initial_residual = state.residual
    sim.tick()
    sim.tick()

    updated_state = sim.get_state()
    assert updated_state.residual > initial_residual
    assert updated_state.gps_trust < state.gps_trust
    assert updated_state.anomaly_score >= state.anomaly_score


def test_simulator_reset():
    sim = DroneSimulator(seed=42)
    sim.inject_gps_fault(initial_bias=8.0)
    for _ in range(4):
        sim.tick()

    assert sim.gps_fault_active is True

    sim.reset(seed=42)
    state = sim.get_state()

    assert state.time == 0.0
    assert state.gps_fault_active is False
    assert state.gps_bias == 0.0
    assert state.mission_status == MissionStatus.NOMINAL
    assert state.navigation_mode == NavigationMode.GPS_ASSISTED


def test_simulator_action_application():
    sim = DroneSimulator(seed=42)
    sim.inject_gps_fault()

    success, msg = sim.apply_action("switch_inertial")
    assert success is True
    assert sim.navigation_mode == NavigationMode.INERTIAL

    success, msg = sim.apply_action("safe_mode")
    assert success is True
    assert sim.navigation_mode == NavigationMode.SAFE_MODE

    # Ticking in safe mode decelerates drone
    sim.tick()
    state = sim.get_state()
    assert abs(state.velocity.x) < 3.0
    assert state.mission_status == MissionStatus.RECOVERED
