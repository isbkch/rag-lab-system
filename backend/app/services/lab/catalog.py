from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    description: str
    component: str
    default_parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        id="mock_ai_timeout",
        title="Mock AI timeout",
        description="Calls the mock AI while it is slow and verifies timeout handling.",
        component="mock_ai",
        default_parameters={"mode": "slow", "prompt": "timeout demo"},
    ),
    Scenario(
        id="mock_ai_500",
        title="Mock AI 500",
        description="Forces the mock AI to return a server error.",
        component="mock_ai",
        default_parameters={"mode": "error", "prompt": "error demo"},
    ),
    Scenario(
        id="redis_unavailable",
        title="Redis unavailable",
        description="Checks Redis using a bad URL to show dependency degradation.",
        component="redis",
        default_parameters={"redis_url": "redis://localhost:1/0"},
    ),
    Scenario(
        id="queue_backlog",
        title="Queue backlog",
        description="Sleeps in a worker task to make queued work visible.",
        component="worker_queue",
        default_parameters={"sleep_seconds": 5},
    ),
    Scenario(
        id="postgres_pool_pressure",
        title="Postgres pool pressure",
        description="Runs bounded database probes to surface pool pressure symptoms.",
        component="postgres",
        default_parameters={"queries": 5},
    ),
    Scenario(
        id="vector_latency",
        title="Vector latency",
        description="Adds delay before checking the ChromaDB dependency.",
        component="chromadb",
        default_parameters={"delay_seconds": 2},
    ),
    Scenario(
        id="stale_health",
        title="Stale health",
        description="Records that liveness can stay green while dependencies degrade.",
        component="health",
        default_parameters={},
    ),
)


def list_scenarios() -> list[dict[str, Any]]:
    return [scenario.to_dict() for scenario in SCENARIOS]


def get_scenario(scenario_id: str) -> Scenario | None:
    return next(
        (scenario for scenario in SCENARIOS if scenario.id == scenario_id), None
    )
