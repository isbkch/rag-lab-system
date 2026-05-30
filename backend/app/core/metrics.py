"""Prometheus metrics for the failure laboratory."""

import logging
import time
from typing import Any, Dict

import psutil
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create custom registry for application metrics
REGISTRY = CollectorRegistry()

# Application Info
app_info = Info("app_info", "Application information", registry=REGISTRY)

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=REGISTRY,
)

# Scenario Metrics
scenario_runs_total = Counter(
    "scenario_runs_total",
    "Total scenario runs",
    ["scenario_id", "status"],
    registry=REGISTRY,
)

scenario_duration_seconds = Histogram(
    "scenario_duration_seconds",
    "Scenario duration in seconds",
    ["scenario_id"],
    registry=REGISTRY,
)

dependency_status = Gauge(
    "dependency_status",
    "Dependency status where 1 is healthy and 0 is degraded",
    ["component"],
    registry=REGISTRY,
)

# System Resource Metrics
system_cpu_usage_percent = Gauge(
    "system_cpu_usage_percent", "CPU usage percentage", registry=REGISTRY
)

system_memory_usage_percent = Gauge(
    "system_memory_usage_percent", "Memory usage percentage", registry=REGISTRY
)

system_disk_usage_percent = Gauge(
    "system_disk_usage_percent",
    "Disk usage percentage",
    ["mount_point"],
    registry=REGISTRY,
)

# Error Metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "component", "severity"],
    registry=REGISTRY,
)


class MetricsCollector:
    """Centralized metrics collector for the application."""

    def __init__(self):
        self.start_time = time.time()
        self._update_app_info()

    def _update_app_info(self):
        """Update application information metrics."""
        app_info.info(
            {
                "version": settings.APP_VERSION,
                "name": settings.APP_NAME,
                "environment": "development" if settings.DEBUG else "production",
                "purpose": "failure-laboratory",
            }
        )

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics."""
        http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_scenario_run(
        self, scenario_id: str, status: str, duration: float | None = None
    ):
        """Record scenario run metrics."""
        scenario_runs_total.labels(scenario_id=scenario_id, status=status).inc()
        if duration is not None:
            scenario_duration_seconds.labels(scenario_id=scenario_id).observe(duration)

    def update_dependency_status(self, component: str, healthy: bool):
        """Update dependency health gauge."""
        dependency_status.labels(component=component).set(1 if healthy else 0)

    def record_error(self, error_type: str, component: str, severity: str = "error"):
        """Record error occurrence."""
        errors_total.labels(
            error_type=error_type, component=component, severity=severity
        ).inc()

    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            system_cpu_usage_percent.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage_percent.set(memory.percent)

            # Disk usage for root partition
            disk = psutil.disk_usage("/")
            system_disk_usage_percent.labels(mount_point="/").set(
                (disk.used / disk.total) * 100
            )

        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        try:
            uptime = time.time() - self.start_time

            return {
                "uptime_seconds": uptime,
                "app_info": {
                    "name": settings.APP_NAME,
                    "version": settings.APP_VERSION,
                    "environment": "development" if settings.DEBUG else "production",
                },
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": (
                        psutil.disk_usage("/").used / psutil.disk_usage("/").total
                    )
                    * 100,
                },
                "metrics_available": True,
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {
                "uptime_seconds": time.time() - self.start_time,
                "error": str(e),
                "metrics_available": False,
            }


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def generate_metrics() -> str:
    """Generate Prometheus metrics output."""
    try:
        # Update system metrics before generating output
        get_metrics_collector().update_system_metrics()

        return generate_latest(REGISTRY)
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return f"# Error generating metrics: {e}\n"
