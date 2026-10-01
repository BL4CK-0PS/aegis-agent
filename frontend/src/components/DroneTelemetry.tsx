
import { Crosshair } from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function DroneTelemetry() {
  const { state } = useSimulator();
  
  return (
    <div className="w-full h-full min-h-[250px] relative bg-zinc-950/50 rounded-lg overflow-hidden flex items-center justify-center border border-zinc-800/50">
      
      {/* Target Crosshair */}
      <div className="absolute top-8 right-12 text-zinc-600/50 flex flex-col items-center">
        <Crosshair className="w-8 h-8" />
        <span className="text-[10px] mt-1 font-mono uppercase">Target</span>
      </div>

      {/* Trajectory lines */}
      <div className="absolute w-full h-full pointer-events-none">
        <svg className="w-full h-full opacity-30">
          <path d="M 50,200 C 100,180 150,150 200,100" stroke="#a1a1aa" strokeWidth="2" fill="none" strokeDasharray="4 4" />
          {state.mission_status === 'DEGRADED' && (
            <path d="M 200,100 C 220,80 250,50 300,40" stroke="#f43f5e" strokeWidth="2" fill="none" className="animate-pulse" />
          )}
        </svg>
      </div>

      {/* Drone Indicator */}
      <div className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center transition-all duration-1000 ease-linear" style={{ left: `${50 + (state.position.x % 40)}%`, top: `${50 - (state.position.y % 40)}%` }}>
        
        {/* Radar Ping */}
        <div className="absolute w-16 h-16 bg-cyan-500/20 rounded-full animate-ping"></div>
        
        <div className={`relative w-4 h-4 rounded-sm transform rotate-45 shadow-[0_0_15px_rgba(34,211,238,0.6)] ${state.mission_status === 'DEGRADED' ? 'bg-amber-400' : state.mission_status === 'SAFE' || state.mission_status === 'RECOVERED' ? 'bg-emerald-400' : 'bg-cyan-400'}`}></div>
        
        <div className="mt-4 bg-zinc-900/80 backdrop-blur-sm border border-zinc-700/50 px-2 py-1 rounded text-[10px] font-mono text-cyan-100 whitespace-nowrap">
          ALT: 400m | HDG: 045°
        </div>
      </div>
      
      {/* Fault Indicator */}
      {state.mission_status === 'DEGRADED' && (
        <div className="absolute bottom-4 left-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 px-3 py-1.5 rounded text-xs font-mono font-bold animate-pulse">
          ! GPS INTEGRITY FAULT
        </div>
      )}

    </div>
  );
}
