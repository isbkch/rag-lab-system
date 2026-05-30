# Failure Laboratory

This repo is a local lab for demonstrating failure modes in a small distributed
application. It is not a RAG product and it does not call real AI providers.

The stack is intentionally narrow:

- FastAPI backend
- React dashboard
- PostgreSQL
- Redis
- ChromaDB as the only vector database service
- Mock external AI service
- Celery worker queue
- Prometheus and Grafana
- Docker Compose

## Quick Start

```bash
docker-compose up -d
docker-compose ps
```

Service URLs:

| Service | URL |
| --- | --- |
| Frontend dashboard | http://localhost:3000 |
| Backend API | http://localhost:8080 |
| Backend docs | http://localhost:8080/docs |
| Mock AI | http://localhost:9000 |
| ChromaDB | http://localhost:8002 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

Grafana uses `admin/admin` locally.

## Lab API

The backend mounts only the lab and health routes under `/api/v1`:

- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/lab/status`
- `GET /api/v1/lab/scenarios`
- `POST /api/v1/lab/scenarios/{scenario_id}/run`
- `GET /api/v1/lab/runs`
- `GET /api/v1/lab/events`

## Scenarios

Current scenario ids:

- `mock_ai_timeout`
- `mock_ai_500`
- `redis_unavailable`
- `queue_backlog`
- `postgres_pool_pressure`
- `vector_latency`
- `stale_health`

Each run is stored in `scenario_runs`; scenario events are stored in
`lab_events`.

## Backend

Run Python commands from `backend/`.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
uv run alembic upgrade head
```

The backend requires Python 3.11. The root `pyproject.toml` is not the backend
dependency source.

## Frontend

Run frontend commands from `frontend/`.

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
```

Docker Compose sets `VITE_API_BASE_URL=http://localhost:8080`. Local frontend
development defaults to `http://localhost:8000`.

## Mock AI

The mock AI service is controlled through:

- `GET /health`
- `POST /admin/mode`
- `POST /v1/complete`

Modes are `normal`, `slow`, `error`, and `flaky`.

Example:

```bash
curl -X POST http://localhost:9000/admin/mode \
  -H 'Content-Type: application/json' \
  -d '{"mode":"slow","delay_seconds":3}'
```

## Compose Commands

```bash
docker-compose up -d
docker-compose logs -f backend
docker-compose logs -f celery-worker
docker-compose down
```

Production-style local override:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
