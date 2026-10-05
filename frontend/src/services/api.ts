import type { NetworkResponse, HazardInput, EngineTimelineResult } from '../types/network';

const API_BASE = '/api';

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchNetwork(): Promise<NetworkResponse> {
  const res = await fetch(`${API_BASE}/network`);
  if (!res.ok) {
    throw new Error(`Failed to load network: ${res.statusText}`);
  }
  return res.json();
}

export async function simulateHazard(hazard: HazardInput): Promise<EngineTimelineResult> {
  const res = await fetch(`${API_BASE}/hazard`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(hazard),
  });
  if (!res.ok) {
    throw new Error(`Hazard simulation failed: ${res.statusText}`);
  }
  return res.json();
}
