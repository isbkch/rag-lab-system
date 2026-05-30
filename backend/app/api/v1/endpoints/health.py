from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.services.lab.status import get_component_status

router = APIRouter()


@router.get("/")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "message": "Failure Laboratory API is running",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live")
async def liveness_check():
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_check(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    components = await get_component_status(db, settings)
    degraded = [
        name for name, detail in components.items() if detail.get("status") != "healthy"
    ]
    return {
        "status": "degraded" if degraded else "ready",
        "components": components,
        "degraded_components": degraded,
        "timestamp": datetime.utcnow().isoformat(),
    }
