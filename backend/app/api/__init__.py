from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.patients import router as patients_router
from backend.app.api.measurements import router as measurements_router
from backend.app.api.twin import router as twin_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.simulation import router as simulation_router
from backend.app.api.evaluation import router as evaluation_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router)
api_router.include_router(patients_router)
api_router.include_router(measurements_router)
api_router.include_router(twin_router)
api_router.include_router(forecast_router)
api_router.include_router(simulation_router)
api_router.include_router(evaluation_router)

__all__ = ["api_router"]
