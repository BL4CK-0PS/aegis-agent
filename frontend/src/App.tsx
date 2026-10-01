import { Shield, Activity, Cpu } from 'lucide-react';
import { MissionGraph } from './components/MissionGraph';
import { DroneTelemetry } from './components/DroneTelemetry';
import { AgentTrace, EvidencePanel } from './components/AgentPanels';
import { CandidateActionsPanel, AuthorizationPanel } from './components/SimulationActionPanels';
import { SimulatorProvider, useSimulator } from './context/SimulatorContext';

function Dashboard() {
  const { state, runIncident } = useSimulator();

  return (
    <div className="min-h-screen bg-[#09090b] text-slate-200 p-4 font-sans selection:bg-cyan-900/50">
      <div className="max-w-[1600px] mx-auto space-y-4">
        
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-zinc-900/50 border border-zinc-800 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-cyan-400" />
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">AEGIS</h1>
              <p className="text-xs text-zinc-400 uppercase tracking-widest font-semibold">Decision Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
              <span className="text-xs text-zinc-400 uppercase tracking-wider">Mission Status</span>
              <span className={`text-sm font-semibold flex items-center gap-2 ${state.mission_status === 'NORMAL' || state.mission_status === 'SAFE' || state.mission_status === 'RECOVERED' ? 'text-emerald-400' : 'text-rose-400'}`}>
                <span className={`w-2 h-2 rounded-full animate-pulse ${state.mission_status === 'NORMAL' || state.mission_status === 'SAFE' || state.mission_status === 'RECOVERED' ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                {state.mission_status}
              </span>
            </div>
            <button 
              onClick={runIncident}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-sm font-medium rounded-lg transition-colors border border-zinc-700"
            >
              Run Incident
            </button>
          </div>
        </header>

        {/* Top Row: Drone + Graph */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* Drone & Telemetry */}
          <div className="lg:col-span-4 bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex flex-col gap-4">
            <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-500" />
              Telemetry & State
            </h2>
            
            <div className="flex-1 bg-zinc-950/50 rounded-lg border border-zinc-800/50 relative overflow-hidden min-h-[250px] flex items-center justify-center">
              <DroneTelemetry />
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-3 bg-zinc-800/30 rounded-lg border border-zinc-800/50">
                <div className="text-zinc-500 text-xs mb-1">Position</div>
                <div className="font-mono text-zinc-200">{state.position.x.toFixed(1)}, {state.position.y.toFixed(1)}</div>
              </div>
              <div className="p-3 bg-zinc-800/30 rounded-lg border border-zinc-800/50">
                <div className="text-zinc-500 text-xs mb-1">Velocity</div>
                <div className="font-mono text-zinc-200">{state.velocity.x.toFixed(1)} m/s</div>
              </div>
              <div className="p-3 bg-zinc-800/30 rounded-lg border border-zinc-800/50">
                <div className="text-zinc-500 text-xs mb-1">Nav Mode</div>
                <div className="font-mono text-cyan-400">{state.navigation_mode}</div>
              </div>
              <div className="p-3 bg-zinc-800/30 rounded-lg border border-zinc-800/50">
                <div className="text-zinc-500 text-xs mb-1">Progress</div>
                <div className="font-mono text-zinc-200">{state.mission_progress.toFixed(0)}%</div>
              </div>
            </div>
          </div>

          {/* Mission Dependency Graph */}
          <div className="lg:col-span-8 bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex flex-col">
            <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Dependency Graph
            </h2>
            <div className="flex-1 bg-zinc-950/50 rounded-lg border border-zinc-800/50 flex items-center justify-center overflow-hidden min-h-[300px]">
              <MissionGraph />
            </div>
          </div>
        </div>

        {/* Agent Trace */}
        <AgentTrace />

        {/* Evidence & Trust */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <EvidencePanel />

          {/* Trust & Impact */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5">
             <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Trust & Impact</h2>
             <div className="space-y-4">
               <div>
                 <div className="flex justify-between text-xs mb-1">
                   <span className="text-zinc-400">GPS Trust</span>
                   <span className={`${state.gps_trust < 0.5 ? 'text-rose-400' : 'text-emerald-400'} font-mono`}>{(state.gps_trust * 100).toFixed(0)}%</span>
                 </div>
                 <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                   <div className={`h-full ${state.gps_trust < 0.5 ? 'bg-rose-500' : 'bg-emerald-500'} transition-all duration-1000`} style={{ width: `${state.gps_trust * 100}%` }}></div>
                 </div>
               </div>

               <div>
                 <div className="flex justify-between text-xs mb-1">
                   <span className="text-zinc-400">IMU Trust</span>
                   <span className="text-emerald-400 font-mono">{(state.imu_trust * 100).toFixed(0)}%</span>
                 </div>
                 <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                   <div className="h-full bg-emerald-500 transition-all duration-1000" style={{ width: `${state.imu_trust * 100}%` }}></div>
                 </div>
               </div>
               
               <div className="pt-2">
                 <div className={`inline-flex items-center gap-2 px-3 py-1 border rounded-full text-xs font-semibold ${
                   state.mission_risk === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                   state.mission_risk === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                   'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                 }`}>
                   MISSION RISK: {state.mission_risk}
                 </div>
               </div>

             </div>
          </div>
        </div>

        {/* Action / Sim / Policy */}
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
