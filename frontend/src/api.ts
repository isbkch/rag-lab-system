import { API_URL, logError } from "./config";

export interface Scenario {
  id: string;
  title: string;
  description: string;
  component: string;
  default_parameters: Record<string, unknown>;
}

export interface ScenarioRun {
  id: string;
  scenario_id: string;
  status: "queued" | "running" | "completed" | "failed";
  parameters: Record<string, unknown>;
  summary: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface LabEvent {
  id: string;
  run_id: string | null;
  component: string;
  severity: "info" | "warning" | "error";
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ComponentStatus {
  status: "healthy" | "degraded" | string;
  error?: string;
  backlog?: number | null;
  detail?: unknown;
}

export interface LabStatus {
  status: "healthy" | "degraded" | string;
  components: Record<string, ComponentStatus>;
  degraded_components: string[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });

  if (!response.ok) {
    const body = await response.text();
    logError("API request failed", response.status, path, body);
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function listScenarios(): Promise<Scenario[]> {
  const payload = await request<{ scenarios: Scenario[] }>("/lab/scenarios");
  return payload.scenarios;
}

export async function runScenario(
  scenarioId: string,
  parameters: Record<string, unknown> = {}
): Promise<ScenarioRun> {
  return request<ScenarioRun>(`/lab/scenarios/${scenarioId}/run`, {
    method: "POST",
    body: JSON.stringify(parameters),
  });
}

export async function listRuns(limit = 12): Promise<ScenarioRun[]> {
  const payload = await request<{ runs: ScenarioRun[] }>(`/lab/runs?limit=${limit}`);
  return payload.runs;
}

export async function listEvents(limit = 30): Promise<LabEvent[]> {
  const payload = await request<{ events: LabEvent[] }>(
    `/lab/events?limit=${limit}`
  );
  return payload.events;
}

export async function getStatus(): Promise<LabStatus> {
  return request<LabStatus>("/lab/status");
}
