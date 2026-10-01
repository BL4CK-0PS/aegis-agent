
import { ReactFlow, Controls, Background, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useSimulator } from '../context/SimulatorContext';

export function MissionGraph() {
  const { state } = useSimulator();
  const gpsDegraded = state.gps_trust < 0.5;

  const nodes = [
    {
      id: 'gps',
      position: { x: 50, y: 150 },
      data: { label: 'GPS' },
      style: { background: '#18181b', color: '#f4f4f5', border: gpsDegraded ? '1px solid #eab308' : '1px solid #27272a' },
    },
    {
      id: 'imu',
      position: { x: 50, y: 50 },
      data: { label: 'IMU' },
      style: { background: '#18181b', color: '#f4f4f5', border: '1px solid #27272a' },
    },
    {
      id: 'pos_est',
      position: { x: 250, y: 100 },
      data: { label: 'Position Estimation' },
      style: { background: '#18181b', color: '#f4f4f5', border: state.mission_status === 'DEGRADED' ? '1px solid #f43f5e' : '1px solid #27272a' },
    },
    {
      id: 'nav',
      position: { x: 450, y: 100 },
      data: { label: 'Navigation' },
      style: { background: '#18181b', color: '#f4f4f5', border: '1px solid #27272a' },
    },
    {
      id: 'route',
      position: { x: 650, y: 100 },
      data: { label: 'Route Following' },
      style: { background: '#18181b', color: '#f4f4f5', border: '1px solid #27272a' },
    },
    {
      id: 'progress',
      position: { x: 850, y: 100 },
      data: { label: 'Mission Progress' },
      style: { background: '#18181b', color: '#f4f4f5', border: '1px solid #27272a' },
    }
  ];

  const edges = [
    { id: 'e1', source: 'gps', target: 'pos_est', animated: true, style: { stroke: gpsDegraded ? '#eab308' : '#3f3f46' }, markerEnd: { type: MarkerType.ArrowClosed, color: gpsDegraded ? '#eab308' : '#3f3f46' } },
    { id: 'e2', source: 'imu', target: 'pos_est', animated: true, style: { stroke: '#3f3f46' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' } },
    { id: 'e3', source: 'pos_est', target: 'nav', animated: true, style: { stroke: state.mission_status === 'DEGRADED' ? '#f43f5e' : '#3f3f46' }, markerEnd: { type: MarkerType.ArrowClosed, color: state.mission_status === 'DEGRADED' ? '#f43f5e' : '#3f3f46' } },
    { id: 'e4', source: 'nav', target: 'route', animated: true, style: { stroke: '#3f3f46' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' } },
    { id: 'e5', source: 'route', target: 'progress', animated: true, style: { stroke: '#3f3f46' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' } },
  ];

  return (
    <div className="w-full h-full min-h-[300px]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        className="bg-zinc-950/50"
        colorMode="dark"
      >
        <Background color="#3f3f46" gap={16} />
        <Controls className="!bg-zinc-900 !border-zinc-800 !fill-zinc-400" />
      </ReactFlow>
    </div>
  );
}
