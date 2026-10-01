import { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  ShieldAlert,
  Cpu,
  Play,
  RotateCw,
  Shield,
  Activity,
} from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function CandidateActionsPanel() {
  const { actions, simulateAction } = useSimulator();
  const [simulatingId, setSimulatingId] = useState<string | null>(null);



  const handleSimulate = async (actionId: string) => {
    setSimulatingId(actionId);
    await simulateAction(actionId);
    setSimulatingId(null);
  };

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
          {actions.length === 0 ? (
            <div className="col-span-1 md:col-span-3 text-zinc-500 italic py-8 text-center border border-dashed border-zinc-800 rounded-lg flex flex-col items-center justify-center gap-2 font-mono text-xs">
              <Cpu className="w-6 h-6 text-zinc-600 animate-pulse" />
              <span>No candidate actions active. Click [ RUN INCIDENT ] to initiate candidate action synthesis and simulation.</span>
            </div>
          ) : (
            actions.map(action => {
            const isRec = Boolean(action.recommended);
            const isRiskCritical = action.risk === 'CRITICAL';
            const isRiskHigh = action.risk === 'HIGH';
            const isRiskMed = action.risk === 'MEDIUM';
            const hasSimulation = Boolean(action.simulation);
            const isSimulating = simulatingId === action.id;

            return (
              <div
                key={action.id}
                className={`p-4 rounded-lg border flex flex-col justify-between transition-all relative overflow-hidden ${
                  isRec
                    ? 'bg-cyan-950/30 border-cyan-600/70 shadow-[0_0_15px_rgba(6,182,212,0.15)] ring-1 ring-cyan-500/30'
                    : 'bg-zinc-950/60 border-zinc-800/80 opacity-85 hover:opacity-100'
                }`}
              >
                {isRec && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 to-indigo-500"></div>
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

                  {action.description && (
                    <p className="text-[11px] text-zinc-400 mb-2 leading-relaxed font-sans line-clamp-2">
                      {action.description}
                    </p>
                  )}

                  <div className="flex items-center gap-2 text-[10px] font-mono mb-2">
                    <span
                      className={`px-1.5 py-0.5 rounded font-bold ${
                        isRiskCritical
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : isRiskHigh
                          ? 'bg-rose-500/20 text-rose-300'
                          : isRiskMed
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      RISK: {action.risk}
                    </span>
                    <span className="text-zinc-400">
                      Continuity: {action.mission_continuity}%
                    </span>
                  </div>

                  {/* Simulation Outcome Display */}
                  {hasSimulation && action.simulation && (
                    <div className="p-2 bg-zinc-900/80 rounded border border-cyan-800/40 text-[10px] font-mono text-zinc-300 space-y-1 my-2">
                      <div className="text-cyan-400 font-bold flex items-center gap-1">
                        <CheckCircle className="w-3 h-3 text-cyan-400" />
                        Outcome: {action.simulation.recommendation.split(':')[0]}
                      </div>
                      <div className="text-zinc-400 line-clamp-2">
                        {action.simulation.predicted_mission_outcome}
                      </div>
                      <div className="flex justify-between text-zinc-500 pt-1 border-t border-zinc-800">
                        <span>Recovery: {action.simulation.expected_recovery_time}s</span>
                        <span>Risk: {(action.simulation.predicted_risk * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-3 pt-2.5 border-t border-zinc-800/60 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-zinc-400 truncate max-w-[110px]">
                    Policy: {action.policy_status || (action.risk === 'CRITICAL' ? 'DENIED' : 'ALLOWED')}
                  </span>
                  
                  <button
                    onClick={() => handleSimulate(action.id)}
                    disabled={isSimulating}
                    className="px-2.5 py-1 bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-700/50 rounded font-mono text-[10px] font-bold flex items-center gap-1 transition-all cursor-pointer active:scale-95 disabled:opacity-50"
                  >
                    {isSimulating ? (
                      <RotateCw className="w-2.5 h-2.5 animate-spin" />
                    ) : (
                      <Play className="w-2.5 h-2.5 fill-current" />
                    )}
                    {hasSimulation ? 'RE-SIMULATE' : 'SIMULATE'}
                  </button>
                </div>
              </div>
            );
          })
          )}
        </div>
      </div>

      <div className="mt-4 p-3 bg-zinc-950/50 border border-zinc-800/60 rounded-lg text-xs font-mono text-zinc-400 flex items-center justify-between">
        <div>
          <span className="text-cyan-400 font-bold">COUNTERFACTUAL REASONING:</span> Inertial switch retains mission profile with localized drift risk (Risk 42%), avoiding GPS divergence departure (Risk 92%).
        </div>
      </div>
    </div>
  );
}

export function AuthorizationPanel() {
  const {
    authRequiredAction,
    approveAction,
    rejectAction,
    verification,
    lifecyclePhase,
    activeExecution,
    replanCount,
  } = useSimulator();

  const pipelineSteps = [
    { label: 'POLICY', active: true, completed: lifecyclePhase !== 'NORMAL' },
    {
      label: 'AUTH',
      active: lifecyclePhase === 'POLICY_CHECK' || lifecyclePhase === 'AUTHORIZED',
      completed: [
        'AUTHORIZED',
        'EXECUTED',
        'VERIFICATION_FAILED',
        'REPLAN',
        'SAFE_MODE',
      ].includes(lifecyclePhase),
    },
    {
      label: 'EXEC',
      active: lifecyclePhase === 'EXECUTED',
      completed: ['VERIFICATION_FAILED', 'REPLAN', 'SAFE_MODE'].includes(lifecyclePhase),
    },
    {
      label: 'VERIFY',
      active:
        lifecyclePhase === 'VERIFICATION_FAILED' || lifecyclePhase === 'SAFE_MODE',
      completed: lifecyclePhase === 'SAFE_MODE',
      failed: lifecyclePhase === 'VERIFICATION_FAILED',
    },
    {
      label: 'REPLAN',
      active: lifecyclePhase === 'REPLAN',
      completed: lifecyclePhase === 'SAFE_MODE',
    },
    {
      label: 'SAFE',
      active: lifecyclePhase === 'SAFE_MODE',
      completed: lifecyclePhase === 'SAFE_MODE',
    },
  ];

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider">
              Policy / Authorization / Verify
            </h2>
          </div>
          {replanCount > 0 && (
            <span className="text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded animate-pulse">
              REPLAN #{replanCount}
            </span>
          )}
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
              {idx < pipelineSteps.length - 1 && (
                <span className="text-zinc-600 text-xs">→</span>
              )}
            </div>
          ))}
        </div>

        {/* Live Execution Panel (Section 13) */}
        {activeExecution && (
          <div className="mb-3 p-3 bg-zinc-950/70 border border-zinc-800/80 rounded-lg font-mono text-xs space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-bold pb-1 border-b border-zinc-800/60">
              <span className="text-zinc-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                EXECUTION BOUNDARY
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  activeExecution.status === 'COMPLETE'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : activeExecution.status === 'EXECUTING'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 animate-pulse'
                    : activeExecution.status === 'FAILED'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : 'bg-zinc-800 text-zinc-400'
                }`}
              >
                {activeExecution.status}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
              <div>
                <span className="text-zinc-500">Action: </span>
                <span className="text-zinc-200 font-bold">{activeExecution.action}</span>
              </div>
              <div>
                <span className="text-zinc-500">Timestamp: </span>
                <span className="text-zinc-300">{activeExecution.completed || activeExecution.started || 'In Progress'}</span>
              </div>
            </div>
            {activeExecution.result && (
              <div className="text-[11px] text-zinc-400 pt-1">
                <span className="text-zinc-500">Actuator Result: </span>
                <span>{activeExecution.result}</span>
              </div>
            )}
          </div>
        )}

        {/* 1. Pending Operator Authorization (HITL) */}
        {authRequiredAction && (
          <div className="border border-amber-500/60 bg-amber-950/20 rounded-lg p-4 animate-in zoom-in-95 space-y-3">
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
              <div>
                <strong className="text-zinc-400">Action:</strong> {authRequiredAction.name}
              </div>
              <div>
                <strong className="text-zinc-400">Policy Verdict:</strong> REQUIRES_HUMAN_AUTHORIZATION
              </div>
              <div>
                <strong className="text-zinc-400">Risk Assessment:</strong> {authRequiredAction.risk} (Continuity: {authRequiredAction.mission_continuity}%)
              </div>
              <div>
                <strong className="text-zinc-400">Governance Mandate:</strong> Invariant check prohibits unconfirmed inertial switches under active telemetry divergence.
              </div>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                onClick={approveAction}
                className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold rounded shadow-lg shadow-emerald-950/50 transition-all flex items-center justify-center gap-1.5 cursor-pointer active:scale-95"
              >
                <CheckCircle className="w-4 h-4" />
                APPROVE INTERVENTION
              </button>
              <button
                onClick={rejectAction}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-mono font-bold rounded transition-all cursor-pointer"
              >
                REJECT
              </button>
            </div>
          </div>
        )}

        {/* 2. Verification Failure Alert (Deliberate for Demo - Section 14 & 15) */}
        {verification && !verification.verified && !authRequiredAction && (
          <div className="border border-rose-500/60 bg-rose-950/20 rounded-lg p-4 animate-in zoom-in-95 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-rose-400 font-bold text-sm font-mono">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <span>VERIFICATION FAILED</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-rose-500/20 text-rose-300 rounded border border-rose-500/40 animate-pulse">
                INVARIANTS VIOLATED
              </span>
            </div>

            <div className="p-2.5 bg-zinc-950/60 rounded border border-rose-900/40 text-xs font-mono space-y-1">
              <div className="text-zinc-400">
                Expected: <span className="text-zinc-200">{verification.expected || 'Navigation residual < 2.0m'}</span>
              </div>
              <div className="text-rose-400 font-bold">
                Actual: {verification.actual || 'Navigation residual = 3.60m (Drift detected)'}
              </div>
              <div className="text-zinc-400 pt-1 text-[11px]">
                Reason: {verification.reason}
              </div>
            </div>

            {/* Replanning Cascade Diagram */}
            <div className="p-2.5 bg-zinc-950/70 border border-amber-600/30 rounded text-[11px] font-mono space-y-1 text-zinc-300">
              <div className="text-amber-400 font-bold flex items-center gap-1.5">
                <RotateCw className="w-3.5 h-3.5 animate-spin text-amber-400" />
                RECOVERY REPLANNING INITIATED (REPLAN #{replanCount || 1})
              </div>
              <div className="text-zinc-400 text-[10px] space-y-0.5 pt-1">
                <div>Verification failed → Mission state reassessed</div>
                <div>↳ Dynamic agent replanning → Alternative response selected: <strong className="text-emerald-400">SAFE_MODE (Hover)</strong></div>
                <div>↳ Actuator transition dispatched → Secondary verification pending</div>
              </div>
            </div>
          </div>
        )}

        {/* 3. Recovery Successful */}
        {verification && verification.verified && !authRequiredAction && (
          <div className="border border-emerald-500/60 bg-emerald-950/20 rounded-lg p-4 animate-in zoom-in-95 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm font-mono">
                <CheckCircle className="w-5 h-5 shrink-0" />
                <span>RECOVERY VERIFIED (PASSED)</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/40">
                SAFETY RESTORED
              </span>
            </div>

            <div className="p-2.5 bg-zinc-950/60 rounded border border-emerald-900/40 text-xs font-mono space-y-1">
              <div>
                Active Navigation Mode: <span className="text-emerald-300 font-bold">SAFE_MODE (Controlled Station Keep)</span>
              </div>
              <div>
                Position Residual: <span className="text-emerald-300 font-bold">{verification.position_residual ?? 0.08}m (Drift arrested)</span>
              </div>
              <div>
                Operational Risk: <span className="text-emerald-300 font-bold">LOW (0.08)</span>
              </div>
              <div className="text-zinc-400 text-[11px] pt-1">
                {verification.reason}
              </div>
            </div>

            <div className="pt-1 text-xs font-mono font-bold text-emerald-400 flex items-center gap-1.5">
              <span>●</span>
              <span>AEGIS AUTONOMOUS INCIDENT RESPONSE CONCLUDED SUCCESSFULLY</span>
            </div>
          </div>
        )}

        {/* Default / Idle State */}
        {!authRequiredAction && !verification && (
          <div className="flex flex-col items-center justify-center text-xs font-mono text-zinc-500 border border-dashed border-zinc-800 rounded-lg p-6 text-center space-y-1">
            <span className="font-bold text-zinc-400">GOVERNANCE GATE: ACTIVE</span>
            <span className="text-[11px] text-zinc-500">
              Actions requiring authorization or undergoing post-action verification will hold here.
            </span>
          </div>
        )}
      </div>

      <div className="text-[10px] font-mono text-zinc-500 pt-3 border-t border-zinc-800/60 flex justify-between">
        <span>AUTHORITATIVE ACTUATOR: ENFORCED</span>
        <span>GOVERNANCE: ZERO TRUST</span>
      </div>
    </div>
  );
}
