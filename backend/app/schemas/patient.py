from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PatientCreate(BaseModel):
    id: str = Field(..., description="Unique patient identifier, e.g., 'PT-DEMO-001'")
    name: str = Field(..., min_length=1, max_length=128)
    age: int = Field(..., ge=0, le=130)
    gender: str = Field(..., min_length=1, max_length=32)
    baseline_heart_rate: float = Field(70.0, ge=40.0, le=120.0, description="Resting baseline HR in bpm")
    medical_notes: Optional[str] = None
    is_synthetic: bool = True


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    age: int
    gender: str
    baseline_heart_rate: float
    medical_notes: Optional[str]
    is_synthetic: bool
    created_at: datetime


class SyntheticPatientRequest(BaseModel):
    patient_id: Optional[str] = Field("PT-DEMO-001", description="Patient ID to generate or overwrite")
    name: Optional[str] = "Alice M. Taylor"
    age: Optional[int] = 56
    gender: Optional[str] = "Female"
    baseline_hr: Optional[float] = 72.0
    duration_hours: Optional[int] = Field(24, ge=6, le=168, description="Observation history span in hours")
    interval_minutes: Optional[int] = Field(15, ge=5, le=60, description="Minutes between consecutive readings")
    noise_level: Optional[float] = Field(1.5, ge=0.0, le=10.0, description="Gaussian noise standard deviation")
    include_exercise_transient: Optional[bool] = Field(True, description="Inject an afternoon transient exertion spike")
