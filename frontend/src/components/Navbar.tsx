import React from 'react';
import {
  Heart,
  RefreshCw,
  Sparkles,
  ShieldCheck,
  UserCheck,
  LogOut,
  LayoutDashboard,
  FileText,
  Video,
  Activity,
  Calendar,
  Home
} from 'lucide-react';
import { Patient, User } from '../types';

interface NavbarProps {
  user: User | null;
  patients: Patient[];
  selectedPatientId: string;
  onSelectPatient: (id: string) => void;
  onRefresh: () => void;
  onLoadSynthetic: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  loading: boolean;
  onLogout: () => void;
  onGoHome?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  patients,
  selectedPatientId,
  onSelectPatient,
  onRefresh,
  onLoadSynthetic,
  activeTab,
  setActiveTab,
  loading,
  onLogout,
  onGoHome,
}) => {
  // Navigation tabs based on user context
  const isFemale = user?.gender === 'Female';

  const primaryTabs = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'my-health', label: '1. My Health', icon: Heart },
    { id: 'future-outlook', label: '2. Future Outlook', icon: Activity },
    { id: 'record-history', label: '3. Record History', icon: RefreshCw },
    { id: 'reports', label: 'Medical Reports', icon: FileText },
    { id: 'videos', label: 'Videos', icon: Video },
    { id: 'disease-tracker', label: 'Disease Tracker', icon: Activity },
    ...(isFemale ? [{ id: 'cycle-tracker', label: 'Period Tracker', icon: Calendar }] : []),
    { id: 'profile', label: 'My Profile', icon: UserCheck },
  ];

  return (
    <header className="bg-white border-b-2 border-slate-200 sticky top-0 z-30 shadow-sm">
      {/* Top security status bar */}
      <div className="bg-slate-900 text-white px-4 py-1.5 text-xs flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          <span className="font-semibold text-slate-200">
            Sovereign Health Twin • Research & Educational Assistant
          </span>
        </div>
        <div className="flex items-center space-x-3 text-slate-300">
          <span className="flex items-center space-x-1.5 bg-slate-800 px-3 py-0.5 rounded-full border border-slate-700">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Web3 Blockchain Security: Active</span>
          </span>
          {user && (
            <span className="font-medium text-purple-300">
              Logged in: <strong>{user.full_name}</strong>
            </span>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Logo & Simple Title */}
          <div
            className="flex items-center space-x-3 cursor-pointer"
            onClick={onGoHome ? onGoHome : () => setActiveTab('dashboard')}
          >
            <div className="bg-purple-700 text-white p-2.5 rounded-2xl shadow-sm flex items-center justify-center">
              <Heart className="w-6 h-6 fill-white" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-slate-900 leading-tight">
                Sovereign Health Twin
              </h1>
              <p className="text-xs text-slate-600 font-medium">
                Continuous physiological modeling & Web3 integrity
              </p>
            </div>
          </div>

          {/* Quick Action Controls */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Home Link */}
            {onGoHome && (
              <button
                onClick={onGoHome}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-sm px-3.5 py-2 rounded-xl transition flex items-center space-x-1.5 min-h-[44px]"
              >
                <Home className="w-4 h-4 text-slate-600" />
                <span>Home Page</span>
              </button>
            )}

            {/* Quick Demo Button */}
            <button
              onClick={onLoadSynthetic}
              disabled={loading}
              className="bg-purple-50 hover:bg-purple-100 text-purple-900 font-bold text-sm px-3.5 py-2 rounded-xl border border-purple-200 transition flex items-center space-x-1.5 min-h-[44px]"
            >
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span>Load Demo Patient</span>
            </button>

            {/* Patient selector */}
            <div className="flex items-center space-x-1.5 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-300 min-h-[44px]">
              <label htmlFor="patient-select" className="text-xs font-semibold text-slate-600">
                Patient:
              </label>
              <select
                id="patient-select"
                value={selectedPatientId}
                onChange={(e) => onSelectPatient(e.target.value)}
                className="bg-transparent text-sm font-bold text-slate-900 focus:outline-none cursor-pointer"
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
              title="Refresh Health Data"
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 transition min-h-[44px] min-w-[44px] flex items-center justify-center"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-purple-700' : ''}`} />
            </button>

            {/* Logout button */}
            {user && (
              <button
                onClick={onLogout}
                title="Sign out of account"
                className="bg-red-50 hover:bg-red-100 text-red-700 font-bold text-sm px-3.5 py-2 rounded-xl border border-red-200 transition flex items-center space-x-1.5 min-h-[44px]"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            )}
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <nav className="flex space-x-1 overflow-x-auto pt-3 pb-1 border-t border-slate-100 mt-2.5">
          {primaryTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-sm font-bold transition whitespace-nowrap min-h-[40px] ${
                  isActive
                    ? 'bg-purple-700 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
