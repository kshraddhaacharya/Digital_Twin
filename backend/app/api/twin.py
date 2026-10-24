from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.connection import get_db
from backend.app.models.patient import Patient
from backend.app.models.twin_state import TwinState
from backend.app.schemas.twin import TwinStateResponse
from backend.app.digital_twin.engine import DigitalTwinEngine

router = APIRouter(prefix="/patients/{patient_id}/twin", tags=["Digital Twin"])


@router.get("", response_model=TwinStateResponse)
def get_current_twin_state(patient_id: str, db: Session = Depends(get_db)):
    """Retrieves the active, current modeled physiological state for the patient's digital twin."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")

    state = DigitalTwinEngine.get_active_twin_state(patient_id=patient_id, db=db)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digital twin has not been initialized for patient '{patient_id}'. Please upload measurements or call initialize."
        )

    return state


@router.get("/history", response_model=List[TwinStateResponse])
def get_twin_state_history(patient_id: str, db: Session = Depends(get_db)):
    """Retrieves the complete historical audit log of all twin state versions."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")

    states = db.query(TwinState).filter(
        TwinState.patient_id == patient_id
    ).order_by(TwinState.state_version.desc()).all()

    return states


@router.post("/initialize", response_model=TwinStateResponse)
def initialize_twin(patient_id: str, db: Session = Depends(get_db)):
    """Initializes or resets the digital twin from stored observations (Version 1)."""
    try:
        state = DigitalTwinEngine.initialize_twin(patient_id=patient_id, db=db)
        return state
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
