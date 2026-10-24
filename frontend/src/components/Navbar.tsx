import React from 'react';
import { Activity, ShieldAlert, User, RefreshCw, Blocks, ShieldCheck } from 'lucide-react';
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
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'twin', label: 'Digital Twin Engine' },
    { id: 'web3', label: 'Web3 & Sovereignty' },
    { id: 'forecast', label: 'Forecasting' },
    { id: 'scenarios', label: 'Scenario Comparison' },
    { id: 'data', label: 'Patient Data & Ingestion' },
    { id: 'evaluation', label: 'Model Evaluation' },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      {/* Educational prototype disclaimer top banner */}
      <div className="bg-slate-900 text-slate-200 px-4 py-1.5 text-xs font-semibold flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>
            HACKLOOP 2026: Web3 Decentralized Patient Digital Twin • Smart Contract Attested • Educational Prototype
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="hidden md:inline bg-purple-900/60 text-purple-300 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border border-purple-500/40">
            Smart Contract Verified
          </span>
          <span className="hidden md:inline bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border border-emerald-500/40">
            IPFS Content-Addressed
          </span>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & title */}
          <div className="flex items-center space-x-3">
            <div className="bg-purple-600 text-white p-2 rounded-lg shadow-sm">
              <Blocks className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 leading-tight flex items-center space-x-2">
                <span>Decentralized Patient Digital Twin</span>
                <span className="text-[10px] bg-purple-100 text-purple-800 font-extrabold px-1.5 py-0.5 rounded border border-purple-300 uppercase">
                  Web3 Core
                </span>
              </h1>
              <p className="text-xs text-slate-500">
                Hackloop 2026 • EVM Smart Contracts • IPFS Anchoring • Sovereign Consent
              </p>
            </div>
          </div>

          {/* Web3 Wallet and Patient Selector */}
          <div className="flex items-center space-x-3">
            {/* Connected Web3 Identity Pill */}
            <div
              onClick={() => setActiveTab('web3')}
              className="hidden lg:flex items-center space-x-2 bg-purple-50 hover:bg-purple-100 border border-purple-200 px-3 py-1.5 rounded-lg cursor-pointer transition-colors"
              title="Click to view Web3 Smart Contract & Sovereign Governance"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-[11px] font-mono font-bold text-purple-900">
                0x7E5F...5Bdf (EVM)
              </span>
            </div>

            <div className="flex items-center space-x-2 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
              <User className="w-4 h-4 text-slate-500" />
              <label htmlFor="patient-select" className="text-xs font-medium text-slate-600 hidden sm:inline">
                Patient:
              </label>
              <select
                id="patient-select"
                value={selectedPatientId}
                onChange={(e) => onSelectPatient(e.target.value)}
                className="bg-transparent text-sm font-semibold text-slate-800 focus:outline-none cursor-pointer"
              >
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.id})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={onRefresh}
              disabled={loading}
              title="Refresh Current Data"
              className="p-2 text-slate-600 hover:text-twin-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-twin-600' : ''}`} />
            </button>

            <button
              onClick={onLoadSynthetic}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold px-3 py-2 rounded-lg shadow-sm transition-all flex items-center space-x-1.5 disabled:opacity-50"
            >
              <span>Reload Demo</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto pb-1 scrollbar-none border-t border-slate-100 pt-1">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-2 text-sm font-medium rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-purple-50 text-purple-700 font-semibold border-b-2 border-purple-600'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
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
