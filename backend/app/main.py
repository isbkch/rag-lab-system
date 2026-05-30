import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.v1.api import api_router
from app.core.config import Settings, get_settings
from app.core.database import Base, engine
from app.core.metrics import generate_metrics, get_metrics_collector
from app.models import LabEvent, ScenarioRun  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Failure Laboratory")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Stopping Failure Laboratory")


app = FastAPI(
    title=get_settings().APP_NAME,
    version=get_settings().APP_VERSION,
    description=(
        "Local lab for demonstrating dependency failures and recovery behavior."
    ),
    docs_url="/docs" if get_settings().DEBUG else None,
    redoc_url="/redoc" if get_settings().DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    start_time = time.time()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        if not request.url.path.startswith("/metrics"):
            get_metrics_collector().record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration=time.time() - start_time,
            )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    get_metrics_collector().record_error(
        error_type=type(exc).__name__,
        component="http",
        severity="error",
    )
    if get_settings().DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
async def root(settings: Settings = Depends(get_settings)):
    return {
        "message": "Failure Laboratory API",
        "version": settings.APP_VERSION,
        "status": "running",
        "api_base": settings.API_V1_STR,
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
    }


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/metrics/json")
async def metrics_json():
    return get_metrics_collector().get_metrics_summary()


app.include_router(api_router, prefix=get_settings().API_V1_STR)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=get_settings().DEBUG,
        log_level="info",
    )
