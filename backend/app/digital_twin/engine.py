from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from sqlalchemy.orm import Session

from backend.app.models.measurement import Measurement
from backend.app.models.patient import Patient
from backend.app.models.twin_state import TwinState
from backend.app.models.forecast import Forecast
from backend.app.web3.service import Web3Service


class DigitalTwinEngine:
    """
    Core Digital Twin Engine for maintaining, updating, and versioning a patient's
    dynamic physiological modeled state.
    """

    @staticmethod
    def compute_state_features(
        measurements: List[Measurement],
        baseline_hr: float = 70.0,
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculates inferred physiological features from chronologically sorted observations.
        Keeps raw latest observations distinct from derived state metrics.
        """
        if not measurements:
            raise ValueError("Cannot compute digital twin state without at least one observation.")

        # Ensure sorted by timestamp
        sorted_m = sorted(measurements, key=lambda m: m.timestamp)
        latest_m = sorted_m[-1]
        
        latest_val = float(latest_m.value)
        latest_ts = latest_m.timestamp
        if latest_ts.tzinfo is None:
            latest_ts = latest_ts.replace(tzinfo=timezone.utc)
            
        now_utc = current_time or datetime.now(timezone.utc)
        freshness_seconds = max(0.0, (now_utc - latest_ts).total_seconds())

        # Filter observations from the last 60 minutes relative to the latest observation
        cutoff_60m = latest_ts - timedelta(minutes=60)
        recent_60m = [m for m in sorted_m if (m.timestamp.replace(tzinfo=timezone.utc) if m.timestamp.tzinfo is None else m.timestamp) >= cutoff_60m]
        
        # If fewer than 3 observations in the 60m window, use last 4 observations as fallback
        if len(recent_60m) < 3 and len(sorted_m) >= 3:
            recent_eval = sorted_m[-4:]
        else:
            recent_eval = recent_60m if recent_60m else sorted_m

        recent_vals = [float(m.value) for m in recent_eval]
        rolling_mean = float(np.mean(recent_vals))
        rolling_std = float(np.std(recent_vals, ddof=1)) if len(recent_vals) > 1 else 0.0

        # Calculate slope (rate of change per hour) over recent window (up to 3 hours)
        cutoff_trend = latest_ts - timedelta(hours=3)
        trend_obs = [m for m in sorted_m if (m.timestamp.replace(tzinfo=timezone.utc) if m.timestamp.tzinfo is None else m.timestamp) >= cutoff_trend]
        if len(trend_obs) < 2:
            trend_obs = sorted_m[-3:] if len(sorted_m) >= 2 else sorted_m

        trend_slope_per_hour = 0.0
        if len(trend_obs) >= 2:
            t0 = trend_obs[0].timestamp.replace(tzinfo=timezone.utc) if trend_obs[0].timestamp.tzinfo is None else trend_obs[0].timestamp
            time_hours = np.array([
                ((m.timestamp.replace(tzinfo=timezone.utc) if m.timestamp.tzinfo is None else m.timestamp) - t0).total_seconds() / 3600.0
                for m in trend_obs
            ])
            vals = np.array([float(m.value) for m in trend_obs])
            
            # Simple linear regression: slope = Cov(t, y) / Var(t)
            time_span = time_hours[-1] - time_hours[0]
            if time_span > 0.01:
                p = np.polyfit(time_hours, vals, deg=1)
                trend_slope_per_hour = float(p[0])

        # Variability index (CV = std / mean * 100)
        variability_idx = float((rolling_std / rolling_mean) * 100.0) if rolling_mean > 0 else 0.0

        # Circadian phase estimate (expected diurnal offset from baseline at this hour)
        hour_of_day = latest_ts.hour + latest_ts.minute / 60.0
        circadian_offset = float(6.0 * np.sin(2 * np.pi * (hour_of_day - 10.0) / 24.0))

        # Vital clinical status classification (for display and alerting)
        if latest_val > 100.0:
            vital_status = "tachycardia"
        elif latest_val < 60.0:
            vital_status = "bradycardia"
        elif latest_val > 90.0:
            vital_status = "elevated"
        else:
            vital_status = "normal"

        return {
            "latest_heart_rate": round(latest_val, 2),
            "timestamp_latest_observation": latest_ts,
            "last_processed_measurement_id": latest_m.id,
            "rolling_mean_60m": round(rolling_mean, 2),
            "rolling_std_60m": round(rolling_std, 2),
            "trend_slope_per_hour": round(trend_slope_per_hour, 2),
            "circadian_phase_estimate": round(circadian_offset, 2),
            "physiological_variability_index": round(variability_idx, 2),
            "vital_status": vital_status,
            "data_freshness_seconds": round(freshness_seconds, 1),
        }

    @classmethod
    def initialize_twin(cls, patient_id: str, db: Session) -> TwinState:
        """
        Initializes or resets the digital twin from stored historical observations.
        Creates TwinState Version 1.
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError(f"Patient '{patient_id}' not found.")

        # Fetch all heart rate observations
        hr_measurements = db.query(Measurement).filter(
            Measurement.patient_id == patient_id,
            Measurement.measurement_type == "heart_rate"
        ).order_by(Measurement.timestamp.asc()).all()

        if not hr_measurements:
            raise ValueError(f"Cannot initialize digital twin for patient '{patient_id}': No heart rate observations found.")

        # Deactivate any previous twin states for this patient
        db.query(TwinState).filter(TwinState.patient_id == patient_id).update({"is_active_version": False})

        features = cls.compute_state_features(hr_measurements, baseline_hr=patient.baseline_heart_rate)

        # On-Chain Web3 State Attestation
        web3_meta = {}
        try:
            w3_service = Web3Service.get_instance()
            att = w3_service.attest_twin_state(
                patient_id=patient_id,
                version=1,
                timestamp=features["timestamp_latest_observation"],
                latest_hr=features["latest_heart_rate"],
                rolling_mean=features["rolling_mean_60m"],
                features=features
            )
            web3_meta = {
                "on_chain_tx_hash": att["on_chain_tx_hash"],
                "on_chain_block_number": att["on_chain_block_number"],
                "state_hash_sha256": att["state_hash_sha256"],
                "ipfs_cid": att["ipfs_cid"],
                "contract_address": att["contract_address"],
            }
        except Exception as e:
            print(f"[Web3] State attestation skipped: {e}")

        new_state = TwinState(
            patient_id=patient_id,
            state_version=1,
            is_active_version=True,
            **features,
            **web3_meta
        )

        db.add(new_state)
        # Invalidate any old forecasts
        cls.invalidate_stale_forecasts(patient_id=patient_id, current_state_version=1, db=db)
        db.commit()
        db.refresh(new_state)
        return new_state

    @classmethod
    def update_twin_with_measurement(
        cls,
        patient_id: str,
        measurement: Measurement,
        db: Session
    ) -> Tuple[TwinState, int]:
        """
        Transactional update of the digital twin when a new valid measurement is accepted.
        Increments the state version (v -> v + 1), computes fresh features, marks older forecasts stale.
        Returns (new_twin_state, count_of_invalidated_forecasts).
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError(f"Patient '{patient_id}' not found.")

        # Get current active state version
        current_state = db.query(TwinState).filter(
            TwinState.patient_id == patient_id,
            TwinState.is_active_version == True
        ).first()

        next_version = (current_state.state_version + 1) if current_state else 1

        # Query all heart rate measurements to compute fresh features
        hr_measurements = db.query(Measurement).filter(
            Measurement.patient_id == patient_id,
            Measurement.measurement_type == "heart_rate"
        ).order_by(Measurement.timestamp.asc()).all()

        features = cls.compute_state_features(hr_measurements, baseline_hr=patient.baseline_heart_rate)

        # On-Chain Web3 State Attestation
        web3_meta = {}
        try:
            w3_service = Web3Service.get_instance()
            att = w3_service.attest_twin_state(
                patient_id=patient_id,
                version=next_version,
                timestamp=features["timestamp_latest_observation"],
                latest_hr=features["latest_heart_rate"],
                rolling_mean=features["rolling_mean_60m"],
                features=features
            )
            web3_meta = {
                "on_chain_tx_hash": att["on_chain_tx_hash"],
                "on_chain_block_number": att["on_chain_block_number"],
                "state_hash_sha256": att["state_hash_sha256"],
                "ipfs_cid": att["ipfs_cid"],
                "contract_address": att["contract_address"],
            }
        except Exception as e:
            print(f"[Web3] State attestation skipped: {e}")

        # Deactivate previous active states
        db.query(TwinState).filter(
            TwinState.patient_id == patient_id,
            TwinState.is_active_version == True
        ).update({"is_active_version": False})

        new_state = TwinState(
            patient_id=patient_id,
            state_version=next_version,
            is_active_version=True,
            **features,
            **web3_meta
        )
        db.add(new_state)

        # Invalidate forecasts produced under older state versions
        stale_count = cls.invalidate_stale_forecasts(patient_id, next_version, db)

        db.commit()
        db.refresh(new_state)
        return new_state, stale_count

    @classmethod
    def invalidate_stale_forecasts(
        cls,
        patient_id: str,
        current_state_version: int,
        db: Session
    ) -> int:
        """
        Marks any forecasts generated from earlier twin state versions as stale.
        Preserves historical forecasts in the database for auditing and comparison.
        """
        stale_forecasts = db.query(Forecast).filter(
            Forecast.patient_id == patient_id,
            Forecast.twin_state_version < current_state_version,
            Forecast.is_stale == False
        ).all()

        count = len(stale_forecasts)
        for f in stale_forecasts:
            f.is_stale = True
            f.stale_reason = (
                f"Twin state evolved to Version {current_state_version}. "
                f"This forecast was generated from State Version {f.twin_state_version} "
                f"at {f.last_observation_timestamp.isoformat()}."
            )

        if count > 0:
            db.commit()

        return count

    @classmethod
    def get_active_twin_state(cls, patient_id: str, db: Session) -> Optional[TwinState]:
        """Retrieves the active twin state snapshot for a patient, updating freshness."""
        state = db.query(TwinState).filter(
            TwinState.patient_id == patient_id,
            TwinState.is_active_version == True
        ).first()

        if state and state.timestamp_latest_observation:
            latest_ts = state.timestamp_latest_observation
            if latest_ts.tzinfo is None:
                latest_ts = latest_ts.replace(tzinfo=timezone.utc)
            freshness = max(0.0, (datetime.now(timezone.utc) - latest_ts).total_seconds())
            state.data_freshness_seconds = round(freshness, 1)

        return state
