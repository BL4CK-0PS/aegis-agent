import { AlertTriangle, CheckCircle, ShieldAlert, Cpu } from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function CandidateActionsPanel() {
  const { actions, lifecyclePhase } = useSimulator();

  const defaultActions = [
    {
      id: 'switch_inertial',
      name: 'Switch to IMU-Only Navigation',
      risk: 'MEDIUM' as const,
      mission_continuity: 71,
      success_rate: 71,
      expected_delay: '+18 sec',
      recommended: true,
      policy_status: 'REQUIRES_AUTH' as const,
    },
    {
      id: 'continue_gps',
      name: 'GPS Re-Acquisition / Continue GPS',
      risk: 'HIGH' as const,
      mission_continuity: 12,
      success_rate: 8,
      expected_delay: '+2.4 min',
      recommended: false,
      policy_status: 'DENIED' as const,
    },
    {
      id: 'safe_mode',
      name: 'Emergency Safe Mode (Hover)',
      risk: 'LOW' as const,
      mission_continuity: 0,
      success_rate: 99,
      expected_delay: 'Stationary',
      recommended: false,
      policy_status: 'ALLOWED' as const,
    },
  ];

  const currentActions = actions.length > 0 ? actions : defaultActions;

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Candidate Actions & Simulations
          </h2>
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-2 py-0.5 rounded">
            COUNTERFACTUAL EVALUATION
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {currentActions.map(action => {
            const isRec = Boolean(action.recommended);
            const isRiskHigh = action.risk === 'HIGH';
            const isRiskMed = action.risk === 'MEDIUM';

            return (
              <div
                key={action.id}
                className={`p-4 rounded-lg border flex flex-col justify-between transition-all relative overflow-hidden ${
                  isRec
                    ? 'bg-cyan-950/30 border-cyan-700/60 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                    : 'bg-zinc-950/60 border-zinc-800/80 opacity-80'
                }`}
              >
                {isRec && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-cyan-400"></div>
                )}

                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span
                      className={`text-xs font-bold leading-snug ${
                        isRec ? 'text-white' : 'text-zinc-200'
                      }`}
                    >
                      {action.name}
                    </span>
                    {isRec && (
                      <span className="text-[9px] uppercase font-mono font-bold bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/30 shrink-0 ml-1">
                        RECOMMENDED
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[10px] font-mono mb-2">
                    <span
                      className={`px-1.5 py-0.5 rounded font-bold ${
                        isRiskHigh
                          ? 'bg-rose-500/20 text-rose-300'
                          : isRiskMed
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-emerald-500/20 text-emerald-300'
                      }`}
                    >
                      RISK: {action.risk}
                    </span>
                    <span className="text-zinc-400">
                      Success: {action.success_rate ?? action.mission_continuity}%
                    </span>
                  </div>

                  <div className="text-[11px] font-mono text-zinc-400">
                    <div>Delay: {action.expected_delay || '+18 sec'}</div>
                    <div>Continuity: {action.mission_continuity}%</div>
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[10px] font-mono text-zinc-500">
                  <span>Policy: {action.policy_status || (action.risk === 'HIGH' ? 'DENIED' : 'ALLOWED')}</span>
                  <span className="text-cyan-400 font-bold">
                    {lifecyclePhase === 'NORMAL' ? 'READY' : 'SIMULATED ✓'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 p-3 bg-zinc-950/40 border border-zinc-800/60 rounded-lg text-xs font-mono text-zinc-400 flex items-center justify-between">
        <div>
          <span className="text-cyan-400 font-bold">REASONING SUMMARY:</span> Inertial switch preserves mission timeline (+18s) with moderate drift risk, vs GPS departure failure (Risk 92%).
        </div>
      </div>
    </div>
  );
}

export function AuthorizationPanel() {
  const { authRequiredAction, approveAction, rejectAction, verification, state, lifecyclePhase } = useSimulator();

  const pipelineSteps = [
    { label: 'POLICY', active: true, completed: lifecyclePhase !== 'NORMAL' },
    {
      label: 'AUTH',
      active: lifecyclePhase === 'POLICY_CHECK' || lifecyclePhase === 'AUTHORIZED',
      completed: ['AUTHORIZED', 'EXECUTED', 'VERIFICATION_FAILED', 'REPLAN', 'SAFE_MODE'].includes(lifecyclePhase),
    },
    {
      label: 'EXEC',
      active: lifecyclePhase === 'EXECUTED',
      completed: ['VERIFICATION_FAILED', 'REPLAN', 'SAFE_MODE'].includes(lifecyclePhase),
    },
    {
      label: 'VERIFY',
      active: lifecyclePhase === 'VERIFICATION_FAILED' || lifecyclePhase === 'SAFE_MODE',
      completed: lifecyclePhase === 'SAFE_MODE',
      failed: lifecyclePhase === 'VERIFICATION_FAILED',
    },
    { label: 'REPLAN', active: lifecyclePhase === 'REPLAN', completed: lifecyclePhase === 'SAFE_MODE' },
    { label: 'SAFE', active: lifecyclePhase === 'SAFE_MODE', completed: lifecyclePhase === 'SAFE_MODE' },
  ];

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider">
            Policy / Authorization / Verify
          </h2>
          <span className="text-[10px] font-mono text-zinc-400">STATE MACHINE</span>
        </div>

        {/* Pipeline Stepper */}
        <div className="flex items-center gap-1 mb-4 p-2 bg-zinc-950/70 border border-zinc-800 rounded-lg overflow-x-auto">
          {pipelineSteps.map((step, idx) => (
            <div key={idx} className="flex items-center gap-1 font-mono text-[10px]">
              <span
                className={`px-2 py-0.5 rounded font-bold transition-all ${
                  step.failed
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                    : step.completed
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : step.active
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse'
                    : 'bg-zinc-800/40 text-zinc-500 border border-transparent'
                }`}
              >
                {step.label}
              </span>
              {idx < pipelineSteps.length - 1 && <span className="text-zinc-600 text-xs">→</span>}
            </div>
          ))}
        </div>

        {/* 1. Pending Operator Authorization */}
        {authRequiredAction && (
          <div className="border border-amber-500/50 bg-amber-950/20 rounded-lg p-4 animate-in zoom-in-95 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-sm font-mono">
                <ShieldAlert className="w-5 h-5 shrink-0" />
                <span>ACTION REQUIRES HUMAN AUTHORIZATION</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-amber-500/20 text-amber-300 rounded border border-amber-500/30">
                GATE LOCKED
              </span>
            </div>

            <div className="text-zinc-200 text-xs font-mono space-y-1 bg-zinc-950/60 p-2.5 rounded border border-zinc-800">
              <div><strong className="text-zinc-400">Action:</strong> {authRequiredAction.name}</div>
              <div><strong className="text-zinc-400">Policy Verdict:</strong> REQUIRES_HUMAN_AUTHORIZATION</div>
              <div><strong className="text-zinc-400">Risk Assessment:</strong> {authRequiredAction.risk} (Continuity: {authRequiredAction.mission_continuity}%)</div>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                onClick={approveAction}
                className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold rounded shadow-lg shadow-emerald-950/50 transition-all flex items-center justify-center gap-1.5"
              >
                <CheckCircle className="w-4 h-4" />
                APPROVE INTERVENTION
              </button>
              <button
                onClick={rejectAction}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-mono font-bold rounded transition-all"
              >
                REJECT
              </button>
            </div>
          </div>
        )}

        {/* 2. Verification Failure Alert (Deliberate for Demo) */}
        {verification && !verification.verified && !authRequiredAction && (
          <div className="border border-rose-500/50 bg-rose-950/20 rounded-lg p-4 animate-in zoom-in-95 space-y-2">
            <div className="flex items-center gap-2 text-rose-400 font-bold text-sm font-mono">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <span>VERIFICATION FAILURE</span>
            </div>

            <div className="p-2.5 bg-zinc-950/60 rounded border border-rose-900/40 text-xs font-mono space-y-1">
              <div className="text-zinc-400">Expected: <span className="text-zinc-200">{verification.expected || 'Navigation confidence > 0.80'}</span></div>
              <div className="text-rose-400 font-bold">Actual: {verification.actual || 'Navigation residual = 7.89m (drift detected)'}</div>
            </div>

            <div className="text-[11px] font-mono text-zinc-300 space-y-0.5 pt-1">
              <div>→ Action considered unsuccessful</div>
              <div className="text-amber-400 font-bold animate-pulse">→ Agent replanning initiated: Safe Mode failsafe</div>
            </div>
          </div>
        )}

        {/* 3. Recovery Successful */}
        {verification && verification.verified && !authRequiredAction && (
          <div className="border border-emerald-500/50 bg-emerald-950/20 rounded-lg p-4 animate-in zoom-in-95 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm font-mono">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <span>RECOVERY SUCCESSFUL</span>
            </div>

            <div className="p-2.5 bg-zinc-950/60 rounded border border-emerald-900/40 text-xs font-mono space-y-1">
              <div>Navigation Mode: <span className="text-emerald-300 font-bold">SAFE_MODE (Stationary Hover)</span></div>
              <div>Mission Risk: <span className="text-emerald-300 font-bold">LOW</span></div>
              <div>Verification: <span className="text-emerald-300 font-bold">PASSED (Residual 0.08m)</span></div>
            </div>

            <div className="pt-2 text-xs font-mono font-bold text-emerald-400">
              AEGIS STATUS: MISSION SAFETY RESTORED
            </div>
          </div>
        )}

        {/* Default / Idle State */}
        {!authRequiredAction && !verification && state.mission_status !== 'RECOVERED' && (
          <div className="flex flex-col items-center justify-center text-xs font-mono text-zinc-500 border border-dashed border-zinc-800 rounded-lg p-6 text-center space-y-1">
            <span>GOVERNANCE GATE: ACTIVE</span>
            <span className="text-[11px] text-zinc-600">Actions requiring authorization will hold here for human sign-off.</span>
          </div>
        )}
      </div>

      <div className="text-[10px] font-mono text-zinc-500 pt-3 border-t border-zinc-800/60 flex justify-between">
        <span>AUTHORITATIVE BOUNDARY: ENFORCED</span>
        <span>AUDIT LOG: IMMUTABLE</span>
      </div>
    </div>
  );
}
