import { Crosshair, AlertTriangle } from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function DroneTelemetry() {
  const { state } = useSimulator();
  const isGpsFault = Boolean(state.gps_fault_active) || state.residual > 2.0;
  const isSafeMode = state.navigation_mode === 'SAFE_MODE';
  const headingDeg = Math.round((((state.heading || 0) * 180) / Math.PI + 360) % 360);
  const altDisplay = state.altitude !== undefined && state.altitude !== 'N/A' ? `${state.altitude}m` : 'N/A';

  // Compute normalized coordinates for visualization
  const posX = (state.position.x % 60);
  const posY = (state.position.y % 60);
  const droneLeft = `${40 + (posX / 60) * 25}%`;
  const droneTop = `${60 - (posY / 60) * 25}%`;

  // Corrupted GPS position offset when fault is injected
  const gpsOffset = state.residual ? Math.min(25, state.residual * 2.2) : 0;

  return (
    <div className="w-full h-full min-h-[250px] relative bg-zinc-950/60 rounded-lg overflow-hidden flex items-center justify-center border border-zinc-800/50">
      
      {/* Target Crosshair */}
      <div className="absolute top-6 right-8 text-zinc-600/60 flex flex-col items-center pointer-events-none">
        <Crosshair className="w-7 h-7 text-cyan-500/40" />
        <span className="text-[9px] mt-0.5 font-mono uppercase text-zinc-500">WAYPOINT 04</span>
      </div>

      {/* Trajectory lines */}
      <div className="absolute w-full h-full pointer-events-none">
        <svg className="w-full h-full opacity-40">
          <path
            d="M 60,190 C 120,160 180,130 260,80"
            stroke="#06b6d4"
            strokeWidth="1.5"
            fill="none"
            strokeDasharray="4 4"
          />
          {isGpsFault && (
            <path
              d="M 180,130 C 220,90 280,60 330,40"
              stroke="#f43f5e"
              strokeWidth="2"
              fill="none"
              className="animate-pulse"
            />
          )}
        </svg>
      </div>

      {/* True Drone Position Indicator */}
      <div
        className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center transition-all duration-700 ease-out"
        style={{ left: droneLeft, top: droneTop }}
      >
        {/* Radar Ping */}
        <div
          className={`absolute w-14 h-14 rounded-full animate-ping ${
            isGpsFault ? 'bg-rose-500/20' : 'bg-cyan-500/20'
          }`}
        ></div>

        <div
          className={`relative w-4 h-4 rounded-sm transform rotate-45 shadow-[0_0_15px_rgba(34,211,238,0.6)] ${
            isSafeMode
              ? 'bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.8)]'
              : isGpsFault
              ? 'bg-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.8)]'
              : 'bg-cyan-400'
          }`}
        ></div>

        <div className="mt-3 bg-zinc-900/90 backdrop-blur-sm border border-zinc-700/60 px-2 py-0.5 rounded text-[10px] font-mono text-cyan-200 whitespace-nowrap shadow-md">
          ALT: {altDisplay} | HDG: {headingDeg.toString().padStart(3, '0')}°
        </div>
      </div>

      {/* Corrupted GPS Indicator (when fault active) */}
      {isGpsFault && !isSafeMode && (
        <div
          className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center transition-all duration-700 ease-out pointer-events-none opacity-80"
          style={{
            left: `calc(${droneLeft} + ${gpsOffset}px)`,
            top: `calc(${droneTop} - ${gpsOffset * 0.7}px)`,
          }}
        >
          <div className="w-3 h-3 rounded-full border-2 border-rose-500 bg-rose-500/20 animate-pulse"></div>
          <span className="text-[8px] font-mono text-rose-400 bg-zinc-950/80 px-1 rounded mt-1 border border-rose-900/40">
            GPS DIVERGENCE +{state.residual.toFixed(1)}m
          </span>
        </div>
      )}

      {/* Fault Indicator Banner */}
      {isGpsFault && !isSafeMode && (
        <div className="absolute bottom-3 left-3 bg-rose-950/80 border border-rose-600/50 text-rose-300 px-3 py-1 rounded text-xs font-mono font-bold animate-pulse flex items-center gap-1.5 shadow-lg">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          <span>GPS INTEGRITY FAULT (RESIDUAL: {state.residual.toFixed(1)}m)</span>
        </div>
      )}

      {/* Safe Mode Hover Banner */}
      {isSafeMode && (
        <div className="absolute bottom-3 left-3 bg-emerald-950/80 border border-emerald-600/50 text-emerald-300 px-3 py-1 rounded text-xs font-mono font-bold flex items-center gap-1.5 shadow-lg">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span>SAFE MODE: STATIONARY HOVER STABILIZED</span>
        </div>
      )}
    </div>
  );
}
