/**
AEGIS Canonical Demo API Client
Connects to backend /api/v1/demo orchestration endpoints and WebSocket event stream.
*/

import { apiClient } from './client';

export interface DemoTraceStep {
  step_id: string;
  sequence: number;
  phase: string;
  tool: string;
  status: string;
  started_at: number;
  completed_at: number;
  summary: string;
  result?: Record<string, any>;
}

export interface DemoResult {
  demo_id: string;
  status: string;
  agent_mode: string;
  started_at: number;
  completed_at: number;
  duration_seconds: number;
  incident: Record<string, any>;
  investigation: Record<string, any>;
  hypotheses: Array<Record<string, any>>;
  mission_impact: Record<string, any>;
  dependency_graph?: Record<string, any>;
  actions: Array<Record<string, any>>;
  selected_action?: string;
  simulation: Record<string, any>;
  policy: Record<string, any>;
  execution: Record<string, any>;
  verification: Record<string, any>;
  replanning: Record<string, any>;
  recovery: Record<string, any>;
  final_state: Record<string, any>;
  trace: DemoTraceStep[];
}

export async function runDemo(autoAuthorize = true): Promise<DemoResult> {
  return apiClient<DemoResult>(`/api/v1/demo/run?auto_authorize=${autoAuthorize}`, {
    method: 'POST',
  });
}

export async function resetDemo(): Promise<{ status: string; phase: string; state: Record<string, any> }> {
  return apiClient<{ status: string; phase: string; state: Record<string, any> }>('/api/v1/demo/reset', {
    method: 'POST',
  });
}

export async function fetchDemoState(): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>('/api/v1/demo/state', {
    method: 'GET',
  });
}

export async function fetchDemoTrace(): Promise<DemoTraceStep[]> {
  return apiClient<DemoTraceStep[]>('/api/v1/demo/trace', {
    method: 'GET',
  });
}

export async function fetchDemoEvents(): Promise<Array<Record<string, any>>> {
  return apiClient<Array<Record<string, any>>>('/api/v1/demo/events', {
    method: 'GET',
  });
}

export function createDemoWebSocket(
  onEvent: (event: any) => void,
  onError?: (err: any) => void
): WebSocket | null {
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use window.location.host or direct localhost:8000
    const wsUrl = `${protocol}//${window.location.host}/ws/demo`;
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        onEvent(parsed);
      } catch {
        console.debug('Non-JSON WebSocket message received:', event.data);
      }
    };

    socket.onerror = (err) => {
      if (onError) onError(err);
    };

    return socket;
  } catch (err) {
    if (onError) onError(err);
    return null;
  }
}
