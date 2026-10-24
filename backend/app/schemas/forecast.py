from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_value: float
    lower_bound_95: float
    upper_bound_95: float
    lower_bound_80: float
    upper_bound_80: float


class ForecastRequest(BaseModel):
    horizon_minutes: int = Field(360, ge=30, le=1440, description="Forecast horizon in minutes (default 360 = 6 hours)")
    model_type: Optional[str] = Field("autoregressive_trend", description="Model: 'autoregressive_trend' or 'baseline_persistence'")


class ForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    twin_state_version: int
    last_observation_timestamp: datetime
    model_name: str
    model_version: str
    forecast_horizon_minutes: int
    predicted_trajectory: List[ForecastPoint]
    is_stale: bool
    stale_reason: Optional[str] = None
    quality_warnings: List[str]
    created_at: datetime
