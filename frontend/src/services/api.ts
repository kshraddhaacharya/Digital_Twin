import axios from 'axios';
import {
  Patient,
  Measurement,
  TwinState,
  Forecast,
  ScenarioComparison,
  ModelEvaluation
} from '../types';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health
  getHealth: async () => {
    const res = await client.get('/health');
    return res.data;
  },

  // Patients
  getPatients: async (): Promise<Patient[]> => {
    const res = await client.get('/patients');
    return res.data;
  },

  getPatient: async (patientId: string): Promise<Patient> => {
    const res = await client.get(`/patients/${patientId}`);
    return res.data;
  },

  createPatient: async (data: Partial<Patient>): Promise<Patient> => {
    const res = await client.post('/patients', data);
    return res.data;
  },

  loadSyntheticPatient: async (params: {
    patient_id?: string;
    name?: string;
    baseline_hr?: number;
    duration_hours?: number;
    interval_minutes?: number;
    noise_level?: number;
    include_exercise_transient?: boolean;
  }) => {
    const res = await client.post('/patients/synthetic', params);
    return res.data;
  },

  // Measurements
  getMeasurements: async (patientId: string, limit: number = 200, type?: string): Promise<Measurement[]> => {
    const params: any = { limit };
    if (type) params.measurement_type = type;
    const res = await client.get(`/patients/${patientId}/measurements`, { params });
    return res.data;
  },

  addMeasurement: async (patientId: string, data: {
    timestamp: string;
    measurement_type: string;
    value: number;
    unit: string;
    source?: string;
  }) => {
    const res = await client.post(`/patients/${patientId}/measurements`, data);
    return res.data;
  },

  uploadCsv: async (patientId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post(`/patients/${patientId}/upload-csv`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  uploadJson: async (patientId: string, payload: any) => {
    const res = await client.post(`/patients/${patientId}/upload-json`, payload);
    return res.data;
  },

  uploadPdf: async (patientId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post(`/patients/${patientId}/upload-pdf`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Digital Twin
  getTwinState: async (patientId: string): Promise<TwinState> => {
    const res = await client.get(`/patients/${patientId}/twin`);
    return res.data;
  },

  getTwinHistory: async (patientId: string): Promise<TwinState[]> => {
    const res = await client.get(`/patients/${patientId}/twin/history`);
    return res.data;
  },

  initializeTwin: async (patientId: string): Promise<TwinState> => {
    const res = await client.post(`/patients/${patientId}/twin/initialize`);
    return res.data;
  },

  // Forecasting
  generateForecast: async (patientId: string, params: {
    horizon_minutes?: number;
    model_type?: string;
  }): Promise<Forecast> => {
    const res = await client.post(`/patients/${patientId}/forecast`, params);
    return res.data;
  },

  getForecasts: async (patientId: string, includeStale: boolean = true): Promise<Forecast[]> => {
    const res = await client.get(`/patients/${patientId}/forecasts`, {
      params: { include_stale: includeStale }
    });
    return res.data;
  },

  // Scenarios
  simulateScenarios: async (patientId: string, params: {
    horizon_minutes?: number;
    parameter_name?: string;
    parameter_value: number;
    parameter_unit?: string;
  }): Promise<ScenarioComparison> => {
    const res = await client.post(`/patients/${patientId}/simulate`, params);
    return res.data;
  },

  // Model Evaluation
  getEvaluation: async (patientId: string, splitRatio: number = 0.20): Promise<ModelEvaluation> => {
    const res = await client.get(`/patients/${patientId}/evaluation`, {
      params: { test_split_ratio: splitRatio }
    });
    return res.data;
  },
};
