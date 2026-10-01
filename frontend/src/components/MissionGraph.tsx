import { useMemo } from 'react';
import { ReactFlow, Controls, Background, MarkerType } from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useSimulator } from '../context/SimulatorContext';

export function MissionGraph() {
  const { state } = useSimulator();
  const isGpsDegraded = state.gps_trust < 0.75 || Boolean(state.gps_fault_active);
  const isSafeMode = state.navigation_mode === 'SAFE_MODE' || state.mission_status === 'SAFE_MODE';
  const isInertial = state.navigation_mode === 'INERTIAL';

  const nodes = useMemo<Node[]>(() => {
    // 1. GPS Node
    const gpsStatusLabel = isSafeMode
      ? 'ISOLATED'
      : isGpsDegraded
      ? `DEGRADED (${(state.gps_trust * 100).toFixed(0)}%)`
      : `NOMINAL (${(state.gps_trust * 100).toFixed(0)}%)`;
    const gpsBorder = isSafeMode ? '#64748b' : isGpsDegraded ? '#ef4444' : '#22c55e';
    const gpsColor = isSafeMode ? '#94a3b8' : isGpsDegraded ? '#f87171' : '#4ade80';

    // 2. IMU Node
    const imuStatusLabel = isInertial
      ? `PRIMARY ACTIVE (${(state.imu_trust * 100).toFixed(0)}%)`
      : `NOMINAL (${(state.imu_trust * 100).toFixed(0)}%)`;

    // 3. Position Estimation Node
    const posStatusLabel = isSafeMode
      ? 'SAFE HOVER'
      : isGpsDegraded
      ? 'AFFECTED'
      : 'HEALTHY';
    const posBorder = isSafeMode ? '#22c55e' : isGpsDegraded ? '#f97316' : '#27272a';
    const posColor = isSafeMode ? '#4ade80' : isGpsDegraded ? '#fb923c' : '#a1a1aa';

    // 4. Navigation Node
    const navStatusLabel = isSafeMode
      ? 'SAFE MODE'
      : isGpsDegraded
      ? 'AFFECTED'
      : 'NORMAL';
    const navBorder = isSafeMode ? '#22c55e' : isGpsDegraded ? '#ef4444' : '#27272a';
    const navColor = isSafeMode ? '#4ade80' : isGpsDegraded ? '#f87171' : '#a1a1aa';

    // 5. Route Following Node
    const routeStatusLabel = isSafeMode
      ? 'SUSPENDED'
      : isGpsDegraded
      ? 'AFFECTED'
      : 'TRACKING';
    const routeBorder = isSafeMode ? '#64748b' : isGpsDegraded ? '#f97316' : '#27272a';
    const routeColor = isSafeMode ? '#94a3b8' : isGpsDegraded ? '#fb923c' : '#a1a1aa';

    // 6. Mission Progress Node
    const progressStatusLabel = isSafeMode
      ? 'RESTORED'
      : isGpsDegraded
      ? 'AT RISK'
      : 'ON TARGET';
    const progressBorder = isSafeMode ? '#22c55e' : isGpsDegraded ? '#f59e0b' : '#27272a';
    const progressColor = isSafeMode ? '#4ade80' : isGpsDegraded ? '#fbbf24' : '#a1a1aa';

    return [
      {
        id: 'gps',
        position: { x: 30, y: 150 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">GPS Receiver</div>
              <div className="text-[10px] mt-0.5 font-bold" style={{ color: gpsColor }}>
                {gpsStatusLabel}
              </div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${gpsBorder}`,
          borderRadius: '8px',
          padding: '8px 12px',
          boxShadow: isGpsDegraded && !isSafeMode ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'none',
        },
      },
      {
        id: 'imu',
        position: { x: 30, y: 40 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">IMU Sensor</div>
              <div className="text-[10px] mt-0.5 text-emerald-400 font-bold">{imuStatusLabel}</div>
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
              <div className="font-bold text-xs text-white">Position Estimation</div>
              <div className="text-[10px] mt-0.5 font-bold" style={{ color: posColor }}>
                {posStatusLabel}
              </div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${posBorder}`,
          borderRadius: '8px',
          padding: '8px 12px',
          boxShadow: isGpsDegraded && !isSafeMode ? '0 0 12px rgba(249, 115, 22, 0.25)' : 'none',
        },
      },
      {
        id: 'nav',
        position: { x: 420, y: 95 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">Navigation</div>
              <div className="text-[10px] mt-0.5 font-bold" style={{ color: navColor }}>
                {navStatusLabel}
              </div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${navBorder}`,
          borderRadius: '8px',
          padding: '8px 12px',
          boxShadow: isGpsDegraded && !isSafeMode ? '0 0 12px rgba(239, 68, 68, 0.25)' : 'none',
        },
      },
      {
        id: 'route',
        position: { x: 610, y: 95 },
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="font-bold text-xs text-white">Route Following</div>
              <div className="text-[10px] mt-0.5 font-bold" style={{ color: routeColor }}>
                {routeStatusLabel}
              </div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${routeBorder}`,
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
              <div className="text-[10px] mt-0.5 font-bold" style={{ color: progressColor }}>
                {progressStatusLabel}
              </div>
            </div>
          ),
        },
        style: {
          background: '#09090b',
          color: '#f4f4f5',
          border: `1.5px solid ${progressBorder}`,
          borderRadius: '8px',
          padding: '8px 12px',
        },
      },
    ];
  }, [state.gps_trust, state.imu_trust, isGpsDegraded, isSafeMode, isInertial]);

  const edges = useMemo<Edge[]>(() => {
    const e1Color = isSafeMode ? '#64748b' : isGpsDegraded ? '#ef4444' : '#22c55e';
    const e2Color = '#22c55e';
    const e3Color = isSafeMode ? '#22c55e' : isGpsDegraded ? '#f97316' : '#3f3f46';
    const e4Color = isSafeMode ? '#64748b' : isGpsDegraded ? '#f97316' : '#3f3f46';
    const e5Color = isSafeMode ? '#22c55e' : isGpsDegraded ? '#f59e0b' : '#3f3f46';

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
        style: { stroke: e3Color, strokeWidth: isGpsDegraded ? 2.2 : 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e3Color },
      },
      {
        id: 'e4',
        source: 'nav',
        target: 'route',
        animated: !isSafeMode && isGpsDegraded,
        style: { stroke: e4Color, strokeWidth: isGpsDegraded ? 2 : 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e4Color },
      },
      {
        id: 'e5',
        source: 'route',
        target: 'progress',
        animated: !isSafeMode && isGpsDegraded,
        style: { stroke: e5Color, strokeWidth: isGpsDegraded ? 2 : 1.5 },
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
