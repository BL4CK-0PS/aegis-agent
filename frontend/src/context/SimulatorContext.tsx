import { createContext, useState, useEffect, useRef, useCallback } from 'react';
import type { ReactNode } from 'react';
import type {
  DroneState,
  AgentEvent,
  Evidence,
  Hypothesis,
  CandidateAction,
  VerificationResult,
  LifecyclePhase,
  CapabilityImpact,
  MissionImpact,
  DependencyGraph,
  SimulationResult,
} from '../types';
import {
  fetchState,
  fetchDependencyGraph,
  fetchMissionImpact,
  authorizeAction,
  simulateAction as apiSimulateAction,
  mapSystemStateToDroneState,
  runDemo,
  resetDemo as apiResetDemo,
  createDemoWebSocket,
} from '../api';

interface ActiveExecutionInfo {
  action: string;
  status: 'READY' | 'EXECUTING' | 'COMPLETE' | 'FAILED';
  started?: string;
  completed?: string;
  result?: string;
}

interface SimulatorContextType {
  state: DroneState;
  events: AgentEvent[];
  evidence: Evidence[];
  hypotheses: Hypothesis[];
  actions: CandidateAction[];
  verification: VerificationResult | null;
  authRequiredAction: CandidateAction | null;
  lifecyclePhase: LifecyclePhase;
  capabilityImpacts: CapabilityImpact[];
  missionImpact: MissionImpact | null;
  dependencyGraph: DependencyGraph | null;
  replanCount: number;
  isExecuting: boolean;
  error: string | null;
  activeExecution: ActiveExecutionInfo | null;
  runIncident: () => Promise<void>;
  resetDemo: () => Promise<void>;
  approveAction: () => Promise<void>;
  rejectAction: () => void;
  simulateAction: (actionId: string) => Promise<SimulationResult | null>;
  clearError: () => void;
}

const defaultState: DroneState = {
  time: 0,
  position: { x: 100, y: 50 },
  velocity: { x: 8, y: 4 },
  altitude: 120,
  heading: 0.46,
  navigation_mode: 'GPS_ASSISTED',
  gps_trust: 0.98,
  imu_trust: 0.95,
  barometer_trust: 0.95,
  mission_progress: 10,
  mission_status: 'NORMAL',
  mission_risk: 'LOW',
  residual: 0.0,
  anomaly_score: 0.0,
  energy: 100,
};

const defaultImpacts: CapabilityImpact[] = [
  { name: 'Position Estimation', level: 'NOMINAL' },
  { name: 'Navigation Guidance', level: 'NOMINAL' },
  { name: 'Route Following', level: 'NOMINAL' },
  { name: 'Mission Progress', level: 'NOMINAL' },
];

export const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

export function SimulatorProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DroneState>(defaultState);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [actions, setActions] = useState<CandidateAction[]>([]);
  const [authRequiredAction, setAuthRequiredAction] = useState<CandidateAction | null>(null);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [lifecyclePhase, setLifecyclePhase] = useState<LifecyclePhase>('NORMAL');
  const [capabilityImpacts, setCapabilityImpacts] = useState<CapabilityImpact[]>(defaultImpacts);
  const [missionImpact, setMissionImpact] = useState<MissionImpact | null>(null);
  const [dependencyGraph, setDependencyGraph] = useState<DependencyGraph | null>(null);
  const [replanCount, setReplanCount] = useState<number>(0);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeExecution, setActiveExecution] = useState<ActiveExecutionInfo | null>(null);

  const isRunningRef = useRef(false);
  const runIdRef = useRef(0);

  // Background polling for live simulator telemetry (pauses during active demonstration animation)
  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      if (isRunningRef.current) return;
      try {
        const live = await fetchState();
        if (isMounted && !isRunningRef.current) {
          const mapped = mapSystemStateToDroneState(live);
          setState(prev => ({
            ...mapped,
            barometer_trust: prev.barometer_trust ?? 0.95,
          }));
        }
      } catch (err: any) {
        console.debug('Telemetry polling inactive:', err.message);
      }
    };

    poll();
    const interval = setInterval(poll, 1200);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Initial load of nominal baseline graph & impact
  useEffect(() => {
    let isMounted = true;
    const loadBaselines = async () => {
      try {
        const [graphData, impactData] = await Promise.all([
          fetchDependencyGraph().catch(() => null),
          fetchMissionImpact().catch(() => null),
        ]);

        if (!isMounted) return;
        if (graphData) setDependencyGraph(graphData);
        if (impactData) setMissionImpact(impactData);
      } catch (err: any) {
        console.debug('Initial baseline load notice:', err.message);
      }
    };

    loadBaselines();
    return () => {
      isMounted = false;
    };
  }, []);

  const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

  const clearError = useCallback(() => setError(null), []);

  /**
   * Reset demonstration and return system to clean nominal state
   */
  const resetDemo = async () => {
    runIdRef.current++;
    isRunningRef.current = false;
    setIsExecuting(true);
    setError(null);
    try {
      const res = await apiResetDemo();
      setEvents([]);
      setEvidence([]);
      setHypotheses([]);
      setActions([]);
      setAuthRequiredAction(null);
      setVerification(null);
      setActiveExecution(null);
      setReplanCount(0);
      setLifecyclePhase('NORMAL');
      setCapabilityImpacts(defaultImpacts);
      setMissionImpact(null);
      if (res && res.state) {
        setState(mapSystemStateToDroneState(res.state as any));
      } else {
        setState(defaultState);
      }
    } catch (err: any) {
      console.error('Reset error:', err);
      setError(err.message || 'Failed to reset simulation');
    } finally {
      setIsExecuting(false);
    }
  };

  /**
   * One-Button End-to-End Orchestrated Incident Demonstration
   * Coordinates the full canonical decision cycle:
   * NORMAL -> INCIDENT -> INVESTIGATING -> ANALYZING -> SIMULATING -> POLICY_CHECK ->
   * AUTHORIZATION -> EXECUTING -> VERIFYING (Failed) -> REPLANNING -> SIMULATING ->
   * POLICY_CHECK -> EXECUTING -> VERIFYING (Success) -> RECOVERING -> COMPLETED
   */
  const runIncident = async () => {
    if (isRunningRef.current) return;
    isRunningRef.current = true;
    setIsExecuting(true);
    setError(null);
    const currentRunId = ++runIdRef.current;

    // Optional WebSocket stream listener to monitor backend live events
    let ws: WebSocket | null = null;
    try {
      ws = createDemoWebSocket((eventData) => {
        console.debug('[AEGIS WS]', eventData.event, eventData.phase);
      });
    } catch (wsErr) {
      console.debug('WS stream initialized in hybrid mode:', wsErr);
    }

    try {
      // Step 0: Clean baseline
      setLifecyclePhase('NORMAL');
      setEvents([]);
      setEvidence([]);
      setHypotheses([]);
      setActions([]);
      setAuthRequiredAction(null);
      setVerification(null);
      setCapabilityImpacts(defaultImpacts);
      setReplanCount(0);
      setActiveExecution(null);

      // Trigger authoritative backend end-to-end orchestration
      const demoResult = await runDemo(true);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 1: INCIDENT DETECTED ----
      setLifecyclePhase('INCIDENT');
      const bias = demoResult.incident?.bias ?? 6.5;
      const initRes = demoResult.incident?.initial_residual ?? 7.9;
      setState(prev => ({
        ...prev,
        mission_status: 'DEGRADED',
        gps_trust: 0.45,
        residual: initRes,
        gps_bias: bias,
        anomaly_score: 0.78,
        gps_fault_active: true,
      }));

      setEvents([
        {
          step: 1,
          tool: 'inject_gps_fault',
          status: 'completed',
          summary: `GPS integrity fault injected (bias=${bias}m). Positional residual divergence: ${initRes.toFixed(2)}m.`,
          subdetails: [
            'Pseudorange inconsistency across multi-constellation receiver',
            `Positional residual divergence: ${initRes.toFixed(2)}m`,
          ],
        },
      ]);

      await delay(500);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 2: INVESTIGATION ----
      setLifecyclePhase('INVESTIGATING');
      setEvents(prev => [
        ...prev,
        {
          step: 2,
          tool: 'get_system_state',
          status: 'completed',
          summary: 'Retrieved drone telemetry: mode=GPS_ASSISTED, status=DEGRADED.',
          subdetails: ['Mode: GPS_ASSISTED', 'Status: DEGRADED', 'Velocity: [8.0, 4.0] m/s'],
        },
        {
          step: 3,
          tool: 'get_observations',
          status: 'completed',
          summary: `Observed sensor divergence: residual=${initRes.toFixed(1)}m, anomaly_score=0.78.`,
          subdetails: [
            `GPS residual divergence: ${initRes.toFixed(1)}m`,
            'Anomaly score: 0.78',
          ],
        },
        {
          step: 4,
          tool: 'get_trust',
          status: 'completed',
          summary: 'Calibrated statistical trust: GPS=0.45, IMU=0.95.',
          subdetails: ['GPS trust: 45%', 'IMU trust: 95%'],
        },
      ]);

      await delay(550);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 3: ANALYZING (Evidence, Hypotheses, Impact, Graph) ----
      setLifecyclePhase('ANALYZING');

      // Populate Evidence
      const evList: Evidence[] = [
        {
          id: 'E01',
          source: 'Sensor Fusion',
          metric: 'GPS-Inertial residual divergence',
          value: `${initRes.toFixed(1)}m`,
          confidence: 0.98,
          description: 'Measurable position discrepancy between satellite fix and dead-reckoning',
          severity: 'CRITICAL',
          relationship: 'Supports H1 (GPS degradation)',
        },
        {
          id: 'E02',
          source: 'Anomaly Detector',
          metric: 'Sensor Anomaly Score',
          value: '0.78',
          confidence: 0.94,
          description: 'Multivariate statistical outlier metric exceeds nominal noise threshold',
          severity: 'HIGH',
          relationship: 'Supports H1 (GPS degradation)',
        },
        {
          id: 'E03',
          source: 'Trust Engine',
          metric: 'Calibrated GPS Trust',
          value: '0.45',
          confidence: 0.95,
          description: 'Statistical integrity score for satellite navigation solution degraded',
          severity: 'CRITICAL',
          relationship: 'Supports H1 (GPS degradation)',
        },
        {
          id: 'E04',
          source: 'IMU Diagnostic',
          metric: 'IMU kinematic consistency',
          value: '0.95',
          confidence: 0.96,
          description: 'Triple-axis accelerometers and rate gyros satisfy kinematic constraints',
          severity: 'NOMINAL',
          relationship: 'Contradicts H3 (IMU failure)',
        },
      ];
      setEvidence(evList);

      // Populate Hypotheses
      const hypList: Hypothesis[] = Array.isArray(demoResult.hypotheses) && demoResult.hypotheses.length > 0
        ? demoResult.hypotheses.map((h: any, idx: number) => ({
            id: h.id || `H${idx + 1}`,
            description: h.title || h.description || 'Hypothesis',
            confidence: h.likelihood ?? h.confidence ?? 0.5,
            likelihood: h.likelihood ?? h.confidence,
            explanation: h.explanation,
            supporting_evidence: h.supporting_evidence,
            supportingEvidence: idx === 0 ? 3 : 1,
            contradictingEvidence: idx === 0 ? 0 : 2,
          }))
        : [
            {
              id: 'H1',
              description: 'GPS Integrity Degradation',
              confidence: 0.94,
              likelihood: 0.94,
              explanation: 'Measurable satellite pseudorange bias produces divergence against inertial propagation.',
              supportingEvidence: 3,
              contradictingEvidence: 0,
            },
            {
              id: 'H2',
              description: 'Severe Multipath / Atmospheric Distortion',
              confidence: 0.05,
              likelihood: 0.05,
              explanation: 'Transient ionospheric or urban canyon reflection anomaly.',
              supportingEvidence: 1,
              contradictingEvidence: 2,
            },
            {
              id: 'H3',
              description: 'IMU Sensor Failure / Drift',
              confidence: 0.01,
              likelihood: 0.01,
              explanation: 'Uncalibrated gyro bias divergence.',
              supportingEvidence: 0,
              contradictingEvidence: 3,
            },
          ];
      setHypotheses(hypList);

      // Populate Mission Impact
      const impact: MissionImpact = (demoResult.mission_impact as any) || {
        operational_risk: 0.85,
        risk_level: 'CRITICAL',
        mission_status: 'DEGRADED',
        affected_capabilities: ['Position Estimation', 'Navigation Guidance', 'Route Following', 'Mission Progress'],
        time_to_critical_seconds: 45,
        recommendation_urgency: 'IMMEDIATE',
        summary: 'Primary positioning channel compromised. Trajectory deviation imminent.',
      };
      setMissionImpact(impact);
      setCapabilityImpacts([
        { name: 'Position Estimation', level: 'CRITICAL' },
        { name: 'Navigation Guidance', level: 'HIGH' },
        { name: 'Route Following', level: 'HIGH' },
        { name: 'Mission Progress', level: 'MEDIUM' },
      ]);

      if (demoResult.dependency_graph) {
        setDependencyGraph(demoResult.dependency_graph as any);
      }

      setEvents(prev => [
        ...prev,
        {
          step: 5,
          tool: 'generate_hypotheses',
          status: 'completed',
          summary: 'Synthesized competing hypotheses. Primary lead: GPS Integrity Degradation (Confidence: 94%).',
          subdetails: [
            'H1: GPS integrity degradation (Likelihood: 94%)',
            'H2: Severe Atmospheric / Multipath Distortion (Likelihood: 5%)',
          ],
        },
        {
          step: 6,
          tool: 'get_mission_impact',
          status: 'completed',
          summary: 'Evaluated mission impact: risk=0.85, urgency=IMMEDIATE.',
          subdetails: ['Operational risk: CRITICAL (0.85)', 'Urgency: IMMEDIATE'],
        },
        {
          step: 7,
          tool: 'get_dependency_graph',
          status: 'completed',
          summary: 'Mapped subsystem dependency graph (6 nodes).',
          subdetails: ['Degradation propagation: GPS_RECEIVER → POSITION_ESTIMATION → NAVIGATION → MISSION_EXECUTION'],
        },
      ]);

      await delay(600);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 4: PLANNING & SIMULATION ----
      setLifecyclePhase('SIMULATING');

      const candidateActions: CandidateAction[] = [
        {
          id: 'SWITCH_TO_IMU_ONLY',
          name: 'Switch to Inertial Navigation',
          description: 'Isolate corrupted GPS signal and engage IMU dead-reckoning filter.',
          risk: 'MEDIUM',
          risk_num: 0.42,
          mission_continuity: 71,
          success_rate: 71,
          expected_delay: '+18 sec',
          policy_status: 'REQUIRES_AUTHORIZATION',
          recommended: true,
          simulation: {
            action_id: 'SWITCH_TO_IMU_ONLY',
            feasible: true,
            predicted_risk: 0.42,
            mission_success_probability: 0.71,
            estimated_delay: 18,
            mission_continuity: 0.71,
            predicted_residual: 3.6,
            predicted_mission_outcome: 'Inertial flight continues with steady accumulation of unmodeled drift',
            recommendation: 'Viable with Human Authorization',
            state_delta: {
              navigation_mode: 'INERTIAL',
              gps_isolated: true,
            },
          },
        },
        {
          id: 'REQUEST_GPS_REACQUISITION',
          name: 'Continue GPS-assisted Navigation',
          description: 'Maintain current GPS tracking without sensor reconfiguration.',
          risk: 'CRITICAL',
          risk_num: 0.88,
          mission_continuity: 35,
          success_rate: 8,
          expected_delay: '+2.4 min',
          policy_status: 'DENIED',
          recommended: false,
          simulation: {
            action_id: 'REQUEST_GPS_REACQUISITION',
            feasible: false,
            predicted_risk: 0.95,
            mission_success_probability: 0.08,
            estimated_delay: 144,
            mission_continuity: 0.35,
            predicted_residual: 12.8,
            predicted_mission_outcome: 'Catastrophic waypoint departure due to degraded satellite integrity',
            recommendation: 'DENIED by Autonomous Safety Policy',
            state_delta: {
              navigation_mode: 'GPS_ASSISTED',
            },
          },
        },
        {
          id: 'ENTER_SAFE_MODE',
          name: 'Enter Safe Mode',
          description: 'Arrest forward velocity into stationary hover / controlled emergency descent.',
          risk: 'LOW',
          risk_num: 0.08,
          mission_continuity: 0,
          success_rate: 99,
          expected_delay: 'Stationary',
          policy_status: 'ALLOWED',
          recommended: false,
          simulation: {
            action_id: 'ENTER_SAFE_MODE',
            feasible: true,
            predicted_risk: 0.08,
            mission_success_probability: 0.99,
            estimated_delay: 0,
            mission_continuity: 0.0,
            predicted_residual: 0.08,
            predicted_mission_outcome: 'Vehicle safely stabilized in stationary station-keep hover',
            recommendation: 'Autonomous failsafe approved',
            state_delta: {
              navigation_mode: 'SAFE_MODE',
              velocity: { x: 0, y: 0 },
            },
          },
        },
      ];
      setActions(candidateActions);

      setEvents(prev => [
        ...prev,
        {
          step: 8,
          tool: 'generate_actions',
          status: 'completed',
          summary: 'Generated 3 candidate response actions tailored to degraded navigation state.',
          subdetails: ['Formulated: SWITCH_TO_IMU_ONLY, REQUEST_GPS_REACQUISITION, ENTER_SAFE_MODE'],
        },
        {
          step: 9,
          tool: 'simulate_action',
          status: 'completed',
          summary: "Simulated 'SWITCH_TO_IMU_ONLY': Predicted Risk=0.42, Delay=18s.",
          subdetails: ['Predicted risk: 42%', 'Predicted residual: 3.6m'],
        },
        {
          step: 10,
          tool: 'simulate_action',
          status: 'completed',
          summary: "Simulated 'REQUEST_GPS_REACQUISITION': Predicted Risk=0.95, Continuity=0.35.",
          subdetails: ['Predicted risk: 95% (CRITICAL)', 'Risk threshold exceeded'],
        },
      ]);

      await delay(600);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 5: POLICY EVALUATION & AUTHORIZATION ----
      setLifecyclePhase('POLICY_CHECK');
      setEvents(prev => [
        ...prev,
        {
          step: 11,
          tool: 'evaluate_policy',
          status: 'completed',
          summary: "Policy evaluation for 'SWITCH_TO_IMU_ONLY': REQUIRES_AUTHORIZATION (Requires Auth: true).",
          subdetails: ['Rule POL-02: Sensor degradation switch requires human confirmation', 'Authorization required: YES'],
        },
      ]);

      await delay(500);
      if (runIdRef.current !== currentRunId) return;

      setLifecyclePhase('AUTHORIZATION');
      setEvents(prev => [
        ...prev,
        {
          step: 12,
          tool: 'request_authorization',
          status: 'completed',
          summary: "Operator granted Human-in-the-Loop authorization for 'SWITCH_TO_IMU_ONLY'.",
          subdetails: ['Authorization approved: True', 'Actuator gate unlocked'],
        },
      ]);

      await delay(500);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 6: EXECUTION (Attempt 1: SWITCH_TO_IMU_ONLY) ----
      setLifecyclePhase('EXECUTING');
      setActiveExecution({
        action: 'SWITCH_TO_IMU_ONLY',
        status: 'COMPLETE',
        completed: new Date().toLocaleTimeString(),
        result: 'Actuator transition: INERTIAL_DEAD_RECKONING',
      });
      setState(prev => ({
        ...prev,
        navigation_mode: 'INERTIAL',
      }));

      setEvents(prev => [
        ...prev,
        {
          step: 13,
          tool: 'execute_action',
          status: 'completed',
          summary: "Authoritative execution of 'SWITCH_TO_IMU_ONLY': Status=SUCCESS, Mode=INERTIAL.",
          subdetails: ['Actuator switched navigation mode to INERTIAL', 'GPS isolated from filter'],
        },
      ]);

      await delay(600);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 7: VERIFICATION (Attempt 1: Intentional Failure) ----
      setLifecyclePhase('VERIFYING');
      setVerification({
        verified: false,
        reason: 'Navigation residual (3.60m) exceeds tolerance (2.00m). Unmodeled dead-reckoning drift detected.',
        expected: 'Navigation residual < 2.0m',
        actual: 'Navigation residual = 3.60m (Drift detected)',
        position_residual: 3.60,
        mission_risk: 'CRITICAL',
        status: 'failed',
        next_action_required: true,
      });

      setEvents(prev => [
        ...prev,
        {
          step: 14,
          tool: 'verify_action',
          status: 'failed',
          summary: 'Verification FAILED: Navigation residual (3.60m) exceeds tolerance (2.00m). Unmodeled dead-reckoning drift detected.',
          subdetails: [
            'Residual check: FAILED (3.60m > 2.00m)',
            'Confidence check: FAILED (0.58 < 0.80)',
            'Dynamic replanning mandate triggered',
          ],
        },
      ]);

      await delay(700);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 8: DYNAMIC REPLANNING ----
      setLifecyclePhase('REPLANNING');
      setReplanCount(1);
      setActions(prev =>
        prev.map(a => ({
          ...a,
          recommended: a.id === 'ENTER_SAFE_MODE' || a.id === 'safe_mode',
        }))
      );

      setEvents(prev => [
        ...prev,
        {
          step: 15,
          tool: 'replan',
          status: 'completed',
          summary: "Dynamic replanning triggered: Reassessed alternatives. Recommended recovery failsafe: 'ENTER_SAFE_MODE'.",
          subdetails: [
            'Failure RCA: Dead-reckoning drift without optical flow or external reference',
            'Selected fallback candidate: ENTER_SAFE_MODE',
          ],
        },
      ]);

      await delay(600);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 9: SIMULATE & POLICY (Attempt 2: ENTER_SAFE_MODE) ----
      setLifecyclePhase('SIMULATING');
      setEvents(prev => [
        ...prev,
        {
          step: 16,
          tool: 'simulate_action',
          status: 'completed',
          summary: "Simulated recovery failsafe 'ENTER_SAFE_MODE': Predicted Risk=0.08, Success=99%.",
          subdetails: ['Predicted risk: 8%', 'Arrests forward velocity into station-keeping hover'],
        },
      ]);

      await delay(450);
      if (runIdRef.current !== currentRunId) return;

      setLifecyclePhase('POLICY_CHECK');
      setEvents(prev => [
        ...prev,
        {
          step: 17,
          tool: 'evaluate_policy',
          status: 'completed',
          summary: "Policy evaluation for emergency failsafe 'ENTER_SAFE_MODE': ALLOWED (Allowed: True).",
          subdetails: ['Emergency failsafe policy rule POL-01 overrides manual gates'],
        },
      ]);

      await delay(500);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 10: EXECUTION (Attempt 2: ENTER_SAFE_MODE) ----
      setLifecyclePhase('EXECUTING');
      setActiveExecution({
        action: 'ENTER_SAFE_MODE',
        status: 'COMPLETE',
        completed: new Date().toLocaleTimeString(),
        result: 'Actuator transition: SAFE_MODE',
      });
      setState(prev => ({
        ...prev,
        navigation_mode: 'SAFE_MODE',
        velocity: { x: 0, y: 0 },
      }));

      setEvents(prev => [
        ...prev,
        {
          step: 18,
          tool: 'execute_action',
          status: 'completed',
          summary: "Authoritative execution of recovery failsafe 'ENTER_SAFE_MODE': New Mode=SAFE_MODE.",
          subdetails: ['Velocity arrested to 0 m/s', 'Hover station-keep engaged'],
        },
      ]);

      await delay(600);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 11: VERIFICATION (Attempt 2: SUCCESS) ----
      setLifecyclePhase('VERIFYING');
      setVerification({
        verified: true,
        reason: 'Safe mode verified. Hover drift arrested, containment satisfied.',
        expected: 'Stationary hover drift < 0.5m',
        actual: 'Drift = 0.08m (Stable)',
        position_residual: 0.08,
        mission_risk: 'LOW',
        status: 'verified',
        next_action_required: false,
      });

      setEvents(prev => [
        ...prev,
        {
          step: 19,
          tool: 'verify_action',
          status: 'completed',
          summary: 'Verification PASSED: Safe mode verified. Drift = 0.08m (Stable).',
          subdetails: [
            'Residual drift: 0.08m (< 0.5m limit)',
            'Velocity magnitude: 0.00 m/s',
            'Safety containment invariants satisfied',
          ],
        },
      ]);

      await delay(500);
      if (runIdRef.current !== currentRunId) return;

      // ---- STAGE 12: RECOVERY & COMPLETION ----
      setLifecyclePhase('RECOVERING');
      setState(prev => ({
        ...prev,
        mission_status: 'SAFE',
        navigation_mode: 'SAFE_MODE',
        residual: 0.08,
        anomaly_score: 0.05,
        velocity: { x: 0, y: 0 },
      }));
      setCapabilityImpacts([
        { name: 'Position Estimation', level: 'NOMINAL' },
        { name: 'Navigation Guidance', level: 'NOMINAL' },
        { name: 'Route Following', level: 'NOMINAL' },
        { name: 'Mission Progress', level: 'NOMINAL' },
      ]);

      await delay(400);
      setLifecyclePhase('COMPLETED');
    } catch (err: any) {
      console.error('Error during incident demonstration:', err);
      setError(err.message || 'Incident demonstration encountered an API error.');
      setLifecyclePhase('FAILED');
    } finally {
      if (ws) {
        try {
          ws.close();
        } catch {
          // ignore
        }
      }
      isRunningRef.current = false;
      setIsExecuting(false);
    }
  };

  /**
   * Operator Human-in-the-Loop approval
   */
  const approveAction = async () => {
    if (!authRequiredAction) return;
    const actionId = authRequiredAction.id;
    setAuthRequiredAction(null);
    setLifecyclePhase('AUTHORIZED');
    setError(null);

    isRunningRef.current = true;
    setIsExecuting(true);

    setActiveExecution({
      action: actionId,
      status: 'EXECUTING',
      started: new Date().toLocaleTimeString(),
    });

    try {
      await delay(400);
      await authorizeAction(actionId, false);
      setActiveExecution({
        action: actionId,
        status: 'COMPLETE',
        completed: new Date().toLocaleTimeString(),
        result: 'Manual intervention authorized by operator',
      });
    } catch (err: any) {
      console.error('Error approving action:', err);
      setError(err.message || 'Error executing authorized action.');
    } finally {
      isRunningRef.current = false;
      setIsExecuting(false);
    }
  };

  /**
   * Operator rejection
   */
  const rejectAction = () => {
    setAuthRequiredAction(null);
    setActiveExecution({
      action: 'SWITCH_TO_IMU_ONLY',
      status: 'FAILED',
      result: 'Intervention declined by Human Operator.',
    });
    setEvents(prev => [
      ...prev,
      {
        step: prev.length + 1,
        tool: 'human_authorization',
        status: 'failed',
        summary: 'Action authorization declined by Human-in-the-Loop operator.',
        subdetails: ['Operator declined intervention; maintaining failsafe hold'],
      },
    ]);
  };

  /**
   * Counterfactual action simulation triggered from Candidate Actions UI
   */
  const simulateAction = async (actionId: string): Promise<SimulationResult | null> => {
    try {
      setError(null);
      const result = await apiSimulateAction(actionId);
      setActions(prev =>
        prev.map(a => (a.id === actionId ? { ...a, simulation: result } : a))
      );
      return result;
    } catch (err: any) {
      console.error(`Simulation failed for ${actionId}:`, err);
      setError(err.message || `Simulation failed for action ${actionId}`);
      return null;
    }
  };

  return (
    <SimulatorContext.Provider
      value={{
        state,
        events,
        evidence,
        hypotheses,
        actions,
        verification,
        authRequiredAction,
        lifecyclePhase,
        capabilityImpacts,
        missionImpact,
        dependencyGraph,
        replanCount,
        isExecuting,
        error,
        activeExecution,
        runIncident,
        resetDemo,
        approveAction,
        rejectAction,
        simulateAction,
        clearError,
      }}
    >
      {children}
    </SimulatorContext.Provider>
  );
}

export { useSimulator } from './useSimulator';
