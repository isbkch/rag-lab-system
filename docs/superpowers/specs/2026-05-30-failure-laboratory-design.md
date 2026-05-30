# Failure Laboratory Strip-Down Design

## Purpose

Repurpose this repository from an enterprise RAG starter kit into a failure
laboratory. The system should be useful for demonstrating dependency failures,
bad operational assumptions, recovery behavior, and observability gaps. It does
not need to be a complete RAG product.

## Alternatives Considered

### API-only lab

Keep only FastAPI and Docker Compose, expose scenario endpoints, and remove the
frontend. This is the smallest codebase, but it weakens the demo because users
must inspect failures through curl, logs, and Grafana only.

### Instrument the existing RAG product

Keep document upload, hybrid search, Elasticsearch, provider selection, and add
failure toggles. This preserves more code, but it keeps the distraction the
repurpose is meant to remove.

### Recommended: small failure lab with dashboard

Keep a small React dashboard because it helps the demo. Strip the backend to
one vector store, one mock external AI dependency, Postgres, Redis, Celery, and
Prometheus/Grafana. Make failure scenarios the primary product surface.

This is the approved direction.

## Scope

Keep:

- FastAPI backend.
- React frontend as a lab dashboard.
- PostgreSQL for metadata, scenario runs, and event records.
- Redis for cache and Celery broker/result backend.
- ChromaDB as the only vector database.
- A separate mock external AI service controlled by Docker Compose.
- Prometheus and Grafana.
- Celery worker queue.
- Docker Compose development workflow.

Remove or stop advertising:

- Pinecone and Weaviate code paths, dependencies, settings, and docs.
- Elasticsearch and keyword/hybrid search as required stack components.
- OpenAI as a required runtime dependency.
- Multi-provider vector database abstractions.
- Enterprise/product claims, generic RAG boilerplate, broad provider matrices,
  and production readiness language.
- Celery beat unless a specific scheduled failure scenario needs it.

## Architecture

The repository becomes a local distributed demo with these services:

- `backend`: FastAPI orchestration API.
- `frontend`: React dashboard for triggering scenarios and reading status.
- `postgres`: persistent lab metadata.
- `redis`: queue broker, result backend, and optional cache target.
- `chromadb`: single vector database dependency.
- `mock-ai`: controllable fake external AI service.
- `celery-worker`: executes scenario work and records events.
- `prometheus`: scrapes backend and mock service metrics.
- `grafana`: visualizes failure and recovery behavior.

The backend should mount a small v1 API:

- `/api/v1/health` for liveness/readiness/component checks.
- `/api/v1/lab/scenarios` to list available scenarios.
- `/api/v1/lab/scenarios/{scenario_id}/run` to enqueue or run a scenario.
- `/api/v1/lab/runs` to list recent scenario runs.
- `/api/v1/lab/events` to list recent event records.
- `/api/v1/lab/status` to summarize current component state.

Existing document and search routes should either be removed or reduced to a
single smoke-test path only if needed to demonstrate vector-store and mock-AI
failure behavior. They should not remain as a product-shaped document manager.

## Failure Scenarios

The first pass should include a focused scenario catalog:

- `mock_ai_timeout`: backend calls mock AI with a timeout and records failure.
- `mock_ai_500`: mock AI returns errors and backend records degraded behavior.
- `redis_unavailable`: queue or cache access fails and health/status reports it.
- `queue_backlog`: Celery job sleeps or fans out enough work to show backlog.
- `postgres_pool_pressure`: backend attempts bounded concurrent DB work and
  records timeout/pressure without crashing the process.
- `vector_latency`: Chroma-facing work is delayed or forced to fail through the
  scenario path.
- `stale_health`: a scenario can show how a shallow liveness check stays green
  while dependency status is degraded.

Scenarios should be explicit and bounded. They should not depend on real paid
AI providers or real customer documents.

## Data Model

Keep the database schema small:

- `scenario_runs`: run id, scenario id, status, started/completed timestamps,
  input parameters, summary, and error text.
- `lab_events`: timestamped event stream keyed by run id, component, severity,
  and message.

Document tables may be removed from the default schema unless the implementation
keeps a minimal vector smoke-test route that needs persisted chunks.

## Mock AI Service

The mock AI service should be a separate service in Compose so network,
timeout, 500, and latency behavior feels like a real external dependency. It
can be implemented as a tiny FastAPI app with endpoints such as:

- `GET /health`
- `POST /v1/complete`
- `POST /admin/mode`

Supported modes should include `normal`, `slow`, `error`, and `flaky`. The
backend should call it with short, explicit timeouts.

## Frontend

Replace the current RAG search/upload/document UI with a compact lab dashboard:

- Component status strip for backend, Postgres, Redis, ChromaDB, mock AI, and
  worker queue.
- Scenario list with run buttons and short failure descriptions.
- Recent runs table.
- Event stream panel.
- Links to Grafana and Prometheus.

The frontend should not claim to be a production platform or generic RAG tool.

## Observability

Keep `/metrics` in the backend. Metrics should focus on failure lab behavior:

- HTTP request counts and latency.
- Scenario run counts by scenario and status.
- Scenario duration histogram.
- Dependency check status.
- Queue/backlog gauges where practical.
- Mock AI call counts, latency, and failure counts.

Grafana dashboards should be renamed and simplified around the failure lab. Old
RAG dashboards should be removed or replaced.

## Documentation

Rewrite the README around the lab:

- What the lab is and is not.
- One-command Docker Compose startup.
- Service URLs.
- Scenario catalog.
- How to read failures in the dashboard, logs, Prometheus, and Grafana.

Remove old architecture docs that center provider breadth, enterprise security,
or production readiness. Keep only concise docs that explain the local lab.

## Testing

Backend tests should cover:

- Health/status behavior when dependencies are healthy or mocked unhealthy.
- Scenario listing and run creation.
- Scenario event recording.
- Mock AI client timeout/error handling.
- Celery task importability.
- API route mounting.

Frontend verification should use `npm run build`.

Compose validation should at least parse configuration with
`docker-compose config` or `docker compose config`, depending on the available
binary.

## Non-goals

- Real OpenAI calls.
- Production RAG quality.
- Multiple vector providers.
- Multi-cloud deployment guidance.
- Authentication and role management unless needed for a specific failure mode.
- Comprehensive document ingestion.
