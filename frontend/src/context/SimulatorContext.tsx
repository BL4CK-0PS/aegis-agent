import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { DroneState, AgentEvent, Evidence, Hypothesis, CandidateAction, VerificationResult } from '../types/simulator';

interface SimulatorContextType {
  state: DroneState;
  events: AgentEvent[];
  evidence: Evidence[];
  hypotheses: Hypothesis[];
  actions: CandidateAction[];
  verification: VerificationResult | null;
  authRequiredAction: CandidateAction | null;
  runIncident: () => void;
  approveAction: () => void;
  rejectAction: () => void;
}

const defaultState: DroneState = {
  time: 0,
  position: { x: 0, y: 0 },
  velocity: { x: 10, y: 5 },
  navigation_mode: 'GPS_ASSISTED',
  gps_trust: 0.99,
  imu_trust: 0.98,
  mission_progress: 0,
  mission_status: 'NORMAL',
  mission_risk: 'LOW',
};

const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

export function SimulatorProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DroneState>(defaultState);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [actions, setActions] = useState<CandidateAction[]>([]);
  const [authRequiredAction, setAuthRequiredAction] = useState<CandidateAction | null>(null);
  const [verification, setVerification] = useState<VerificationResult | null>(null);

  // Background Tick for Drone Movement
  useEffect(() => {
    const interval = setInterval(() => {
      setState(s => {
        if (s.mission_status === 'CRITICAL') return s;
        return {
          ...s,
          time: s.time + 1,
          position: { x: s.position.x + s.velocity.x * 0.1, y: s.position.y + s.velocity.y * 0.1 },
          mission_progress: Math.min(100, s.mission_progress + 0.5)
        };
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

  const runIncident = async () => {
    // Reset
    setState(defaultState);
    setEvents([]);
    setEvidence([]);
    setHypotheses([]);
    setActions([]);
    setAuthRequiredAction(null);
    setVerification(null);

    await delay(2000);

    // Fault Injection
    setState(s => ({ ...s, mission_status: 'DEGRADED', gps_trust: 0.31, mission_risk: 'HIGH' }));
    
    // Agent Trace
    setEvents([{ step: 1, tool: 'get_system_state', status: 'completed', summary: 'Retrieved degraded state' }]);
    await delay(1000);
    setEvents(prev => [...prev, { step: 2, tool: 'get_observations', status: 'completed', summary: 'GPS residual is 8.4m' }]);
    await delay(1000);
    setEvents(prev => [...prev, { step: 3, tool: 'get_trust', status: 'completed', summary: 'GPS trust decreased to 0.31' }]);
    await delay(1000);
    setEvents(prev => [...prev, { step: 4, tool: 'generate_hypotheses', status: 'completed', summary: 'Generated 3 hypotheses' }]);
    
    // Evidence & Hypotheses
    setEvidence([
      { id: 'E01', description: 'GPS residual: 8.4m', source: 'GPS / IMU comparison' },
      { id: 'E02', description: 'GPS trust: 0.31', source: 'Trust engine' },
      { id: 'E03', description: 'Mission risk: HIGH', source: 'Mission impact engine' }
    ]);
    
    setHypotheses([
      { id: 'H1', description: 'GPS integrity degradation', confidence: 0.91 },
      { id: 'H2', description: 'Sensor noise', confidence: 0.06 },
      { id: 'H3', description: 'Inertial issue', confidence: 0.03 }
    ]);

    await delay(1500);
    setEvents(prev => [...prev, { step: 5, tool: 'get_mission_impact', status: 'completed', summary: 'High risk to navigation' }]);
    await delay(1000);
    setEvents(prev => [...prev, { step: 6, tool: 'generate_actions', status: 'completed', summary: 'Generated 3 candidate actions' }]);
    await delay(1000);
    setEvents(prev => [...prev, { step: 7, tool: 'simulate_action', status: 'completed', summary: 'Simulated outcomes' }]);

    const candidateActions: CandidateAction[] = [
      { id: 'continue_gps', name: 'Continue GPS', risk: 'HIGH', mission_continuity: 42 },
      { id: 'switch_inertial', name: 'Switch to Inertial', risk: 'MEDIUM', mission_continuity: 71, recommended: true },
      { id: 'safe_mode', name: 'Safe Mode', risk: 'LOW', mission_continuity: 0 }
    ];
    setActions(candidateActions);

    await delay(1500);
    setEvents(prev => [...prev, { step: 8, tool: 'evaluate_policy', status: 'completed', summary: 'Action requires human authorization' }]);
    
    // Trigger Authorization
    setAuthRequiredAction(candidateActions[1]);
  };

  const approveAction = async () => {
    if (!authRequiredAction) return;
    setAuthRequiredAction(null);

    setEvents(prev => [...prev, { step: 9, tool: 'execute_action', status: 'completed', summary: 'Executing: Switch to Inertial' }]);
    setState(s => ({ ...s, navigation_mode: 'INERTIAL', mission_status: 'DEGRADED', mission_risk: 'MEDIUM' }));
    
    await delay(2000);
    
    // Verification Failure (Deliberate for Demo)
    setEvents(prev => [...prev, { step: 10, tool: 'verify_action', status: 'failed', summary: 'Verification failed' }]);
    setVerification({ verified: false, reason: 'Position residual remains above safe threshold.', next_action_required: true });
    
    await delay(2500);
    
    // Replanning
    setEvents(prev => [...prev, { step: 11, tool: 'replan', status: 'completed', summary: 'Agent replanning to Safe Mode' }]);
    setVerification(null);
    setActions(prev => prev.map(a => ({ ...a, recommended: a.id === 'safe_mode' })));
    
    await delay(2000);
    setEvents(prev => [...prev, { step: 12, tool: 'execute_action', status: 'completed', summary: 'Executing: Safe Mode' }]);
    setState(s => ({ ...s, navigation_mode: 'SAFE_MODE', mission_status: 'SAFE', mission_risk: 'LOW' }));
    
    await delay(2000);
    setEvents(prev => [...prev, { step: 13, tool: 'verify_action', status: 'completed', summary: 'Recovery successful' }]);
    setVerification({ verified: true, reason: 'Mission risk reduced below policy threshold.', next_action_required: false });
    setState(s => ({ ...s, mission_status: 'RECOVERED' }));
  };

  const rejectAction = () => {
    setAuthRequiredAction(null);
    setEvents(prev => [...prev, { step: 9, tool: 'execute_action', status: 'failed', summary: 'Authorization rejected' }]);
  };

  return (
    <SimulatorContext.Provider value={{ state, events, evidence, hypotheses, actions, verification, authRequiredAction, runIncident, approveAction, rejectAction }}>
      {children}
    </SimulatorContext.Provider>
  );
}

export function useSimulator() {
  const context = useContext(SimulatorContext);
  if (context === undefined) throw new Error('useSimulator must be used within a SimulatorProvider');
  return context;
}
