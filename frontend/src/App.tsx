import { useEffect, useMemo, useState } from "react";
import {
  getStatus,
  listEvents,
  listRuns,
  listScenarios,
  runScenario,
  type LabEvent,
  type LabStatus,
  type Scenario,
  type ScenarioRun,
} from "./api";

const componentLabels: Record<string, string> = {
  postgres: "Postgres",
  redis: "Redis",
  chromadb: "ChromaDB",
  mock_ai: "Mock AI",
  worker_queue: "Worker Queue",
};

function formatTime(value: string | null): string {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function statusClass(status: string): string {
  if (status === "healthy" || status === "completed") return "status-good";
  if (status === "failed" || status === "degraded") return "status-bad";
  return "status-warn";
}

function encodeJson(value: Record<string, unknown>): string {
  const keys = Object.keys(value);
  if (keys.length === 0) return "";
  return JSON.stringify(value);
}

export default function App() {
  const [status, setStatus] = useState<LabStatus | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [runs, setRuns] = useState<ScenarioRun[]>([]);
  const [events, setEvents] = useState<LabEvent[]>([]);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const scenarioById = useMemo(
    () => new Map(scenarios.map((scenario) => [scenario.id, scenario])),
    [scenarios]
  );

  async function refresh() {
    const [nextStatus, nextScenarios, nextRuns, nextEvents] = await Promise.all([
      getStatus(),
      listScenarios(),
      listRuns(),
      listEvents(),
    ]);
    setStatus(nextStatus);
    setScenarios(nextScenarios);
    setRuns(nextRuns);
    setEvents(nextEvents);
  }

  useEffect(() => {
    refresh().catch(() => setError("Unable to load lab state."));
    const id = window.setInterval(() => {
      refresh().catch(() => setError("Unable to refresh lab state."));
    }, 5000);
    return () => window.clearInterval(id);
  }, []);

  async function handleRun(scenario: Scenario) {
    setRunningId(scenario.id);
    setError(null);
    try {
      await runScenario(scenario.id, scenario.default_parameters);
      await refresh();
    } catch {
      setError(`Unable to queue ${scenario.title}.`);
    } finally {
      setRunningId(null);
    }
  }

  return (
    <main className="lab-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local failure lab</p>
          <h1>Failure Laboratory</h1>
        </div>
        <nav className="links" aria-label="Monitoring links">
          <a href="http://localhost:9090" target="_blank" rel="noreferrer">
            Prometheus
          </a>
          <a href="http://localhost:3001" target="_blank" rel="noreferrer">
            Grafana
          </a>
        </nav>
      </header>

      {error && <div className="alert">{error}</div>}

      <section className="status-strip" aria-label="Component status">
        {Object.entries(status?.components || {}).map(([key, value]) => (
          <div className="status-cell" key={key}>
            <span className={`status-dot ${statusClass(value.status)}`} />
            <div>
              <span>{componentLabels[key] || key}</span>
              <strong>{value.status}</strong>
            </div>
            {typeof value.backlog === "number" && (
              <small>{value.backlog} queued</small>
            )}
          </div>
        ))}
      </section>

      <section className="grid">
        <div className="panel scenario-panel">
          <div className="panel-heading">
            <h2>Scenarios</h2>
            <span>{scenarios.length}</span>
          </div>
          <div className="scenario-list">
            {scenarios.map((scenario) => (
              <article className="scenario" key={scenario.id}>
                <div>
                  <p className="component">{scenario.component}</p>
                  <h3>{scenario.title}</h3>
                  <p>{scenario.description}</p>
                  <code>{encodeJson(scenario.default_parameters)}</code>
                </div>
                <button
                  type="button"
                  onClick={() => handleRun(scenario)}
                  disabled={runningId === scenario.id}
                >
                  {runningId === scenario.id ? "Queueing" : "Run"}
                </button>
              </article>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-heading">
            <h2>Recent Runs</h2>
            <span>{runs.length}</span>
          </div>
          <div className="run-list">
            {runs.map((run) => (
              <article className="run" key={run.id}>
                <span className={`pill ${statusClass(run.status)}`}>
                  {run.status}
                </span>
                <div>
                  <strong>
                    {scenarioById.get(run.scenario_id)?.title || run.scenario_id}
                  </strong>
                  <small>{formatTime(run.created_at)}</small>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className="panel event-panel">
          <div className="panel-heading">
            <h2>Event Stream</h2>
            <span>{events.length}</span>
          </div>
          <div className="event-list">
            {events.map((event) => (
              <article className="event" key={event.id}>
                <span className={`rail ${statusClass(event.severity)}`} />
                <div>
                  <div className="event-meta">
                    <strong>{event.component}</strong>
                    <small>{formatTime(event.created_at)}</small>
                  </div>
                  <p>{event.message}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
