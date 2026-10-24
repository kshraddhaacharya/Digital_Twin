from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database.connection import get_db
from backend.app.models.patient import Patient
from backend.app.models.forecast import Forecast
from backend.app.models.twin_state import TwinState
from backend.app.schemas.forecast import ForecastRequest, ForecastResponse
from backend.app.forecasting.engine import ForecastingEngine

router = APIRouter(prefix="/patients/{patient_id}", tags=["Forecasting"])


@router.post("/forecast", response_model=ForecastResponse)
def generate_forecast(
    patient_id: str,
    payload: ForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a forward-looking physiological forecast rooted in the active digital twin state.
    Records model version, uncertainty bands, and explicit association to the active twin state version.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")

    try:
        record = ForecastingEngine.generate_forecast(
            patient_id=patient_id,
            db=db,
            horizon_minutes=payload.horizon_minutes,
            model_type=payload.model_type or "autoregressive_trend"
        )
        return record
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/forecasts", response_model=List[ForecastResponse])
def get_forecasts(
    patient_id: str,
    include_stale: bool = Query(True, description="Whether to include stale historical forecasts"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieves all generated forecasts for a patient.
    Highlights whether each forecast is fresh or stale relative to current twin state.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")

    active_state = db.query(TwinState).filter(
        TwinState.patient_id == patient_id,
        TwinState.is_active_version == True
    ).first()

    query = db.query(Forecast).filter(Forecast.patient_id == patient_id)
    if not include_stale:
        query = query.filter(Forecast.is_stale == False)

    forecasts = query.order_by(Forecast.created_at.desc()).limit(limit).all()

    # Dynamic check: if state evolved beyond forecast's version, ensure flagged stale
    if active_state:
        for f in forecasts:
            if f.twin_state_version < active_state.state_version and not f.is_stale:
                f.is_stale = True
                f.stale_reason = f"State advanced to Version {active_state.state_version}."

    return forecasts
