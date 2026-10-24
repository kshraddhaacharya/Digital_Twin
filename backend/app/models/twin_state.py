from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base


class TwinState(Base):
    __tablename__ = "twin_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    state_version = Column(Integer, nullable=False, index=True)
    timestamp_latest_observation = Column(DateTime, nullable=False)
    last_processed_measurement_id = Column(Integer, nullable=True)

    # Latest observed values
    latest_heart_rate = Column(Float, nullable=False)

    # Inferred physiological features (distinct from raw observations)
    rolling_mean_60m = Column(Float, nullable=True)
    rolling_std_60m = Column(Float, nullable=True)
    trend_slope_per_hour = Column(Float, nullable=True)  # in bpm/hr
    circadian_phase_estimate = Column(Float, nullable=True)  # diurnal baseline estimate
    physiological_variability_index = Column(Float, nullable=True)
    vital_status = Column(String(32), nullable=False, default="normal")  # normal, elevated, tachycardia, bradycardia
    
    # State metadata
    data_freshness_seconds = Column(Float, nullable=False, default=0.0)
    is_active_version = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="twin_states")

    __table_args__ = (
        Index("ix_patient_version", "patient_id", "state_version"),
    )
