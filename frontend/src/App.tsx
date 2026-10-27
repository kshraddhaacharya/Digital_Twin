import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { MyHealthView } from './components/MyHealthView';
import { FutureOutlookView } from './components/FutureOutlookView';
import { RecordHistoryView } from './components/RecordHistoryView';
import { api } from './services/api';
import { Patient, TwinState, Measurement, Forecast } from './types';

export function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('PT-DEMO-001');
  const [activeTab, setActiveTab] = useState<string>('my-health');
  
  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null);
  const [twinState, setTwinState] = useState<TwinState | null>(null);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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

  const loadPatientData = async (patientId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [ptData, tState, meas, fcs] = await Promise.allSettled([
        api.getPatient(patientId),
        api.getTwinState(patientId),
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
      setError('Failed to load patient data.');
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
      setActiveTab('my-health');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to load demo patient.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 font-sans" style={{ fontSize: '18px' }}>
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

      <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-2 border-red-300 text-red-900 rounded-2xl text-lg font-semibold shadow-sm">
            {error}
          </div>
        )}

        {activeTab === 'my-health' && (
          <MyHealthView
            patient={currentPatient}
            twinState={twinState}
            recentMeasurements={measurements}
            onNavigateTab={(tab) => setActiveTab(tab)}
            onLoadSynthetic={handleLoadSynthetic}
          />
        )}

        {activeTab === 'future-outlook' && (
          <FutureOutlookView
            patientId={selectedPatientId}
            twinState={twinState}
            measurements={measurements}
            forecasts={forecasts}
            onRefreshData={() => loadPatientData(selectedPatientId)}
          />
        )}

        {activeTab === 'record-history' && (
          <RecordHistoryView
            patientId={selectedPatientId}
            measurements={measurements}
            twinState={twinState}
            onDataChanged={() => loadPatientData(selectedPatientId)}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}
      </main>

      {/* Simplified, reassuring footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-slate-600 text-sm">
        <div className="max-w-4xl mx-auto px-4 space-y-2">
          <p className="font-semibold text-slate-800">
            HackLoop 2026: Web3-Powered Patient Digital Twin
          </p>
          <p className="text-xs text-slate-500">
            For research & educational purposes only. Not intended for direct medical diagnosis or clinical treatment.
            Cryptographic attestations secured by Ethereum Smart Contracts.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;

