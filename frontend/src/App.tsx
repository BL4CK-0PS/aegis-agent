import { Shield, Activity, Cpu, Play } from 'lucide-react';
import { MissionGraph } from './components/MissionGraph';
import { DroneTelemetry } from './components/DroneTelemetry';
import { AgentTrace, EvidencePanel } from './components/AgentPanels';
import { CandidateActionsPanel, AuthorizationPanel } from './components/SimulationActionPanels';
import { SimulatorProvider, useSimulator } from './context/SimulatorContext';

function Dashboard() {
  const { state, runIncident, lifecyclePhase, capabilityImpacts } = useSimulator();

  const lifecycleStages = [
    { key: 'NORMAL', label: 'NORMAL' },
    { key: 'INCIDENT_DETECTED', label: 'INCIDENT DETECTED' },
    { key: 'INVESTIGATING', label: 'INVESTIGATING' },
    { key: 'EVIDENCE_GATHERED', label: 'EVIDENCE' },
    { key: 'HYPOTHESIS_FORMED', label: 'HYPOTHESIS' },
    { key: 'ACTION_SIMULATED', label: 'SIMULATION' },
    { key: 'POLICY_CHECK', label: 'POLICY CHECK' },
    { key: 'AUTHORIZED', label: 'AUTHORIZED' },
    { key: 'EXECUTED', label: 'EXECUTED' },
    { key: 'VERIFICATION_FAILED', label: 'VERIFY FAILED' },
    { key: 'REPLAN', label: 'REPLAN' },
    { key: 'SAFE_MODE', label: 'SAFE MODE' },
  ];

  const currentIdx = lifecycleStages.findIndex(s => s.key === lifecyclePhase);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NORMAL':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'SAFE':
      case 'RECOVERED':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'DEGRADED':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30 animate-pulse';
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30 animate-pulse';
      default:
        return 'text-zinc-400 bg-zinc-800 border-zinc-700';
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-slate-200 p-4 font-sans selection:bg-cyan-900/50">
      <div className="max-w-[1600px] mx-auto space-y-4">
        
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-zinc-900/50 border border-zinc-800 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-950/40 border border-cyan-800/50 rounded-lg">
              <Shield className="w-7 h-7 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">AEGIS</h1>
                <span className="text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded">
                  BHARAT AGENTIC 2026
                </span>
              </div>
              <p className="text-xs text-zinc-400 tracking-wider">
                Autonomous Evidence-driven Governance and Intelligent Safety
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-mono">Mission Status</span>
              <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${getStatusColor(state.mission_status)}`}>
                ● {state.mission_status}
              </span>
            </div>

            <button
              onClick={runIncident}
              className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-mono font-bold rounded-lg shadow-lg shadow-cyan-950/40 border border-cyan-500/40 flex items-center gap-2 transition-all cursor-pointer active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              RUN INCIDENT
            </button>
          </div>
        </header>

        {/* Lifecycle Ribbon */}
        <div className="px-4 py-2.5 bg-zinc-900/40 border border-zinc-800/80 rounded-xl overflow-x-auto flex items-center gap-2">
          <span className="text-[10px] font-mono text-zinc-500 font-bold uppercase tracking-wider shrink-0 mr-1">
            DECISION LIFECYCLE:
          </span>
          <div className="flex items-center gap-1.5 min-w-max font-mono text-[10px]">
            {lifecycleStages.map((stage, idx) => {
              const isPast = idx < currentIdx;
              const isCurrent = idx === currentIdx;

              return (
                <div key={stage.key} className="flex items-center gap-1.5">
                  <span
                    className={`px-2 py-0.5 rounded font-bold transition-all ${
                      isCurrent
                        ? stage.key === 'VERIFICATION_FAILED'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/50 animate-pulse'
                          : stage.key === 'SAFE_MODE'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 animate-pulse'
                          : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 animate-pulse'
                        : isPast
                        ? 'bg-zinc-800/60 text-zinc-400 border border-zinc-700/40'
                        : 'text-zinc-600 border border-transparent'
                    }`}
                  >
                    {isCurrent ? `▶ ${stage.label}` : stage.label}
                  </span>
                  {idx < lifecycleStages.length - 1 && (
                    <span className="text-zinc-700 text-xs">→</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Row: Drone Telemetry + Mission Dependency Graph */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* Drone & Telemetry */}
          <div className="lg:col-span-4 bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-500" />
                Telemetry & State
              </h2>
              <span className="text-[10px] font-mono text-zinc-500">AUTONOMOUS SENSING</span>
            </div>
            
            <div className="flex-1 bg-zinc-950/50 rounded-lg border border-zinc-800/50 relative overflow-hidden min-h-[240px] flex items-center justify-center">
              <DroneTelemetry />
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 bg-zinc-950/60 rounded-lg border border-zinc-800/70">
                <div className="text-zinc-500 text-[10px] mb-0.5">POSITION (X, Y)</div>
                <div className="font-bold text-zinc-200">{state.position.x.toFixed(1)}, {state.position.y.toFixed(1)}</div>
              </div>
              <div className="p-2.5 bg-zinc-950/60 rounded-lg border border-zinc-800/70">
                <div className="text-zinc-500 text-[10px] mb-0.5">VELOCITY</div>
                <div className="font-bold text-zinc-200">{state.velocity.x.toFixed(1)} m/s</div>
              </div>
              <div className="p-2.5 bg-zinc-950/60 rounded-lg border border-zinc-800/70">
                <div className="text-zinc-500 text-[10px] mb-0.5">NAV MODE</div>
                <div className="font-bold text-cyan-400">{state.navigation_mode}</div>
              </div>
              <div className="p-2.5 bg-zinc-950/60 rounded-lg border border-zinc-800/70">
                <div className="text-zinc-500 text-[10px] mb-0.5">PROGRESS</div>
                <div className="font-bold text-zinc-200">{state.mission_progress.toFixed(0)}%</div>
              </div>
            </div>
          </div>

          {/* Mission Dependency Graph */}
          <div className="lg:col-span-8 bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                Dependency Propagation Graph
              </h2>
              <span className="text-[10px] font-mono text-zinc-500">FAULT ISOLATION</span>
            </div>
            <div className="flex-1 bg-zinc-950/50 rounded-lg border border-zinc-800/50 flex items-center justify-center overflow-hidden min-h-[300px]">
              <MissionGraph />
            </div>
          </div>
        </div>

        {/* HERO: Agent Investigation Trace */}
        <AgentTrace />

        {/* Evidence & Hypotheses + Trust & Mission Impact */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <EvidencePanel />

          {/* Trust & Impact Panel */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider">
                  Trust & Mission Impact
                </h2>
                <span className="text-[10px] font-mono text-zinc-500">STATISTICAL INTEGRITY</span>
              </div>

              {/* Sensor Trust Bars */}
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-zinc-400">GPS Trust Index</span>
                    <span className={`font-bold ${state.gps_trust < 0.5 ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {state.gps_trust < 0.5 ? `${(state.gps_trust * 100).toFixed(0)}% (DEGRADED)` : `${(state.gps_trust * 100).toFixed(0)}%`}
                    </span>
                  </div>
                  <div className="h-2 bg-zinc-950 rounded-full overflow-hidden border border-zinc-800">
                    <div
                      className={`h-full ${state.gps_trust < 0.5 ? 'bg-rose-500' : 'bg-emerald-500'} transition-all duration-700`}
                      style={{ width: `${Math.max(5, state.gps_trust * 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-zinc-400">IMU Trust Index</span>
                    <span className="text-emerald-400 font-bold">{(state.imu_trust * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-zinc-950 rounded-full overflow-hidden border border-zinc-800">
                    <div
                      className="h-full bg-emerald-500 transition-all duration-700"
                      style={{ width: `${state.imu_trust * 100}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-zinc-400">Barometer / Comms Trust</span>
                    <span className="text-emerald-400 font-bold">95%</span>
                  </div>
                  <div className="h-2 bg-zinc-950 rounded-full overflow-hidden border border-zinc-800">
                    <div
                      className="h-full bg-emerald-500 transition-all duration-700"
                      style={{ width: '95%' }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Capability Impact Breakdown */}
              <div className="mt-6 pt-4 border-t border-zinc-800/80">
                <div className="text-[11px] font-mono uppercase text-zinc-400 tracking-wider mb-2">
                  Impacted Subsystems & Capabilities
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  {capabilityImpacts.map(cap => (
                    <div
                      key={cap.name}
                      className="p-2 bg-zinc-950/60 rounded border border-zinc-800/70 flex justify-between items-center"
                    >
                      <span className="text-zinc-400 truncate max-w-[130px]">{cap.name}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          cap.level === 'HIGH'
                            ? 'bg-rose-500/20 text-rose-300'
                            : cap.level === 'MEDIUM'
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-emerald-500/20 text-emerald-300'
                        }`}
                      >
                        {cap.level}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between font-mono">
              <span className="text-xs text-zinc-400">OVERALL MISSION RISK</span>
              <div
                className={`inline-flex items-center gap-2 px-3 py-1 border rounded-full text-xs font-bold ${
                  state.mission_risk === 'HIGH'
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse'
                    : state.mission_risk === 'MEDIUM'
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                }`}
              >
                ● {state.mission_risk} RISK
              </div>
            </div>
          </div>
        </div>

        {/* Candidate Actions / Simulations + Policy / Authorization / Verification */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CandidateActionsPanel />
          <AuthorizationPanel />
        </div>

      </div>
    </div>
  );
}

export default function App() {
  return (
    <SimulatorProvider>
      <Dashboard />
    </SimulatorProvider>
  );
}
