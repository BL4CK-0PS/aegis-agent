import { createContext, useContext, useState, useEffect, useRef } from 'react';
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
  RiskLevel,
} from '../types/simulator';
import {
  fetchState,
  resetSystem,
  injectGpsFault,
  agentStep,
  authorizeAction,
  mapBackendToDroneState,
  type BackendAgentEvent,
} from '../services/api';

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
  runIncident: () => Promise<void>;
  approveAction: () => Promise<void>;
  rejectAction: () => void;
}

const defaultState: DroneState = {
  time: 0,
  position: { x: 100, y: 50 },
  velocity: { x: 8, y: 4 },
  navigation_mode: 'GPS_ASSISTED',
  gps_trust: 0.98,
  imu_trust: 0.95,
  barometer_trust: 0.95,
  mission_progress: 10,
  mission_status: 'NORMAL',
  mission_risk: 'LOW',
  residual: 0.0,
  anomaly_score: 0.0,
};

const defaultImpacts: CapabilityImpact[] = [
  { name: 'Position Estimation', level: 'NOMINAL' },
  { name: 'Navigation Guidance', level: 'NOMINAL' },
  { name: 'Route Following', level: 'NOMINAL' },
  { name: 'Mission Progress', level: 'NOMINAL' },
];

const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

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

  const isRunningRef = useRef(false);
  const runIdRef = useRef(0);

  // Poll backend state for live telemetry
  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      try {
        const live = await fetchState();
        if (isMounted) {
          const mapped = mapBackendToDroneState(live);
          setState(prev => ({
            ...mapped,
            barometer_trust: prev.barometer_trust ?? 0.95,
            residual: live.residual ?? prev.residual,
            anomaly_score: live.anomaly_score ?? prev.anomaly_score,
          }));
        }
      } catch (err) {
        console.warn('Telemetry polling error:', err);
      }
    };

    poll();
    const interval = setInterval(poll, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

  const processEventArtifacts = (backendEvents: BackendAgentEvent[]) => {
    // Transform events with rich multi-line findings
    const mappedEvents: AgentEvent[] = backendEvents.map(e => {
      let subdetails: string[] = [];
      const tool = e.tool;
      const details = e.details || {};

      if (tool === 'get_system_state') {
        subdetails = ['Mission state retrieved', 'Active mode: GPS_ASSISTED'];
      } else if (tool === 'get_observations') {
        const res = details.residual ?? 8.4;
        subdetails = [`GPS residual: ${typeof res === 'number' ? res.toFixed(1) : res}m`, 'Position anomaly detected'];
      } else if (tool === 'get_trust') {
        const gpsT = details.gps_trust ?? 0.31;
        const imuT = details.imu_trust ?? 0.95;
        subdetails = [`GPS trust: ${(gpsT * 100).toFixed(0)}% ↓`, `IMU trust: ${(imuT * 100).toFixed(0)}%`];
      } else if (tool === 'generate_hypotheses') {
        subdetails = ['GPS integrity degradation: 91%', 'Sensor noise: 6%'];
      } else if (tool === 'get_mission_impact') {
        subdetails = ['Navigation capability affected', 'Mission risk: HIGH'];
      } else if (tool === 'generate_actions') {
        subdetails = ['Formulated 3 candidate recovery actions'];
      } else if (tool === 'simulate_action') {
        const actId = details.action_id || '';
        if (actId === 'continue_gps') {
          subdetails = ['Simulate Continue GPS: Risk 92% (Disallowed)'];
        } else {
          subdetails = ['Simulate Inertial switch: Risk 42%, Success 71%'];
        }
      } else if (tool === 'evaluate_policy') {
        subdetails = ['Policy Gate: Human authorization required'];
      } else if (tool === 'execute_action') {
        const act = details.action_id || 'action';
        subdetails = [`Authoritative execution: ${act}`];
      } else if (tool === 'verify_action') {
        const ver = details.verified;
        if (ver === false) {
          subdetails = ['Navigation confidence below safety threshold', 'Inertial drift detected'];
        } else {
          subdetails = ['Recovery successful within safety margins', 'Stationary hover established'];
        }
      } else if (tool === 'replan') {
        subdetails = ['Dynamic replan: Switching to SAFE_MODE failsafe'];
      }

      return {
        step: e.step,
        tool: e.tool,
        status: e.status,
        summary: e.summary,
        details: e.details,
        subdetails,
      };
    });
    setEvents(mappedEvents);

    // Scan for lifecycle updates & domain models
    for (const e of backendEvents) {
      if (e.tool === 'get_system_state' || e.tool === 'get_observations') {
        setLifecyclePhase('INVESTIGATING');
      }

      if (e.tool === 'get_trust') {
        setLifecyclePhase('EVIDENCE_GATHERED');
      }

      if (e.tool === 'generate_hypotheses' && e.details) {
        setLifecyclePhase('HYPOTHESIS_FORMED');
        if (Array.isArray(e.details.evidence)) {
          setEvidence(
            e.details.evidence.map((ev: any) => ({
              id: ev.id,
              metric: ev.metric || 'Telemetry Metric',
              value: ev.value || 'N/A',
              confidence: ev.severity === 'NOMINAL' ? 0.96 : 0.94,
              description: ev.interpretation || ev.metric,
              source: ev.source || 'Sensors / Trust Engine',
              severity: ev.severity || 'MEDIUM',
            }))
          );
        }

        if (Array.isArray(e.details.hypotheses)) {
          setHypotheses(
            e.details.hypotheses.map((h: any, idx: number) => ({
              id: h.id || `H${idx + 1}`,
              description: h.title || h.name || 'Hypothesis',
              confidence: h.likelihood ?? h.confidence ?? 0.5,
              supportingEvidence: idx === 0 ? 4 : 1,
              contradictingEvidence: idx === 0 ? 0 : 2,
            }))
          );
        }
      }

      if (e.tool === 'get_mission_impact') {
        setCapabilityImpacts([
          { name: 'Position Estimation', level: 'HIGH' },
          { name: 'Navigation Guidance', level: 'HIGH' },
          { name: 'Route Following', level: 'MEDIUM' },
          { name: 'Mission Progress', level: 'MEDIUM' },
        ]);
      }

      if (e.tool === 'generate_actions' && e.details && Array.isArray(e.details.actions)) {
        setLifecyclePhase('ACTION_SIMULATED');
        setActions(
          e.details.actions.map((act: any) => {
            const riskNum = typeof act.risk === 'number' ? act.risk : 0.5;
            const riskLevel: RiskLevel = riskNum >= 0.6 ? 'HIGH' : riskNum >= 0.25 ? 'MEDIUM' : 'LOW';
            const rawCont = typeof act.mission_continuity === 'number' ? act.mission_continuity : 0.5;
            const continuity = Math.round(rawCont <= 1 ? rawCont * 100 : rawCont);
            return {
              id: act.id,
              name: act.name || act.id,
              risk: riskLevel,
              mission_continuity: continuity,
              success_rate: act.id === 'switch_inertial' ? 71 : act.id === 'continue_gps' ? 8 : 99,
              expected_delay: act.id === 'switch_inertial' ? '+18 sec' : act.id === 'continue_gps' ? '+2.4 min' : 'Stationary',
              policy_status: act.id === 'switch_inertial' ? 'REQUIRES_AUTH' : act.id === 'continue_gps' ? 'DENIED' : 'ALLOWED',
              recommended: act.id === 'switch_inertial',
            };
          })
        );
      }

      if (e.tool === 'evaluate_policy') {
        setLifecyclePhase('POLICY_CHECK');
      }

      if (e.tool === 'execute_action') {
        setLifecyclePhase('EXECUTED');
      }

      if (e.tool === 'replan') {
        setLifecyclePhase('REPLAN');
        setActions(prev =>
          prev.map(a => ({
            ...a,
            recommended: a.id === 'safe_mode',
          }))
        );
        setVerification(null);
      }

      if (e.tool === 'verify_action' && e.details) {
        const verified = Boolean(e.details.verified);
        if (verified) {
          setLifecyclePhase('SAFE_MODE');
          setCapabilityImpacts([
            { name: 'Position Estimation', level: 'NOMINAL' },
            { name: 'Navigation Guidance', level: 'NOMINAL' },
            { name: 'Route Following', level: 'NOMINAL' },
            { name: 'Mission Progress', level: 'NOMINAL' },
          ]);
        } else {
          setLifecyclePhase('VERIFICATION_FAILED');
        }

        setVerification({
          verified,
          reason: e.details.reason || (verified ? 'Recovery safe mode verified.' : 'Position residual remains above safe threshold.'),
          expected: verified ? 'Stationary hover drift < 0.5m' : 'Navigation residual < 2.0m',
          actual: verified ? 'Drift = 0.08m (Stable)' : `Navigation residual = ${(e.details.residual ?? 7.89).toFixed(2)}m`,
          next_action_required: !verified,
        });
      }
    }
  };

  const runIncident = async () => {
    if (isRunningRef.current) return;
    isRunningRef.current = true;
    const currentRunId = ++runIdRef.current;

    try {
      // 1. Clean Reset
      setLifecyclePhase('NORMAL');
      setEvents([]);
      setEvidence([]);
      setHypotheses([]);
      setActions([]);
      setAuthRequiredAction(null);
      setVerification(null);
      setCapabilityImpacts(defaultImpacts);

      const resetRes = await resetSystem(42);
      setState(mapBackendToDroneState(resetRes.state));

      await delay(1200);
      if (runIdRef.current !== currentRunId) return;

      // 2. Fault Injection
      setLifecyclePhase('INCIDENT_DETECTED');
      const faultRes = await injectGpsFault(6.5);
      setState(mapBackendToDroneState(faultRes.state));

      await delay(1000);
      if (runIdRef.current !== currentRunId) return;

      // 3. Step through agent loop
      let finished = false;
      while (!finished && runIdRef.current === currentRunId) {
        const agentRes = await agentStep(false);
        processEventArtifacts(agentRes.events);

        const liveState = await fetchState();
        setState(mapBackendToDroneState(liveState));

        if (agentRes.waiting_for_authorization) {
          setLifecyclePhase('POLICY_CHECK');
          const pendingId = agentRes.pending_action || 'switch_inertial';
          const matchedAction: CandidateAction = actions.find(a => a.id === pendingId) || {
            id: pendingId,
            name: 'Switch to Inertial Navigation',
            risk: 'MEDIUM',
            mission_continuity: 71,
            success_rate: 71,
            expected_delay: '+18 sec',
            policy_status: 'REQUIRES_AUTH',
            recommended: true,
          };
          setAuthRequiredAction(matchedAction);
          finished = true;
          break;
        }

        if (agentRes.completed) {
          finished = true;
          break;
        }

        await delay(1000);
      }
    } catch (err) {
      console.error('Error running incident:', err);
    } finally {
      isRunningRef.current = false;
    }
  };

  const approveAction = async () => {
    if (!authRequiredAction) return;
    const actionId = authRequiredAction.id;
    setAuthRequiredAction(null);
    setLifecyclePhase('AUTHORIZED');

    const currentRunId = runIdRef.current;
    isRunningRef.current = true;

    // Add operator approval trace event
    setEvents(prev => [
      ...prev,
      {
        step: prev.length + 1,
        tool: 'human_authorization',
        status: 'completed',
        summary: `Operator APPROVED flight intervention: ${actionId}`,
        subdetails: ['Policy authorization granted', 'Proceeding to authoritative actuator execution'],
      },
    ]);

    try {
      await delay(800);
      const authRes = await authorizeAction(actionId, false);
      processEventArtifacts(authRes.events);

      await delay(1000);

      let finished = false;
      while (!finished && runIdRef.current === currentRunId) {
        const agentRes = await agentStep(true);
        processEventArtifacts(agentRes.events);

        const liveState = await fetchState();
        setState(mapBackendToDroneState(liveState));

        if (agentRes.completed) {
          finished = true;
          break;
        }

        await delay(1200);
      }
    } catch (err) {
      console.error('Error approving action:', err);
    } finally {
      isRunningRef.current = false;
    }
  };

  const rejectAction = () => {
    setAuthRequiredAction(null);
    setEvents(prev => [
      ...prev,
      {
        step: prev.length + 1,
        tool: 'human_authorization',
        status: 'failed',
        summary: 'Action authorization declined by Human-in-the-Loop operator.',
        subdetails: ['Intervention aborted by operator command'],
      },
    ]);
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
        runIncident,
        approveAction,
        rejectAction,
      }}
    >
      {children}
    </SimulatorContext.Provider>
  );
}

export function useSimulator() {
  const context = useContext(SimulatorContext);
  if (context === undefined) {
    throw new Error('useSimulator must be used within a SimulatorProvider');
  }
  return context;
}
