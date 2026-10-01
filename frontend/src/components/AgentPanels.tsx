import { useState } from 'react';
import { CheckCircle, AlertTriangle, ShieldAlert, Cpu, Sparkles, Database } from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function AgentTrace() {
  const { events, lifecyclePhase, replanCount } = useSimulator();

  const formatToolName = (tool: string) => {
    return tool.replace(/_/g, ' ').toUpperCase();
  };

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4 border-b border-zinc-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider">
            Agent Investigation Trace
          </h2>
          {replanCount > 0 && (
            <span className="text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded animate-pulse">
              REPLAN #{replanCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-mono text-zinc-400">
            PHASE: <strong className="text-cyan-400">{lifecyclePhase}</strong>
          </span>
          <span className="text-xs font-mono text-zinc-500">
            {events.length > 0 ? `${events.length} STEPS` : 'IDLE'}
          </span>
        </div>
      </div>

      <div className="space-y-3 font-mono text-xs overflow-y-auto max-h-[380px] pr-2">
        {events.length === 0 && (
          <div className="text-zinc-500 italic py-8 text-center border border-dashed border-zinc-800 rounded-lg flex flex-col items-center justify-center gap-2">
            <Cpu className="w-6 h-6 text-zinc-600 animate-pulse" />
            <span>Waiting for incident trigger... Click [ RUN INCIDENT ] to initiate autonomous decision cycle.</span>
          </div>
        )}

        {events.map((e, idx) => {
          const isComplete = e.status === 'completed';
          const isFailed = e.status === 'failed' || e.status === 'error';
          const isAuth = e.status === 'awaiting_authorization';

          const badgeText = isComplete
            ? 'COMPLETE'
            : isFailed
            ? 'FAILED'
            : isAuth
            ? 'AUTH REQUIRED'
            : 'RUNNING';

          const badgeColor = isComplete
            ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
            : isFailed
            ? 'text-rose-400 bg-rose-500/10 border-rose-500/20'
            : isAuth
            ? 'text-amber-400 bg-amber-500/10 border-amber-500/20 animate-pulse'
            : 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20';

          return (
            <div
              key={idx}
              className={`p-3 rounded-lg border transition-all flex flex-col gap-1.5 ${
                isFailed
                  ? 'bg-rose-950/20 border-rose-800/50'
                  : isAuth
                  ? 'bg-amber-950/20 border-amber-700/50 shadow-[0_0_10px_rgba(245,158,11,0.1)]'
                  : 'bg-zinc-950/60 border-zinc-800/70 hover:border-zinc-700/80'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold">
                  {isComplete ? (
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : isFailed ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                  ) : isAuth ? (
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                  )}
                  <span className="text-cyan-300">
                    ● {String(e.step || idx + 1).padStart(2, '0')}
                  </span>
                  <span className="text-zinc-100 tracking-wide font-semibold">
                    {formatToolName(e.tool)}
                  </span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}`}>
                  {badgeText}
                </span>
              </div>

              {/* Informative summary & findings */}
              <div className="pl-6 space-y-1">
                <div className={`${isFailed ? 'text-rose-300 font-semibold' : 'text-zinc-300'} text-xs`}>
                  {e.summary}
                </div>
                {e.subdetails && e.subdetails.length > 0 && (
                  <div className="text-[11px] text-zinc-500 space-y-0.5 pt-0.5">
                    {e.subdetails.map((sub, sIdx) => (
                      <div key={sIdx} className="flex items-center gap-1.5 text-zinc-400">
                        <span className={isFailed ? 'text-rose-500' : 'text-cyan-600'}>↳</span>
                        <span>{sub}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function EvidencePanel() {
  const { evidence, hypotheses } = useSimulator();
  const [selectedHypothesis, setSelectedHypothesis] = useState<string | null>(null);

  // Baseline fallbacks if backend is just initializing
  const displayEvidence = evidence;
  const displayHypotheses = hypotheses;

  // Highest confidence hypothesis is marked as primary
  const topHypothesis = displayHypotheses.length > 0
    ? displayHypotheses.reduce(
        (prev, current) => (current.confidence > prev.confidence ? current : prev),
        displayHypotheses[0]
      )
    : null;

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col gap-5">
      <div>
        <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider mb-3 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            Evidence & Hypotheses
          </span>
          <span className="text-[10px] text-cyan-400 bg-cyan-950/40 border border-cyan-800/50 px-2 py-0.5 rounded font-mono">
            AUTHORITATIVE FUSION
          </span>
        </h2>

        {/* Evidence Section */}
        <div className="space-y-2">
          <div className="text-[11px] font-mono uppercase text-zinc-400 tracking-wider flex items-center justify-between">
            <span>Authoritative Evidence ({displayEvidence.length})</span>
            <span className="text-[10px] text-zinc-500">RESIDUAL / TRUST PROVENANCE</span>
          </div>

          {displayEvidence.length === 0 ? (
            <div className="text-zinc-500 italic py-6 text-center border border-dashed border-zinc-800 rounded-lg flex flex-col items-center justify-center gap-1.5 font-mono text-xs">
              <Database className="w-5 h-5 text-zinc-600 mb-1" />
              <span>No active sensor evidence gathered. Initiate incident response loop to calibrate telemetry.</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {displayEvidence.map(ev => {
                const isAlert = ev.severity === 'CRITICAL' || ev.severity === 'HIGH';
                return (
                  <div
                    key={ev.id}
                    className={`p-3 rounded-lg border flex flex-col justify-between transition-all ${
                      isAlert
                        ? 'bg-rose-950/20 border-rose-800/40'
                        : 'bg-zinc-950/60 border-zinc-800/80 hover:border-zinc-700/70'
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start text-xs mb-1">
                        <span className="text-zinc-400 font-mono text-[11px] truncate max-w-[150px]">
                          {ev.metric}
                        </span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-800/60 text-zinc-400 border border-zinc-700/50">
                          {ev.id}
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between mt-1">
                        <div
                          className={`text-base font-bold font-mono ${
                            isAlert ? 'text-rose-400' : 'text-zinc-100'
                          }`}
                        >
                          {ev.value}
                        </div>
                        <div className="text-[11px] font-mono font-bold text-cyan-400">
                          Confidence {(ev.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                      {ev.relationship && (
                        <div className="mt-1.5 text-[10px] font-mono text-zinc-400 flex items-center gap-1">
                          <span className="text-cyan-500">↳</span>
                          <span>{ev.relationship}</span>
                        </div>
                      )}
                    </div>

                    <div className="mt-2 pt-2 border-t border-zinc-800/60 flex justify-between items-center text-[10px] font-mono text-zinc-500">
                      <span className="truncate max-w-[180px]">{ev.source}</span>
                      <span
                        className={`px-1 rounded text-[9px] font-bold ${
                          isAlert
                            ? 'bg-rose-500/20 text-rose-300'
                            : 'bg-zinc-800 text-zinc-400'
                        }`}
                      >
                        {ev.severity}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Competing Hypotheses Section */}
      <div className="space-y-2 pt-2 border-t border-zinc-800/70">
        <div className="text-[11px] font-mono uppercase text-zinc-400 tracking-wider flex items-center justify-between">
          <span>Competing Hypotheses ({displayHypotheses.length})</span>
          <span className="text-[10px] text-zinc-500">BAYESIAN LIKELIHOOD</span>
        </div>

        {displayHypotheses.length === 0 ? (
          <div className="text-zinc-500 italic py-6 text-center border border-dashed border-zinc-800 rounded-lg flex flex-col items-center justify-center gap-1.5 font-mono text-xs">
            <Sparkles className="w-5 h-5 text-zinc-600 mb-1" />
            <span>No active hypotheses formed. Awaiting sensor evidence.</span>
          </div>
        ) : (
          <div className="space-y-2">
          {displayHypotheses.map(h => {
            const isTop = h.id === topHypothesis?.id && h.confidence > 0.4;
            const isSelected = selectedHypothesis === h.id;

            return (
              <div
                key={h.id}
                onClick={() => setSelectedHypothesis(isSelected ? null : h.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  isTop
                    ? 'bg-cyan-950/30 border-cyan-500/60 shadow-[0_0_12px_rgba(6,182,212,0.15)]'
                    : 'bg-zinc-950/50 border-zinc-800/60 opacity-75 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-cyan-400">
                      {h.id}
                    </span>
                    <span className="text-xs font-semibold text-zinc-200">
                      {h.description}
                    </span>
                    {isTop && (
                      <span className="text-[9px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 px-1.5 py-0.5 rounded flex items-center gap-1">
                        <Sparkles className="w-2.5 h-2.5" />
                        PRIMARY LEAD
                      </span>
                    )}
                  </div>
                  <span className="text-sm font-bold font-mono text-amber-400">
                    Confidence: {(h.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                {h.explanation && (
                  <div className="mt-1.5 text-[11px] text-zinc-400 leading-relaxed font-sans">
                    {h.explanation}
                  </div>
                )}

                <div className="mt-2 pt-1.5 border-t border-zinc-800/40 flex items-center gap-4 text-[10px] font-mono text-zinc-400">
                  <span className="text-emerald-400">
                    Supporting evidence: {h.supporting_evidence ? h.supporting_evidence.join(', ') : h.supportingEvidence ?? 3}
                  </span>
                  {h.contradictingEvidence !== undefined && (
                    <span className="text-zinc-500">
                      Contradicting: {h.contradictingEvidence}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
          </div>
        )}
      </div>
    </div>
  );
}
