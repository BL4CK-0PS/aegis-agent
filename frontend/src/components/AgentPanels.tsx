import { CheckCircle, AlertTriangle, ShieldAlert, Cpu } from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function AgentTrace() {
  const { events } = useSimulator();

  const formatToolName = (tool: string) => {
    return tool.replace(/_/g, ' ').toUpperCase();
  };

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4 border-b border-zinc-800/80 pb-3">
        <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          Agent Investigation Trace
        </h2>
        <span className="text-xs font-mono text-zinc-500">
          {events.length > 0 ? `${events.length} STEPS RECORDED` : 'IDLE'}
        </span>
      </div>

      <div className="space-y-3 font-mono text-xs overflow-y-auto max-h-[380px] pr-2">
        {events.length === 0 && (
          <div className="text-zinc-600 italic py-8 text-center border border-dashed border-zinc-800 rounded-lg">
            Waiting for incident trigger... Click [ RUN INCIDENT ] to initiate autonomous decision cycle.
          </div>
        )}

        {events.map((e, idx) => {
          const isComplete = e.status === 'completed';
          const isFailed = e.status === 'failed';
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
              className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800/70 hover:border-zinc-700/80 transition-all flex flex-col gap-1.5"
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

              {/* Multi-line findings */}
              <div className="pl-6 space-y-0.5">
                <div className="text-zinc-300 text-xs">{e.summary}</div>
                {e.subdetails && e.subdetails.length > 0 && (
                  <div className="text-[11px] text-zinc-500 space-y-0.5 pt-1">
                    {e.subdetails.map((sub, sIdx) => (
                      <div key={sIdx} className="flex items-center gap-1.5 text-zinc-400">
                        <span className="text-cyan-600">↳</span>
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

  // Fallback defaults for nominal showcase if empty
  const displayEvidence =
    evidence.length > 0
      ? evidence
      : [
          {
            id: 'E01',
            metric: 'GPS position residual',
            value: '0.00 m',
            confidence: 0.98,
            description: 'Euclidean distance between GPS receiver and state prediction',
            source: 'GPS / IMU comparison',
            severity: 'NOMINAL' as const,
          },
          {
            id: 'E02',
            metric: 'Mission telemetry',
            value: 'Consistent',
            confidence: 0.95,
            description: 'Triple-axis accelerations match command dynamics',
            source: 'Telemetry Anomaly Detector',
            severity: 'NOMINAL' as const,
          },
          {
            id: 'E03',
            metric: 'IMU trajectory',
            value: 'Consistent',
            confidence: 0.96,
            description: 'Kinematic inertial continuity within bounds',
            source: 'Inertial Measurement Unit',
            severity: 'NOMINAL' as const,
          },
        ];

  const displayHypotheses =
    hypotheses.length > 0
      ? hypotheses
      : [
          {
            id: '01',
            description: 'Nominal Navigation Performance',
            confidence: 0.98,
            supportingEvidence: 4,
            contradictingEvidence: 0,
          },
          {
            id: '02',
            description: 'Sensor noise',
            confidence: 0.02,
            supportingEvidence: 1,
            contradictingEvidence: 3,
          },
        ];

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full flex flex-col gap-6">
      <div>
        <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Evidence & Hypotheses</span>
          <span className="text-[10px] text-zinc-500 font-mono">AUDITABLE REASONING</span>
        </h2>

        {/* Evidence Section */}
        <div className="space-y-2">
          <div className="text-[11px] font-mono uppercase text-zinc-400 tracking-wider">
            Evidence Captured ({displayEvidence.length})
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
            {displayEvidence.map(ev => {
              const isAlert = ev.severity === 'HIGH';
              return (
                <div
                  key={ev.id}
                  className={`p-3 rounded-lg border flex flex-col justify-between ${
                    isAlert
                      ? 'bg-rose-950/20 border-rose-800/40'
                      : 'bg-zinc-950/60 border-zinc-800/80'
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start text-xs mb-1">
                      <span className="text-zinc-400 font-mono text-[11px]">{ev.metric}</span>
                      <span className="text-[10px] font-mono text-zinc-500">{ev.id}</span>
                    </div>
                    <div
                      className={`text-base font-bold font-mono ${
                        isAlert ? 'text-rose-400' : 'text-zinc-100'
                      }`}
                    >
                      {ev.value}
                    </div>
                  </div>
                  <div className="mt-2 pt-2 border-t border-zinc-800/50 flex justify-between items-center text-[10px] font-mono text-zinc-500">
                    <span>Conf: {(ev.confidence * 100).toFixed(0)}%</span>
                    <span className="truncate max-w-[110px]">{ev.source}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Hypotheses Section */}
      <div className="space-y-2">
        <div className="text-[11px] font-mono uppercase text-zinc-400 tracking-wider">
          Hypotheses Formed ({displayHypotheses.length})
        </div>
        <div className="space-y-2">
          {displayHypotheses.map(h => {
            const isTop = h.confidence > 0.5;
            return (
              <div
                key={h.id}
                className={`p-3 rounded-lg border transition-all ${
                  isTop
                    ? 'bg-cyan-950/20 border-cyan-800/50'
                    : 'bg-zinc-950/50 border-zinc-800/60 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-cyan-400">
                      {h.id.padStart(2, '0')}
                    </span>
                    <span className="text-xs font-semibold text-zinc-200">{h.description}</span>
                  </div>
                  <span className="text-sm font-bold font-mono text-amber-400">
                    {(h.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="mt-2 flex items-center gap-4 text-[10px] font-mono text-zinc-400">
                  <span className="text-emerald-400">
                    Supporting evidence: {h.supportingEvidence ?? 3}
                  </span>
                  <span className="text-zinc-500">
                    Contradicting evidence: {h.contradictingEvidence ?? 0}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
