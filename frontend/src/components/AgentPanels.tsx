import { CheckCircle, AlertTriangle, Clock } from 'lucide-react';
import { useSimulator } from '../context/SimulatorContext';

export function AgentTrace() {
  const { events } = useSimulator();
  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full overflow-y-auto min-h-[200px] max-h-[300px]">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4 flex items-center gap-2">
        <Clock className="w-4 h-4 text-purple-400" />
        Agent Investigation Trace
      </h2>
      <div className="space-y-2 font-mono text-sm">
        {events.length === 0 && (
          <div className="text-zinc-500 italic">Waiting for incident...</div>
        )}
        {events.map((e, idx) => (
          <div key={idx} className="flex items-start gap-3 text-zinc-400 animate-in slide-in-from-left-2 fade-in">
            {e.status === 'completed' ? (
              <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
            ) : e.status === 'failed' ? (
              <AlertTriangle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
            ) : (
              <div className="w-4 h-4 rounded-full border-2 border-zinc-600 flex items-center justify-center mt-0.5 shrink-0">
                <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-pulse"></div>
              </div>
            )}
            <div className="flex flex-col">
              <span className="text-zinc-200">{e.tool}()</span>
              <span className="text-xs text-zinc-500">{e.summary}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function EvidencePanel() {
  const { evidence, hypotheses } = useSimulator();
  
  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 h-full">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Evidence & Hypotheses</h2>
      
      <div className="mb-6 space-y-2">
        <h3 className="text-xs text-zinc-500 font-semibold mb-2">EVIDENCE</h3>
        {evidence.length === 0 && <div className="text-xs text-zinc-600">No evidence gathered yet.</div>}
        {evidence.map(e => (
          <div key={e.id} className="p-2 bg-zinc-800/30 rounded border border-zinc-800/50">
            <div className="text-xs font-mono text-zinc-400 mb-1">{e.id}</div>
            <div className="text-sm text-zinc-200">{e.description}</div>
            <div className="text-xs text-zinc-500 mt-1">Source: {e.source}</div>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <h3 className="text-xs text-zinc-500 font-semibold mb-2">HYPOTHESES</h3>
        {hypotheses.length === 0 && <div className="text-xs text-zinc-600">No hypotheses generated yet.</div>}
        {hypotheses.map(h => (
          <div key={h.id} className="p-2 bg-zinc-800/30 rounded border border-zinc-800/50 flex justify-between items-center" style={{ opacity: h.confidence > 0.5 ? 1 : 0.5 }}>
            <div className="flex gap-2">
              <span className="text-xs font-mono text-zinc-400">{h.id}</span>
              <span className="text-sm text-zinc-200">{h.description}</span>
            </div>
            <div className="text-sm font-mono text-amber-400">{(h.confidence * 100).toFixed(0)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}
