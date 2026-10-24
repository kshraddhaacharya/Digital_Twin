import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewSection } from './components/OverviewSection';
import { DigitalTwinSection } from './components/DigitalTwinSection';
import { ForecastSection } from './components/ForecastSection';
import { ScenarioSection } from './components/ScenarioSection';
import { PatientDataSection } from './components/PatientDataSection';
import { EvaluationSection } from './components/EvaluationSection';
import { api } from './services/api';
import { Patient, TwinState, Measurement, Forecast } from './types';

export function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('PT-DEMO-001');
  const [activeTab, setActiveTab] = useState<string>('overview');
  
  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null);
  const [twinState, setTwinState] = useState<TwinState | null>(null);
  const [twinHistory, setTwinHistory] = useState<TwinState[]>([]);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load all patients on mount
  const loadPatients = async () => {
    try {
      const pts = await api.getPatients();
      setPatients(pts);
      if (pts.length > 0 && !pts.some((p) => p.id === selectedPatientId)) {
        setSelectedPatientId(pts[0].id);
      }
    } catch (err: any) {
      console.error('Failed to fetch patients:', err);
    }
  };

  // Load patient specific data
  const loadPatientData = async (patientId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [ptData, tState, tHist, meas, fcs] = await Promise.allSettled([
        api.getPatient(patientId),
        api.getTwinState(patientId),
        api.getTwinHistory(patientId),
        api.getMeasurements(patientId, 300),
        api.getForecasts(patientId, true),
      ]);

      if (ptData.status === 'fulfilled') {
        setCurrentPatient(ptData.value);
      }
      if (tState.status === 'fulfilled') {
        setTwinState(tState.value);
      } else {
        setTwinState(null);
      }
      if (tHist.status === 'fulfilled') {
        setTwinHistory(tHist.value);
      } else {
        setTwinHistory([]);
      }
      if (meas.status === 'fulfilled') {
        setMeasurements(meas.value);
      } else {
        setMeasurements([]);
      }
      if (fcs.status === 'fulfilled') {
        setForecasts(fcs.value);
      } else {
        setForecasts([]);
      }
    } catch (err: any) {
      setError('Failed to load patient telemetry or digital twin state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, []);

  useEffect(() => {
    if (selectedPatientId) {
      loadPatientData(selectedPatientId);
    }
  }, [selectedPatientId]);

  // Load or regenerate synthetic patient demo
  const handleLoadSynthetic = async () => {
    setLoading(true);
    try {
      await api.loadSyntheticPatient({
        patient_id: 'PT-DEMO-001',
        name: 'Alice M. Taylor',
        baseline_hr: 72.0,
        duration_hours: 24,
      });
      await loadPatients();
      setSelectedPatientId('PT-DEMO-001');
      await loadPatientData('PT-DEMO-001');
      setActiveTab('overview');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to seed synthetic patient.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <Navbar
        patients={patients}
        selectedPatientId={selectedPatientId}
        onSelectPatient={(id) => setSelectedPatientId(id)}
        onRefresh={() => loadPatientData(selectedPatientId)}
        onLoadSynthetic={handleLoadSynthetic}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        loading={loading}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm font-medium">
            {error}
          </div>
        )}

        {activeTab === 'overview' && (
          <OverviewSection
            patient={currentPatient}
            twinState={twinState}
            recentMeasurements={measurements}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'twin' && (
          <DigitalTwinSection
            patientId={selectedPatientId}
            twinState={twinState}
            twinHistory={twinHistory}
            onTwinUpdated={() => loadPatientData(selectedPatientId)}
          />
        )}

        {activeTab === 'forecast' && (
          <ForecastSection
            patientId={selectedPatientId}
            twinState={twinState}
            measurements={measurements}
            forecasts={forecasts}
            onForecastGenerated={() => loadPatientData(selectedPatientId)}
          />
        )}

        {activeTab === 'scenarios' && (
          <ScenarioSection
            patientId={selectedPatientId}
            twinState={twinState}
          />
        )}

        {activeTab === 'data' && (
          <PatientDataSection
            patientId={selectedPatientId}
            measurements={measurements}
            onDataChanged={() => loadPatientData(selectedPatientId)}
            onLoadSynthetic={handleLoadSynthetic}
          />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationSection patientId={selectedPatientId} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 px-6 text-center text-xs text-slate-500">
        <p>
          <strong>Hackloop 2026</strong> • Digital Twin of a Patient Prototype • Built with FastAPI, SQLAlchemy, React, Vite & Tailwind CSS.
        </p>
        <p className="mt-1 text-[11px] text-slate-400">
          This system is a research and educational prototype. It does not replace clinicians, diagnose diseases, or prescribe medication.
        </p>
      </footer>
    </div>
  );
}

export default App;
