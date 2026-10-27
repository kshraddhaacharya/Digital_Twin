import React from 'react';
import { Heart, RefreshCw, Sparkles, ShieldCheck } from 'lucide-react';
import { Patient } from '../types';

interface NavbarProps {
  patients: Patient[];
  selectedPatientId: string;
  onSelectPatient: (id: string) => void;
  onRefresh: () => void;
  onLoadSynthetic: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  loading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  patients,
  selectedPatientId,
  onSelectPatient,
  onRefresh,
  onLoadSynthetic,
  activeTab,
  setActiveTab,
  loading,
}) => {
  // Only THREE primary, senior-friendly sections
  const tabs = [
    { id: 'my-health', label: '1. My Health' },
    { id: 'future-outlook', label: '2. Future Outlook' },
    { id: 'record-history', label: '3. Record History' },
  ];

  return (
    <header className="bg-white border-b-2 border-slate-200 sticky top-0 z-30 shadow-sm">
      {/* Calm, reassuring senior-friendly safety bar */}
      <div className="bg-slate-900 text-white px-4 py-2 text-sm flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center space-x-2 text-center sm:text-left">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          <span className="font-medium text-slate-200 text-sm">
            Patient Digital Twin • Research & Educational Assistant
          </span>
        </div>
        <div className="flex items-center space-x-3 text-xs text-slate-300">
          <span className="flex items-center space-x-1.5 bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Blockchain Security: Active</span>
          </span>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Logo & Simple Title */}
          <div className="flex items-center space-x-3">
            <div className="bg-purple-700 text-white p-2.5 rounded-xl shadow-sm flex items-center justify-center">
              <Heart className="w-7 h-7 text-white fill-white" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-900 leading-tight">
                My Health Twin
              </h1>
              <p className="text-sm text-slate-600 font-medium">
                Simple, secure health trend tracking
              </p>
            </div>
          </div>

          {/* Senior-Friendly Quick Action Controls */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Quick Demo Button (Large & prominent) */}
            <button
              onClick={onLoadSynthetic}
              disabled={loading}
              className="bg-purple-700 hover:bg-purple-800 text-white font-bold text-base px-5 py-3 rounded-xl shadow-sm transition-all flex items-center space-x-2 min-h-[48px] active:scale-95"
            >
              <Sparkles className="w-5 h-5 text-purple-200" />
              <span>Try Demo Patient</span>
            </button>

            {/* Patient selector */}
            <div className="flex items-center space-x-2 bg-slate-100 px-3 py-2 rounded-xl border border-slate-300 min-h-[48px]">
              <label htmlFor="patient-select" className="text-sm font-semibold text-slate-700">
                Patient:
              </label>
              <select
                id="patient-select"
                value={selectedPatientId}
                onChange={(e) => onSelectPatient(e.target.value)}
                className="bg-transparent text-base font-bold text-slate-900 focus:outline-none cursor-pointer"
              >
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={loading}
              title="Refresh readings"
              className="p-3 text-slate-700 hover:text-purple-700 hover:bg-slate-100 rounded-xl transition-colors border border-slate-300 min-h-[48px] min-w-[48px] flex items-center justify-center"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-purple-700' : ''}`} />
            </button>
          </div>
        </div>

        {/* 3 Primary Navigation Tabs (Large, High Contrast, Accessible) */}
        <nav className="mt-4 grid grid-cols-3 gap-2 border-t-2 border-slate-100 pt-3">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3.5 px-3 text-base sm:text-lg font-bold rounded-xl transition-all text-center min-h-[48px] flex items-center justify-center ${
                  isActive
                    ? 'bg-purple-700 text-white shadow-md'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
