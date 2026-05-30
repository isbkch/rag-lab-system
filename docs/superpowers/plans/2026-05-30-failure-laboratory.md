# Failure Laboratory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strip the repo down from an enterprise RAG starter kit into a local failure laboratory with a FastAPI backend, React dashboard, Postgres, Redis, ChromaDB, mock AI service, Celery worker, Prometheus/Grafana, and Docker Compose.

**Architecture:** FastAPI exposes health and lab scenario APIs. Celery executes bounded failure scenarios and records scenario runs/events in Postgres. A separate mock AI FastAPI service simulates normal, slow, error, and flaky external AI behavior; React presents component status, scenario triggers, runs, and events.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL, ChromaDB, React/Vite/TypeScript, Prometheus, Grafana, Docker Compose.

---

## File Structure

- Delete: `backend/app/services/vectordb/factory.py`, `backend/app/services/vectordb/pinecone_db.py`, `backend/app/services/vectordb/weaviate_db.py`.
- Keep and simplify: `backend/app/services/vectordb/chroma_db.py`, `backend/app/services/vectordb/base.py`.
- Delete or bypass product routes: `backend/app/api/v1/endpoints/documents.py`, `backend/app/api/v1/endpoints/search.py`.
- Create: `backend/app/models/lab.py` for `ScenarioRun` and `LabEvent`.
- Create: `backend/app/services/lab/catalog.py`, `backend/app/services/lab/repository.py`, `backend/app/services/lab/runner.py`, `backend/app/services/lab/mock_ai_client.py`, `backend/app/services/lab/status.py`.
- Create: `backend/app/api/v1/endpoints/lab.py`.
- Create: `backend/app/tasks/lab.py`.
- Modify: `backend/app/celery_app.py`, `backend/app/api/v1/api.py`, `backend/app/api/v1/endpoints/health.py`, `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/metrics.py`.
- Create: `mock_ai/main.py`, `mock_ai/pyproject.toml`, `mock_ai/Dockerfile`.
- Replace: `frontend/src/App.tsx`, `frontend/src/api.ts`, `frontend/src/config.ts`, `frontend/src/index.css`.
- Replace: `README.md`.
- Replace or simplify: `monitoring/prometheus.yml`, Grafana dashboard JSON files.
- Modify: `docker-compose.yml`, `docker-compose.override.yml`, `docker-compose.prod.yml`, `backend/pyproject.toml`.
- Add tests: `backend/tests/test_lab_api.py`, `backend/tests/test_lab_repository.py`, `backend/tests/test_mock_ai_client.py`, `backend/tests/test_celery_imports.py`.

## Task 1: Backend Lab Schema

**Files:**
- Create: `backend/app/models/lab.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/003_failure_lab_schema.py`
- Test: `backend/tests/test_lab_repository.py`

- [ ] **Step 1: Write failing repository test**

```python
def test_create_run_and_event(db_session):
    repo = LabRepository(db_session)
    run = repo.create_run("mock_ai_500", {"mode": "error"})
    repo.record_event(str(run.id), "mock-ai", "error", "mock AI returned 500")

    runs = repo.list_runs(limit=10)
    events = repo.list_events(limit=10)

    assert runs[0].scenario_id == "mock_ai_500"
    assert runs[0].status == "queued"
    assert events[0].component == "mock-ai"
    assert events[0].severity == "error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_lab_repository.py -v`

Expected: import failure for `app.services.lab.repository`.

- [ ] **Step 3: Add models and repository**

Implement `ScenarioRun` and `LabEvent` SQLAlchemy models with UUID primary keys, timestamps, JSON parameters/summary, status, component, severity, and message fields. Implement `LabRepository.create_run`, `mark_run_started`, `mark_run_completed`, `mark_run_failed`, `record_event`, `list_runs`, and `list_events`.

- [ ] **Step 4: Add migration**

Create `003_failure_lab_schema.py` with `scenario_runs` and `lab_events` tables. Use `metadata_` for JSON fields if the Python attribute needs to avoid SQLAlchemy reserved names.

- [ ] **Step 5: Verify**

Run: `cd backend && uv run pytest tests/test_lab_repository.py -v`

Expected: all tests pass.

## Task 2: Scenario Catalog And Runner

**Files:**
- Create: `backend/app/services/lab/catalog.py`
- Create: `backend/app/services/lab/runner.py`
- Create: `backend/app/services/lab/mock_ai_client.py`
- Create: `backend/app/services/lab/status.py`
- Test: `backend/tests/test_mock_ai_client.py`

- [ ] **Step 1: Write failing mock AI client tests**

```python
@pytest.mark.asyncio
async def test_mock_ai_client_records_timeout(respx_mock):
    route = respx_mock.post("http://mock-ai:9000/v1/complete").mock(
        side_effect=httpx.ReadTimeout("slow")
    )
    client = MockAIClient("http://mock-ai:9000", timeout_seconds=0.1)

    with pytest.raises(MockAIError) as exc:
        await client.complete("hello")

    assert route.called
    assert "timeout" in str(exc.value).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_mock_ai_client.py -v`

Expected: import failure for `MockAIClient`.

- [ ] **Step 3: Implement catalog**

Create a static catalog with these scenario ids: `mock_ai_timeout`, `mock_ai_500`, `redis_unavailable`, `queue_backlog`, `postgres_pool_pressure`, `vector_latency`, `stale_health`. Each scenario has `id`, `title`, `description`, `component`, and `default_parameters`.

- [ ] **Step 4: Implement mock AI client**

Use `httpx.AsyncClient` with a short timeout. Convert `TimeoutException`, non-2xx responses, and request errors into a local `MockAIError`.

- [ ] **Step 5: Implement runner**

Implement async scenario handlers that record start/completion/failure events through `LabRepository`. Keep each scenario bounded; no infinite loops, no unbounded fan-out, no real external providers.

- [ ] **Step 6: Verify**

Run: `cd backend && uv run pytest tests/test_mock_ai_client.py -v`

Expected: all tests pass.

## Task 3: Celery Queue Integration

**Files:**
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/lab.py`
- Modify: `backend/app/celery_app.py`
- Test: `backend/tests/test_celery_imports.py`

- [ ] **Step 1: Write failing import test**

```python
def test_celery_imports_lab_tasks():
    from app.celery_app import celery
    import app.tasks.lab

    task_names = set(celery.tasks.keys())
    assert "app.tasks.lab.run_scenario" in task_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_celery_imports.py -v`

Expected: `ModuleNotFoundError` for `app.tasks`.

- [ ] **Step 3: Create lab task**

Define `run_scenario(run_id: str, scenario_id: str, parameters: dict)` as a Celery task. It should create a database session, call the async runner through `asyncio.run`, and return a JSON-serializable summary.

- [ ] **Step 4: Simplify Celery app**

Set Celery name to `failure_lab`, include only `app.tasks.lab`, and route `app.tasks.lab.*` to queue `lab`.

- [ ] **Step 5: Verify**

Run: `cd backend && uv run pytest tests/test_celery_imports.py -v`

Expected: all tests pass.

## Task 4: Lab API And Health

**Files:**
- Create: `backend/app/api/v1/endpoints/lab.py`
- Modify: `backend/app/api/v1/api.py`
- Modify: `backend/app/api/v1/endpoints/health.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_lab_api.py`

- [ ] **Step 1: Write failing API tests**

```python
def test_list_scenarios(client):
    response = client.get("/api/v1/lab/scenarios")
    assert response.status_code == 200
    assert any(item["id"] == "mock_ai_500" for item in response.json()["scenarios"])

def test_run_scenario_creates_run(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.endpoints.lab.run_scenario.delay", lambda *args: None)
    response = client.post("/api/v1/lab/scenarios/mock_ai_500/run", json={})
    assert response.status_code == 202
    assert response.json()["scenario_id"] == "mock_ai_500"
    assert response.json()["status"] == "queued"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_lab_api.py -v`

Expected: 404 for `/api/v1/lab/scenarios`.

- [ ] **Step 3: Implement lab router**

Add endpoints for scenarios, scenario run creation, recent runs, recent events, and component status. Return `202 Accepted` for queued runs.

- [ ] **Step 4: Simplify route mounts**

Mount only `health` and `lab` in `backend/app/api/v1/api.py`. Remove document/search product route mounts.

- [ ] **Step 5: Simplify app startup**

Remove startup dependency on search manager and default admin creation. Keep metrics, CORS, logging, and database-independent startup.

- [ ] **Step 6: Verify**

Run: `cd backend && uv run pytest tests/test_lab_api.py -v`

Expected: all tests pass.

## Task 5: Mock AI Service

**Files:**
- Create: `mock_ai/main.py`
- Create: `mock_ai/pyproject.toml`
- Create: `mock_ai/Dockerfile`

- [ ] **Step 1: Create mock service**

Implement a tiny FastAPI app with:

```python
@app.get("/health")
async def health():
    return {"status": "healthy", "mode": state.mode}

@app.post("/admin/mode")
async def set_mode(request: ModeRequest):
    state.mode = request.mode
    return {"mode": state.mode}

@app.post("/v1/complete")
async def complete(request: CompletionRequest):
    if state.mode == "slow":
        await asyncio.sleep(state.delay_seconds)
    if state.mode == "error":
        raise HTTPException(status_code=500, detail="mock AI forced error")
    if state.mode == "flaky" and random.random() < state.failure_rate:
        raise HTTPException(status_code=503, detail="mock AI flaky failure")
    return {"text": f"mock response for {request.prompt}", "mode": state.mode}
```

- [ ] **Step 2: Verify import**

Run: `cd mock_ai && uv run python -m compileall .`

Expected: compile succeeds.

## Task 6: Compose And Dependency Strip-Down

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.override.yml`
- Modify: `docker-compose.prod.yml`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`

- [ ] **Step 1: Remove distracting services**

Remove `elasticsearch` and `celery-beat` from Compose. Remove Elasticsearch volumes and env vars. Keep `postgres`, `redis`, `chromadb`, `backend`, `celery-worker`, `frontend`, `mock-ai`, `prometheus`, and `grafana`.

- [ ] **Step 2: Add mock AI service**

Add a `mock-ai` service built from `./mock_ai`, expose host port `9000`, and set backend/worker `MOCK_AI_URL=http://mock-ai:9000`.

- [ ] **Step 3: Remove provider dependencies**

Remove `pinecone-client`, `weaviate-client`, `openai`, `elasticsearch`, `faiss-cpu`, `sentence-transformers`, `nltk`, `spacy`, and `tiktoken` from `backend/pyproject.toml` unless a remaining import requires them. Run `uv lock` from `backend/`.

- [ ] **Step 4: Verify compose config**

Run: `docker-compose config` or `docker compose config`

Expected: config renders without service dependency errors.

## Task 7: Frontend Lab Dashboard

**Files:**
- Replace: `frontend/src/App.tsx`
- Replace: `frontend/src/api.ts`
- Modify: `frontend/src/config.ts`
- Replace: `frontend/src/index.css`

- [ ] **Step 1: Replace API client**

Expose `getStatus`, `listScenarios`, `runScenario`, `listRuns`, and `listEvents`. Use `VITE_API_BASE_URL` and `VITE_API_VERSION`.

- [ ] **Step 2: Replace app UI**

Render component status, scenario cards with run buttons, recent runs, event stream, and monitoring links. Remove search/upload/document management UI.

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`

Expected: TypeScript and Vite build pass.

## Task 8: Docs And Monitoring

**Files:**
- Replace: `README.md`
- Delete or rewrite: old docs under `docs/`
- Modify: `monitoring/prometheus.yml`
- Replace: Grafana dashboards under `monitoring/grafana/dashboards/`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rewrite README**

Describe the repo as a failure lab, list kept services and removed product claims, document startup, URLs, and scenario catalog.

- [ ] **Step 2: Remove stale architecture docs**

Delete old docs that center enterprise RAG, vector abstraction, provider comparisons, and production claims. Keep the design/plan docs under `docs/superpowers/`.

- [ ] **Step 3: Update agent docs**

Update `AGENTS.md` and `CLAUDE.md` with current commands, service list, route list, and the failure-lab purpose.

- [ ] **Step 4: Verify stale-language scan**

Run:

```bash
rg -n "Enterprise RAG|production-ready|Pinecone|Weaviate|Elasticsearch|OpenAI API key|multi-provider|hot-swapping" README.md AGENTS.md CLAUDE.md docs backend frontend docker-compose*.yml
```

Expected: no matches except approved historical notes in the committed design/plan docs.

## Task 9: Final Verification

**Files:**
- All touched files.

- [ ] **Step 1: Run backend tests**

Run: `cd backend && uv run pytest`

Expected: tests pass.

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && npm run build`

Expected: build pass.

- [ ] **Step 3: Validate compose**

Run: `docker-compose config` or `docker compose config`

Expected: config pass.

- [ ] **Step 4: Check git status**

Run: `git status --short`

Expected: only intentional failure-lab changes remain.
