def test_root_identifies_failure_lab(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Failure Laboratory API"


def test_list_scenarios(client):
    response = client.get("/api/v1/lab/scenarios")

    assert response.status_code == 200
    scenario_ids = {item["id"] for item in response.json()["scenarios"]}
    assert "mock_ai_500" in scenario_ids
    assert "queue_backlog" in scenario_ids


def test_run_scenario_creates_run(client):
    response = client.post(
        "/api/v1/lab/scenarios/mock_ai_500/run", json={"mode": "error"}
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["scenario_id"] == "mock_ai_500"
    assert payload["status"] == "queued"
    assert payload["parameters"]["mode"] == "error"
    assert payload["parameters"]["prompt"] == "error demo"


def test_recent_runs_and_events(client):
    run_response = client.post(
        "/api/v1/lab/scenarios/mock_ai_500/run", json={"mode": "error"}
    )
    run_id = run_response.json()["id"]

    runs_response = client.get("/api/v1/lab/runs")
    events_response = client.get("/api/v1/lab/events")

    assert runs_response.status_code == 200
    assert events_response.status_code == 200
    assert runs_response.json()["runs"][0]["id"] == run_id
    assert events_response.json()["events"][0]["run_id"] == run_id
    assert events_response.json()["events"][0]["component"] == "queue"


def test_lab_status_contains_components(client):
    response = client.get("/api/v1/lab/status")

    assert response.status_code == 200
    components = response.json()["components"]
    assert {"postgres", "redis", "chromadb", "mock_ai", "worker_queue"} <= set(
        components
    )
