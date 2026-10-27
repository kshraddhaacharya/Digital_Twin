import React, { useState, useEffect } from 'react';
import { LandingPage } from './components/LandingPage';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { MyHealthView } from './components/MyHealthView';
import { FutureOutlookView } from './components/FutureOutlookView';
import { RecordHistoryView } from './components/RecordHistoryView';
import { ProfileView } from './components/ProfileView';
import { ReportsView } from './components/ReportsView';
import { VideosView } from './components/VideosView';
import { DiseaseTrackerView } from './components/DiseaseTrackerView';
import { CycleTrackerView } from './components/CycleTrackerView';
import { api } from './services/api';
import {
  User,
  Patient,
  TwinState,
  Measurement,
  Forecast,
  MedicalReport,
  UserVideo,
  HealthCondition,
  ConditionLog,
  DiseaseAnalytics,
  CycleSummary,
  CycleLog
} from './types';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<string>('landing');

  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('PT-DEMO-001');

  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null);
  const [twinState, setTwinState] = useState<TwinState | null>(null);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);

  // Features data
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [videos, setVideos] = useState<UserVideo[]>([]);
  const [conditions, setConditions] = useState<HealthCondition[]>([]);
  const [conditionLogs, setConditionLogs] = useState<ConditionLog[]>([]);
  const [diseaseAnalytics, setDiseaseAnalytics] = useState<DiseaseAnalytics | null>(null);
  const [cycleSummary, setCycleSummary] = useState<CycleSummary | null>(null);
  const [cycleHistory, setCycleHistory] = useState<CycleLog[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize session from token if available
  useEffect(() => {
    const initSession = async () => {
      const token = api.getToken();
      if (token) {
        try {
          const user = await api.getMe();
          setCurrentUser(user);
          setSelectedPatientId(user.patient_id);
          setActiveTab('dashboard');
        } catch (err) {
          api.setToken(null);
          setCurrentUser(null);
        }
      }
    };
    initSession();
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const pts = await api.getPatients();
      setPatients(pts);
      if (pts.length > 0 && !pts.some((p) => p.id === selectedPatientId)) {
        setSelectedPatientId(pts[0].id);
      }
    } catch (err) {
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

      if (ptData.status === 'fulfilled') setCurrentPatient(ptData.value);
      if (tState.status === 'fulfilled') setTwinState(tState.value);
      else setTwinState(null);

      if (meas.status === 'fulfilled') setMeasurements(meas.value);
      else setMeasurements([]);

      if (fcs.status === 'fulfilled') setForecasts(fcs.value);
      else setForecasts([]);
    } catch (err) {
      setError('Failed to load patient records.');
    } finally {
      setLoading(false);
    }
  };

  const loadUserFeatures = async () => {
    if (!currentUser) return;
    try {
      const [reps, vids, conds, logs, analytics, cSum, cHist] = await Promise.allSettled([
        api.getReports(),
        api.getVideos(),
        api.getConditions(),
        api.getConditionLogs(),
        api.getDiseaseAnalytics(),
        api.getCycleSummary(),
        api.getCycleHistory(),
      ]);

      if (reps.status === 'fulfilled') setReports(reps.value);
      if (vids.status === 'fulfilled') setVideos(vids.value);
      if (conds.status === 'fulfilled') setConditions(conds.value);
      if (logs.status === 'fulfilled') setConditionLogs(logs.value);
      if (analytics.status === 'fulfilled') setDiseaseAnalytics(analytics.value);
      if (cSum.status === 'fulfilled') setCycleSummary(cSum.value);
      if (cHist.status === 'fulfilled') setCycleHistory(cHist.value);
    } catch (err) {
      console.error('Error loading user features:', err);
    }
  };

  useEffect(() => {
    if (selectedPatientId) {
      loadPatientData(selectedPatientId);
    }
  }, [selectedPatientId]);

  useEffect(() => {
    if (currentUser) {
      loadUserFeatures();
    }
  }, [currentUser]);

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    setSelectedPatientId(user.patient_id);
    setActiveTab('dashboard');
    loadPatients();
    loadPatientData(user.patient_id);
  };

  const handleLogout = () => {
    api.setToken(null);
    setCurrentUser(null);
    setActiveTab('landing');
  };

  const handleExploreDemo = () => {
    setSelectedPatientId('PT-DEMO-001');
    setActiveTab('dashboard');
    loadPatientData('PT-DEMO-001');
  };

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

  // If user is on landing page, display the public landing page
  if (activeTab === 'landing' && !currentUser) {
    return (
      <LandingPage
        onLoginSuccess={handleLoginSuccess}
        onExploreDemo={handleExploreDemo}
      />
    );
  }

  // Authenticated or Demo Dashboard Layout
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 font-sans" style={{ fontSize: '18px' }}>
      <Navbar
        user={currentUser}
        patients={patients}
        selectedPatientId={selectedPatientId}
        onSelectPatient={(id) => setSelectedPatientId(id)}
        onRefresh={() => {
          loadPatientData(selectedPatientId);
          if (currentUser) loadUserFeatures();
        }}
        onLoadSynthetic={handleLoadSynthetic}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        loading={loading}
        onLogout={handleLogout}
        onGoHome={() => setActiveTab('landing')}
      />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-2 border-red-300 text-red-900 rounded-2xl text-base font-semibold shadow-sm">
            {error}
          </div>
        )}

        {/* View 1: Personalized Dashboard */}
        {activeTab === 'dashboard' && (
          <DashboardView
            user={currentUser || {
              id: 'USR-DEMO',
              email: 'demo@patient.org',
              full_name: currentPatient?.name || 'Alice M. Taylor',
              patient_id: selectedPatientId,
              gender: currentPatient?.gender || 'Female',
              age: currentPatient?.age || 56,
              height: 165,
              body_weight: 68,
              existing_conditions: currentPatient?.medical_notes || 'Demonstration Patient',
              created_at: new Date().toISOString()
            }}
            twinState={twinState}
            recentMeasurements={measurements}
            reports={reports}
            videos={videos}
            diseaseAnalytics={diseaseAnalytics}
            onNavigate={(tab) => setActiveTab(tab)}
            onQuickLoadDemo={handleLoadSynthetic}
          />
        )}

        {/* View 2: My Health Screen */}
        {activeTab === 'my-health' && (
          <MyHealthView
            patient={currentPatient}
            twinState={twinState}
            recentMeasurements={measurements}
            onNavigateTab={(tab) => setActiveTab(tab)}
            onLoadSynthetic={handleLoadSynthetic}
          />
        )}

        {/* View 3: Future Outlook Screen */}
        {activeTab === 'future-outlook' && (
          <FutureOutlookView
            patientId={selectedPatientId}
            twinState={twinState}
            measurements={measurements}
            forecasts={forecasts}
            onRefreshData={() => loadPatientData(selectedPatientId)}
          />
        )}

        {/* View 4: Record History Screen */}
        {activeTab === 'record-history' && (
          <RecordHistoryView
            patientId={selectedPatientId}
            measurements={measurements}
            twinState={twinState}
            onDataChanged={() => loadPatientData(selectedPatientId)}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {/* View 5: Medical Reports & Search Engine */}
        {activeTab === 'reports' && (
          <ReportsView
            reports={reports}
            onReportsChanged={loadUserFeatures}
            onNavigateToTwin={() => setActiveTab('my-health')}
          />
        )}

        {/* View 6: Personal Video Library */}
        {activeTab === 'videos' && (
          <VideosView
            videos={videos}
            onVideosChanged={loadUserFeatures}
          />
        )}

        {/* View 7: Disease Tracker & Timeline */}
        {activeTab === 'disease-tracker' && (
          <DiseaseTrackerView
            conditions={conditions}
            logs={conditionLogs}
            analytics={diseaseAnalytics}
            onDataChanged={loadUserFeatures}
          />
        )}

        {/* View 8: Period Cycle Tracker */}
        {activeTab === 'cycle-tracker' && (
          <CycleTrackerView
            summary={cycleSummary}
            history={cycleHistory}
            onDataChanged={loadUserFeatures}
          />
        )}

        {/* View 9: My Health Profile Management */}
        {activeTab === 'profile' && (
          <ProfileView
            user={currentUser || {
              id: 'USR-DEMO',
              email: 'demo@patient.org',
              full_name: currentPatient?.name || 'Alice M. Taylor',
              patient_id: selectedPatientId,
              gender: currentPatient?.gender || 'Female',
              age: currentPatient?.age || 56,
              height: 165,
              body_weight: 68,
              existing_conditions: currentPatient?.medical_notes || 'Demonstration Patient',
              created_at: new Date().toISOString()
            }}
            onProfileUpdated={(updated) => {
              setCurrentUser(updated);
              loadUserFeatures();
            }}
            onLogout={handleLogout}
          />
        )}
      </main>

      {/* Reassuring Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-slate-600 text-sm">
        <div className="max-w-5xl mx-auto px-4 space-y-2">
          <p className="font-semibold text-slate-800">
            HackLoop 2026: Sovereign Health Twin Platform
          </p>
          <p className="text-xs text-slate-500">
            Continuous Physiological Modeling • Web3 Ethereum Smart Contract Integrity • Medical Report Search • Privacy First.
            For research & educational purposes only.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
