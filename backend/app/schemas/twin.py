from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TwinStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    state_version: int
    timestamp_latest_observation: datetime
    last_processed_measurement_id: Optional[int]
    
    # Raw latest observation
    latest_heart_rate: float
    
    # Inferred state features
    rolling_mean_60m: Optional[float]
    rolling_std_60m: Optional[float]
    trend_slope_per_hour: Optional[float]
    circadian_phase_estimate: Optional[float]
    physiological_variability_index: Optional[float]
    vital_status: str
    
    # Metadata
    data_freshness_seconds: float
    is_active_version: bool
    created_at: datetime


class TwinUpdateResult(BaseModel):
    success: bool
    patient_id: str
    previous_state_version: int
    new_state_version: int
    updated_at: datetime
    latest_measurement_value: float
    stale_forecasts_invalidated: int
    twin_state: TwinStateResponse
    message: str
