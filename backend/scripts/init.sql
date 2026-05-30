CREATE TABLE IF NOT EXISTS scenario_runs (
    id VARCHAR(36) PRIMARY KEY,
    scenario_id VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary JSONB,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_scenario_runs_scenario_id
    ON scenario_runs (scenario_id);

CREATE INDEX IF NOT EXISTS ix_scenario_runs_status
    ON scenario_runs (status);

CREATE TABLE IF NOT EXISTS lab_events (
    id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(36) REFERENCES scenario_runs(id) ON DELETE CASCADE,
    component VARCHAR(100) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_lab_events_component
    ON lab_events (component);

CREATE INDEX IF NOT EXISTS ix_lab_events_severity
    ON lab_events (severity);

CREATE INDEX IF NOT EXISTS ix_lab_events_created_at
    ON lab_events (created_at);
