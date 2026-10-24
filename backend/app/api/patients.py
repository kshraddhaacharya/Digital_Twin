from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from backend.app.database.connection import get_db
from backend.app.models.patient import Patient
from backend.app.models.measurement import Measurement
from backend.app.schemas.patient import PatientCreate, PatientResponse, SyntheticPatientRequest
from backend.app.data.synthetic import generate_synthetic_patient_data
from backend.app.digital_twin.engine import DigitalTwinEngine
from backend.app.services.ingestion import parse_iso_datetime

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=List[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    """Lists all registered patients."""
    return db.query(Patient).order_by(Patient.created_at.desc()).all()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    """Registers a new patient."""
    existing = db.query(Patient).filter(Patient.id == payload.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient with ID '{payload.id}' already exists."
        )

    patient = Patient(
        id=payload.id,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        baseline_heart_rate=payload.baseline_heart_rate,
        medical_notes=payload.medical_notes,
        is_synthetic=payload.is_synthetic,
        created_at=datetime.now(timezone.utc)
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.post("/synthetic", status_code=status.HTTP_201_CREATED)
def create_or_load_synthetic_patient(payload: SyntheticPatientRequest, db: Session = Depends(get_db)):
    """
    Generates a deterministic synthetic patient telemetry stream, stores measurements,
    and initializes the Patient Digital Twin at Version 1.
    """
    pid = payload.patient_id or "PT-DEMO-001"

    # Delete existing patient if already present to guarantee clean demo state
    existing = db.query(Patient).filter(Patient.id == pid).first()
    if existing:
        db.delete(existing)
        db.commit()

    synthetic_bundle = generate_synthetic_patient_data(
        patient_id=pid,
        name=payload.name or "Alice M. Taylor",
        age=payload.age or 56,
        gender=payload.gender or "Female",
        baseline_hr=payload.baseline_hr or 72.0,
        duration_hours=payload.duration_hours or 24,
        interval_minutes=payload.interval_minutes or 15,
        noise_level=payload.noise_level or 1.2,
        include_exercise=payload.include_exercise_transient if payload.include_exercise_transient is not None else True
    )

    pt_info = synthetic_bundle["patient"]
    new_patient = Patient(
        id=pt_info["id"],
        name=pt_info["name"],
        age=pt_info["age"],
        gender=pt_info["gender"],
        baseline_heart_rate=pt_info["baseline_heart_rate"],
        medical_notes=pt_info["medical_notes"],
        is_synthetic=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_patient)
    db.flush()

    # Insert synthetic measurements
    measurement_objs = []
    for m in synthetic_bundle["measurements"]:
        ts = parse_iso_datetime(m["timestamp"])
        measurement_objs.append(Measurement(
            patient_id=pid,
            timestamp=ts,
            measurement_type=m["measurement_type"],
            value=m["value"],
            unit=m["unit"],
            source=m["source"],
            is_late_arrival=False
        ))
    db.add_all(measurement_objs)
    db.commit()

    # Initialize Digital Twin at State Version 1
    twin_state = DigitalTwinEngine.initialize_twin(patient_id=pid, db=db)

    return {
        "success": True,
        "patient": {
            "id": new_patient.id,
            "name": new_patient.name,
            "age": new_patient.age,
            "gender": new_patient.gender,
            "baseline_heart_rate": new_patient.baseline_heart_rate,
            "is_synthetic": True
        },
        "measurements_loaded": len(measurement_objs),
        "twin_state_version": twin_state.state_version,
        "latest_heart_rate": twin_state.latest_heart_rate,
        "observation_window": synthetic_bundle["summary"]
    }


@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Retrieves patient details along with digital twin status."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found."
        )

    active_twin = DigitalTwinEngine.get_active_twin_state(patient_id=patient_id, db=db)
    total_measurements = db.query(Measurement).filter(Measurement.patient_id == patient_id).count()

    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "baseline_heart_rate": patient.baseline_heart_rate,
        "medical_notes": patient.medical_notes,
        "is_synthetic": patient.is_synthetic,
        "created_at": patient.created_at,
        "total_measurements": total_measurements,
        "active_twin_state_version": active_twin.state_version if active_twin else None,
        "latest_heart_rate": active_twin.latest_heart_rate if active_twin else None,
        "latest_observation_time": active_twin.timestamp_latest_observation if active_twin else None,
        "vital_status": active_twin.vital_status if active_twin else "uninitialized"
    }
