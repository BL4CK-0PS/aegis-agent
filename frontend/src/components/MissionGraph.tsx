import { useMemo } from 'react';
import { ReactFlow, Controls, Background, MarkerType } from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useSimulator } from '../context/SimulatorContext';

export function MissionGraph() {
  const { state } = useSimulator();
  const isGpsDegraded = state.gps_trust < 0.5;
  const isSafeMode = state.navigation_mode === 'SAFE_MODE';
  const isInertial = state.navigation_mode === 'INERTIAL';

  const nodes = useMemo<Node[]>(() => {
    const gpsStatusLabel = isSafeMode
      ? 'ISOLATED'
      : isGpsDegraded
      ? '🔴 DEGRADED (31%)'
      : '🟢 NOMINAL (98%)';
    const gpsBorder = isSafeMode ? '#64748b' : isGpsDegraded ? '#ef4444' : '#22c55e';

    const imuStatusLabel = isInertial
      ? '🟡 PRIMARY ACTIVE'
      : '🟢 NOMINAL (95%)';

    const posStatusLabel = isSafeMode
      ? '🟢 SAFE HOVER'
      : isGpsDegraded
      ? '🟠 AFFECTED'
      : '🟢 HEALTHY';
    const posBorder = isSafeMode ? '#22c55e' : isGpsDegraded ? '#f97316' : '#27272a';

    const navStatusLabel = isSafeMode
      ? '🟢 SAFE MODE'
      : isGpsDegraded
      ? '🔴 HIGH IMPACT'
      : '🟢 NORMAL';
    const navBorder = isSafeMode ? '#22c55e' : isGpsDegraded ? '#ef4444' : '#27272a';

    const routeStatusLabel = isSafeMode
      ? '⚪ SUSPENDED'
      : isGpsDegraded
      ? '🟠 AFFECTED'
      : '🟢 TRACKING';

    const progressStatusLabel = isSafeMode
      ? '🟢 RESTORED'
      : isGpsDegraded
      ? '🟠 AT RISK'
      : '🟢 ON TARGET';

    return [
      {
        id: 'gps',
        position: { x: 30, y: 150 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">GPS Receiver</div>
              <div className="text-[10px] mt-0.5">{gpsStatusLabel}</div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${gpsBorder}`,
          borderRadius: '8px',
          padding: '8px 12px',
          boxShadow: isGpsDegraded && !isSafeMode ? '0 0 12px rgba(239, 68, 68, 0.3)' : 'none',
        },
      },
      {
        id: 'imu',
        position: { x: 30, y: 40 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">IMU Sensor</div>
              <div className="text-[10px] mt-0.5">{imuStatusLabel}</div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: '1.5px solid #22c55e',
          borderRadius: '8px',
          padding: '8px 12px',
        },
      },
      {
        id: 'pos_est',
        position: { x: 230, y: 95 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">State Estimator</div>
              <div className="text-[10px] mt-0.5">{posStatusLabel}</div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${posBorder}`,
          borderRadius: '8px',
          padding: '8px 12px',
        },
      },
      {
        id: 'nav',
        position: { x: 420, y: 95 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">Flight Navigation</div>
              <div className="text-[10px] mt-0.5">{navStatusLabel}</div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${navBorder}`,
          borderRadius: '8px',
          padding: '8px 12px',
        },
      },
      {
        id: 'route',
        position: { x: 610, y: 95 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">Route Following</div>
              <div className="text-[10px] mt-0.5">{routeStatusLabel}</div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: '1.5px solid #27272a',
          borderRadius: '8px',
          padding: '8px 12px',
        },
      },
      {
        id: 'progress',
        position: { x: 800, y: 95 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">Mission Progress</div>
              <div className="text-[10px] mt-0.5">{progressStatusLabel}</div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: isSafeMode ? '1.5px solid #22c55e' : '1.5px solid #27272a',
          borderRadius: '8px',
          padding: '8px 12px',
        },
      },
    ];
  }, [state.gps_trust, state.navigation_mode, isGpsDegraded, isSafeMode, isInertial]);

  const edges = useMemo<Edge[]>(() => {
    const e1Color = isSafeMode ? '#64748b' : isGpsDegraded ? '#ef4444' : '#22c55e';
    const e2Color = '#22c55e';
    const e3Color = isSafeMode ? '#22c55e' : isGpsDegraded ? '#f97316' : '#3f3f46';
    const e4Color = isSafeMode ? '#64748b' : isGpsDegraded ? '#f97316' : '#3f3f46';
    const e5Color = isSafeMode ? '#22c55e' : '#3f3f46';

    return [
      {
        id: 'e1',
        source: 'gps',
        target: 'pos_est',
        animated: isGpsDegraded,
        style: { stroke: e1Color, strokeWidth: isGpsDegraded ? 2.5 : 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e1Color },
      },
      {
        id: 'e2',
        source: 'imu',
        target: 'pos_est',
        animated: true,
        style: { stroke: e2Color, strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e2Color },
      },
      {
        id: 'e3',
        source: 'pos_est',
        target: 'nav',
        animated: isGpsDegraded,
        style: { stroke: e3Color, strokeWidth: isGpsDegraded ? 2 : 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e3Color },
      },
      {
        id: 'e4',
        source: 'nav',
        target: 'route',
        animated: !isSafeMode && isGpsDegraded,
        style: { stroke: e4Color, strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e4Color },
      },
      {
        id: 'e5',
        source: 'route',
        target: 'progress',
        animated: false,
        style: { stroke: e5Color, strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e5Color },
      },
    ];
  }, [isGpsDegraded, isSafeMode]);

  return (
    <div className="w-full h-full min-h-[280px]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        className="bg-zinc-950/60"
        colorMode="dark"
      >
        <Background color="#27272a" gap={16} />
        <Controls className="!bg-zinc-900 !border-zinc-800 !fill-zinc-400" />
      </ReactFlow>
    </div>
  );
}
