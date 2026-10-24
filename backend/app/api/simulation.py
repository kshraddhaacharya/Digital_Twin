from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.connection import get_db
from backend.app.models.patient import Patient
from backend.app.models.scenario import Scenario
from backend.app.schemas.scenario import ScenarioSimulateRequest, ScenarioComparisonResponse, ScenarioResponse
from backend.app.simulation.engine import SimulationEngine

router = APIRouter(prefix="/patients/{patient_id}", tags=["Simulation"])


@router.post("/simulate", response_model=ScenarioComparisonResponse)
def simulate_scenarios(
    patient_id: str,
    payload: ScenarioSimulateRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a counterfactual scenario simulation:
    - Scenario A: Current trajectory from active twin state
    - Scenario B: Hypothetical altered condition with transparent parameter adjustment and mathematical rules.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")

    try:
        result = SimulationEngine.run_simulation(
            patient_id=patient_id,
            db=db,
            horizon_minutes=payload.horizon_minutes or 360,
            parameter_name=payload.parameter_name or "trend_damping_pct",
            parameter_value=payload.parameter_value,
            parameter_unit=payload.parameter_unit or "%"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/scenarios", response_model=List[ScenarioResponse])
def get_scenarios(
    patient_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieves stored historical scenario records for a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")

    return db.query(Scenario).filter(
        Scenario.patient_id == patient_id
    ).order_by(Scenario.created_at.desc()).limit(limit).all()
