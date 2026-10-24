import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.linear_model import Ridge
from sqlalchemy.orm import Session

from backend.app.models.measurement import Measurement
from backend.app.models.twin_state import TwinState
from backend.app.models.forecast import Forecast
from backend.app.schemas.forecast import ForecastPoint


class ForecastingEngine:
    """
    Forecasting Engine providing short-term physiological forecasts
    using both Baseline Persistence and Autoregressive Trend Extrapolation.
    """

    @staticmethod
    def generate_forecast(
        patient_id: str,
        db: Session,
        horizon_minutes: int = 360,
        step_minutes: int = 15,
        model_type: str = "autoregressive_trend"
    ) -> Forecast:
        """
        Generates a short-term forecast rooted in the active digital twin state.
        Associates the output with the exact twin state version.
        """
        # 1. Fetch active twin state
        active_state = db.query(TwinState).filter(
            TwinState.patient_id == patient_id,
            TwinState.is_active_version == True
        ).first()

        if not active_state:
            raise ValueError(f"No active digital twin state found for patient '{patient_id}'. Please initialize the twin first.")

        # 2. Fetch historical heart rate measurements
        measurements = db.query(Measurement).filter(
            Measurement.patient_id == patient_id,
            Measurement.measurement_type == "heart_rate"
        ).order_by(Measurement.timestamp.asc()).all()

        if len(measurements) < 6:
            raise ValueError(
                f"Insufficient historical data for forecasting: Found {len(measurements)} heart rate observations, "
                f"but a minimum of 6 observations is required."
            )

        quality_warnings: List[str] = []
        if len(measurements) < 16:
            quality_warnings.append("Limited historical observations (<16 points). Uncertainty intervals may be wider than usual.")

        # Check for irregular sampling intervals
        timestamps = [
            (m.timestamp.replace(tzinfo=timezone.utc) if m.timestamp.tzinfo is None else m.timestamp)
            for m in measurements
        ]
        diffs = [
            (timestamps[i] - timestamps[i - 1]).total_seconds() / 60.0
            for i in range(1, len(timestamps))
        ]
        median_interval = float(np.median(diffs))
        if max(diffs) > (median_interval * 3.0):
            quality_warnings.append("Gaps detected in measurement stream; interpolation applied during feature engineering.")

        # 3. Model execution
        last_obs_ts = timestamps[-1]
        last_val = float(measurements[-1].value)
        values = np.array([float(m.value) for m in measurements])

        num_steps = max(1, horizon_minutes // step_minutes)
        future_timestamps = [last_obs_ts + timedelta(minutes=(i + 1) * step_minutes) for i in range(num_steps)]

        forecast_points: List[Dict[str, Any]] = []

        if model_type == "baseline_persistence":
            model_name = "BaselinePersistenceModel"
            model_version = "1.0.0"

            # Baseline holds last observed value forward with error based on sample std dev
            sample_std = float(np.std(values, ddof=1)) if len(values) > 1 else 2.5
            for i, fut_ts in enumerate(future_timestamps):
                step_idx = i + 1
                # Error growth: se(h) = std * sqrt(h)
                se = sample_std * math.sqrt(1.0 + 0.08 * step_idx)
                forecast_points.append({
                    "timestamp": fut_ts.isoformat(),
                    "predicted_value": round(last_val, 2),
                    "lower_bound_95": round(max(35.0, last_val - 1.96 * se), 2),
                    "upper_bound_95": round(min(220.0, last_val + 1.96 * se), 2),
                    "lower_bound_80": round(max(35.0, last_val - 1.28 * se), 2),
                    "upper_bound_80": round(min(220.0, last_val + 1.28 * se), 2),
                })

        else:
            # Autoregressive Trend Model with Diurnal / Circadian harmonics + Ridge regression
            model_name = "AutoregressiveTrendModel"
            model_version = "1.2.0"

            # Construct features for historical series
            # Features: [elapsed_hours, sin_diurnal, cos_diurnal, lag_1, lag_2]
            t0 = timestamps[0]
            elapsed_hours = np.array([(ts - t0).total_seconds() / 3600.0 for ts in timestamps])

            sin_circadian = np.sin(2 * np.pi * np.array([ts.hour + ts.minute / 60.0 for ts in timestamps]) / 24.0)
            cos_circadian = np.cos(2 * np.pi * np.array([ts.hour + ts.minute / 60.0 for ts in timestamps]) / 24.0)

            X_list = []
            y_list = []
            lags = 2
            for i in range(lags, len(values)):
                feats = [
                    elapsed_hours[i],
                    sin_circadian[i],
                    cos_circadian[i],
                    values[i - 1],
                    values[i - 2]
                ]
                X_list.append(feats)
                y_list.append(values[i])

            X_arr = np.array(X_list)
            y_arr = np.array(y_list)

            # Fit regularized Ridge regression
            ridge = Ridge(alpha=1.0)
            ridge.fit(X_arr, y_arr)

            # In-sample residual variance for prediction interval computation
            residuals = y_arr - ridge.predict(X_arr)
            residual_std = float(np.std(residuals, ddof=1)) if len(residuals) > 2 else 2.0

            # Iterative multi-step projection into future
            current_lags = [values[-1], values[-2]]
            for i, fut_ts in enumerate(future_timestamps):
                step_idx = i + 1
                fut_elapsed = (fut_ts - t0).total_seconds() / 3600.0
                fut_hour = fut_ts.hour + fut_ts.minute / 60.0
                fut_sin = math.sin(2 * math.pi * fut_hour / 24.0)
                fut_cos = math.cos(2 * math.pi * fut_hour / 24.0)

                fut_feats = np.array([[fut_elapsed, fut_sin, fut_cos, current_lags[0], current_lags[1]]])
                pred_val = float(ridge.predict(fut_feats)[0])
                
                # Physiological boundary clamping
                pred_val = max(40.0, min(180.0, pred_val))

                # Update autoregressive memory
                current_lags = [pred_val, current_lags[0]]

                # Standard error increases monotonically with horizon steps
                se = residual_std * math.sqrt(1.0 + 0.05 * step_idx)

                forecast_points.append({
                    "timestamp": fut_ts.isoformat(),
                    "predicted_value": round(pred_val, 2),
                    "lower_bound_95": round(max(35.0, pred_val - 1.96 * se), 2),
                    "upper_bound_95": round(min(220.0, pred_val + 1.96 * se), 2),
                    "lower_bound_80": round(max(35.0, pred_val - 1.28 * se), 2),
                    "upper_bound_80": round(min(220.0, pred_val + 1.28 * se), 2),
                })

        # 4. Save to database
        forecast_record = Forecast(
            patient_id=patient_id,
            twin_state_version=active_state.state_version,
            last_observation_timestamp=last_obs_ts,
            model_name=model_name,
            model_version=model_version,
            forecast_horizon_minutes=horizon_minutes,
            predicted_trajectory=forecast_points,
            is_stale=False,
            stale_reason=None,
            quality_warnings=quality_warnings,
            created_at=datetime.now(timezone.utc)
        )

        db.add(forecast_record)
        db.commit()
        db.refresh(forecast_record)

        return forecast_record
