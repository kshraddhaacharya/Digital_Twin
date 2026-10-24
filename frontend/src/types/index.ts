export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  baseline_heart_rate: number;
  medical_notes?: string;
  is_synthetic: boolean;
  created_at: string;
  total_measurements?: number;
  active_twin_state_version?: number;
  latest_heart_rate?: number;
  latest_observation_time?: string;
  vital_status?: string;
}

export interface Measurement {
  id: number;
  patient_id: string;
  timestamp: string;
  measurement_type: string;
  value: number;
  unit: string;
  source: string;
  is_late_arrival: boolean;
  created_at: string;
}

export interface TwinState {
  id: number;
  patient_id: string;
  state_version: number;
  timestamp_latest_observation: string;
  last_processed_measurement_id?: number;
  latest_heart_rate: number;
  rolling_mean_60m?: number;
  rolling_std_60m?: number;
  trend_slope_per_hour?: number;
  circadian_phase_estimate?: number;
  physiological_variability_index?: number;
  vital_status: 'normal' | 'elevated' | 'tachycardia' | 'bradycardia';
  data_freshness_seconds: number;
  is_active_version: boolean;
  created_at: string;
}

export interface ForecastPoint {
  timestamp: string;
  predicted_value: number;
  lower_bound_95: number;
  upper_bound_95: number;
  lower_bound_80: number;
  upper_bound_80: number;
}

export interface Forecast {
  id: number;
  patient_id: string;
  twin_state_version: number;
  last_observation_timestamp: string;
  model_name: string;
  model_version: string;
  forecast_horizon_minutes: number;
  predicted_trajectory: ForecastPoint[];
  is_stale: boolean;
  stale_reason?: string;
  quality_warnings: string[];
  created_at: string;
}

export interface ScenarioPoint {
  timestamp: string;
  simulated_value: number;
}

export interface Scenario {
  id: string;
  patient_id: string;
  baseline_state_version: number;
  scenario_type: string;
  parameter_name: string;
  parameter_value: number;
  parameter_unit: string;
  mathematical_rule: string;
  assumptions: string;
  limitations: string;
  simulated_trajectory: ScenarioPoint[];
  created_at: string;
}

export interface ScenarioComparison {
  patient_id: string;
  baseline_state_version: number;
  scenario_a: Scenario;
  scenario_b: Scenario;
  delta_summary: {
    max_absolute_delta_bpm: number;
    mean_absolute_delta_bpm: number;
    endpoint_delta_bpm: number;
    horizon_hours: number;
    step_count: number;
  };
  disclaimer: string;
}

export interface ModelEvaluation {
  patient_id: string;
  model_name: string;
  evaluation_period_start: string;
  evaluation_period_end: string;
  train_samples: number;
  test_samples: number;
  mae: number;
  rmse: number;
  baseline_mae: number;
  baseline_rmse: number;
  mae_improvement_pct: number;
  is_synthetic_data: boolean;
  disclaimer: string;
  created_at: string;
}
