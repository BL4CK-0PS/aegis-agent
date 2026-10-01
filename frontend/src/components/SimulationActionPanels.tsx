import { AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function CandidateActionsPanel() {
  const { actions } = useSimulator();
  
  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Candidate Actions & Simulations</h2>
      {actions.length === 0 ? (
        <div className="text-xs text-zinc-600">Waiting for agent simulation...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {actions.map(action => (
            <div key={action.id} className={`p-4 rounded-lg border flex flex-col gap-3 relative overflow-hidden ${action.recommended ? 'bg-cyan-900/20 border-cyan-800/50' : 'bg-zinc-800/30 border-zinc-800/50'}`}>
              {action.recommended && <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500"></div>}
              <div className="flex justify-between items-start">
                <div className={`text-sm font-medium ${action.recommended ? 'text-cyan-100' : 'text-zinc-200'}`}>{action.name}</div>
                {action.recommended && <div className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">Recommended</div>}
              </div>
              <div className={`text-xs px-2 py-1 rounded inline-block w-fit ${action.risk === 'HIGH' ? 'text-rose-400 bg-rose-400/10' : action.risk === 'MEDIUM' ? 'text-amber-400 bg-amber-400/10' : 'text-emerald-400 bg-emerald-400/10'}`}>
                {action.risk} RISK
              </div>
              <div className="text-xs text-zinc-500 mt-2">Mission continuity: {action.mission_continuity}%</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function AuthorizationPanel() {
  const { authRequiredAction, approveAction, rejectAction, verification, state } = useSimulator();

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Policy / Authorization / Verify</h2>
      
      {!authRequiredAction && !verification && state.mission_status !== 'RECOVERED' && (
        <div className="flex-1 flex items-center justify-center text-xs text-zinc-600 border-2 border-dashed border-zinc-800 rounded-lg p-6">
          No pending authorizations.
        </div>
      )}

      {authRequiredAction && (
        <div className="border border-amber-500/30 bg-amber-500/5 rounded-lg p-4 animate-in zoom-in-95">
          <div className="flex items-center gap-2 text-amber-500 font-bold text-sm mb-3">
            <ShieldAlert className="w-5 h-5" />
            ACTION REQUIRES AUTHORIZATION
          </div>
          <div className="text-zinc-200 text-sm mb-1">{authRequiredAction.name}</div>
          <div className="text-xs text-zinc-400 mb-4">
            <div>Mission Risk: {authRequiredAction.risk}</div>
            <div>Expected Continuity: {authRequiredAction.mission_continuity}%</div>
          </div>
          <div className="flex gap-3">
            <button onClick={approveAction} className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold rounded">APPROVE</button>
            <button onClick={rejectAction} className="px-4 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-white text-xs font-bold rounded">REJECT</button>
          </div>
        </div>
      )}

      {verification && !verification.verified && (
        <div className="border border-rose-500/50 bg-rose-500/10 rounded-lg p-4 animate-in zoom-in-95">
          <div className="flex items-center gap-2 text-rose-500 font-bold text-sm mb-2">
            <AlertTriangle className="w-5 h-5" />
            VERIFICATION FAILED
          </div>
          <div className="text-xs text-rose-200 mb-2">Reason: {verification.reason}</div>
          <div className="text-xs font-mono text-zinc-400 animate-pulse">AGENT REPLANNING...</div>
        </div>
      )}

      {verification && verification.verified && (
        <div className="border border-emerald-500/50 bg-emerald-500/10 rounded-lg p-4 animate-in zoom-in-95">
          <div className="flex items-center gap-2 text-emerald-500 font-bold text-sm mb-2">
            <CheckCircle className="w-5 h-5" />
            RECOVERY SUCCESSFUL
          </div>
          <div className="text-xs text-emerald-200 mb-1">Navigation: SAFE_MODE</div>
          <div className="text-xs text-emerald-200 mb-1">Mission Risk: LOW</div>
          <div className="text-xs text-emerald-200">Verification: PASSED</div>
          <div className="mt-3 text-sm font-bold text-emerald-400">AEGIS STATUS: MISSION SAFETY RESTORED</div>
        </div>
      )}
    </div>
  );
}
