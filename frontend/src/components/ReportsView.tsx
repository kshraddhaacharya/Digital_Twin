import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  Search,
  CheckCircle2,
  AlertTriangle,
  Download,
  Trash2,
  RefreshCw,
  Sparkles,
  ExternalLink,
  X,
  FileCheck,
  Activity
} from 'lucide-react';
import { MedicalReport } from '../types';
import { api } from '../services/api';

interface ReportsViewProps {
  reports: MedicalReport[];
  onReportsChanged: () => void;
  onNavigateToTwin: () => void;
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  reports,
  onReportsChanged,
  onNavigateToTwin,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDate, setUploadDate] = useState(new Date().toISOString().slice(0, 10));
  const [uploadDesc, setUploadDesc] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [activeReport, setActiveReport] = useState<MedicalReport | null>(null);
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [bannerMsg, setBannerMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setBannerMsg({ text: 'Please select a PDF, JPG, or PNG report file to upload.', type: 'error' });
      return;
    }

    setUploading(true);
    setBannerMsg(null);
    try {
      const res = await api.uploadReport(selectedFile, uploadTitle, uploadDate, uploadDesc);
      setBannerMsg({
        text: `Report "${res.report.title}" uploaded! Extracted ${res.report.biomarkers.length} clinical parameters.`,
        type: 'success'
      });
      setUploadTitle('');
      setUploadDesc('');
      setSelectedFile(null);
      onReportsChanged();
    } catch (err: any) {
      setBannerMsg({
        text: err.response?.data?.detail || 'Failed to upload report. Please check file format and size.',
        type: 'error'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleSyncToTwin = async (reportId: number) => {
    setSyncingId(reportId);
    setBannerMsg(null);
    try {
      const res = await api.syncReportTwin(reportId);
      setBannerMsg({
        text: `${res.message} Twin updated to Version ${res.twin_state_version} and verified on blockchain!`,
        type: 'success'
      });
      onReportsChanged();
    } catch (err: any) {
      setBannerMsg({
        text: err.response?.data?.detail || 'Failed to sync vital to Digital Twin.',
        type: 'error'
      });
    } finally {
      setSyncingId(null);
    }
  };

  const handleDelete = async (reportId: number) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await api.deleteReport(reportId);
      if (activeReport?.id === reportId) setActiveReport(null);
      setBannerMsg({ text: 'Report deleted successfully.', type: 'success' });
      onReportsChanged();
    } catch (err: any) {
      setBannerMsg({ text: 'Failed to delete report.', type: 'error' });
    }
  };

  // Filter reports locally by search query if any
  const filteredReports = reports.filter((r) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.title.toLowerCase().includes(q) ||
      (r.description && r.description.toLowerCase().includes(q)) ||
      (r.extracted_text && r.extracted_text.toLowerCase().includes(q)) ||
      r.biomarkers.some((b) => b.name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border-2 border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-slate-900 flex items-center space-x-3">
            <FileText className="w-8 h-8 text-blue-600" />
            <span>Medical Report Reader & Search Engine</span>
          </h1>
          <p className="text-slate-600 text-base mt-1">
            Upload clinical lab tests, ECGs, and hospital reports in PDF or image format.
            Search inside your documents and automatically synchronize vitals with your Digital Twin.
          </p>
        </div>
      </div>

      {bannerMsg && (
        <div
          className={`p-4 rounded-2xl text-base font-semibold flex items-center space-x-2 border-2 ${
            bannerMsg.type === 'success'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
              : 'bg-red-50 border-red-300 text-red-900'
          }`}
        >
          {bannerMsg.type === 'success' ? (
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
          )}
          <span>{bannerMsg.text}</span>
        </div>
      )}

      {/* Upload Form Card */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border-2 border-slate-200 shadow-sm space-y-6">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2 border-b border-slate-200 pb-3">
          <Upload className="w-5 h-5 text-purple-700" />
          <span>Upload New Medical Report</span>
        </h2>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Report Title *</label>
              <input
                type="text"
                required
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                placeholder="e.g. Annual Blood Work & Lipid Panel"
                className="w-full p-3 bg-slate-50 border-2 border-slate-300 rounded-xl text-base font-semibold"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Report Date *</label>
              <input
                type="date"
                required
                value={uploadDate}
                onChange={(e) => setUploadDate(e.target.value)}
                className="w-full p-3 bg-slate-50 border-2 border-slate-300 rounded-xl text-base font-semibold"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Optional Notes / Description</label>
            <input
              type="text"
              value={uploadDesc}
              onChange={(e) => setUploadDesc(e.target.value)}
              placeholder="e.g. Conducted at City Hospital following routine cardiology checkup"
              className="w-full p-3 bg-slate-50 border-2 border-slate-300 rounded-xl text-base"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">
              Select Document File (PDF, JPG, JPEG, PNG • max 25MB) *
            </label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              required
              onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
              className="w-full p-2.5 bg-slate-50 border-2 border-dashed border-slate-300 rounded-xl text-sm font-medium cursor-pointer"
            />
          </div>

          <button
            type="submit"
            disabled={uploading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-black text-lg px-8 py-3.5 rounded-2xl shadow-md transition flex items-center space-x-2 min-h-[48px]"
          >
            <Upload className="w-5 h-5" />
            <span>{uploading ? 'Extracting Text & Vitals...' : 'Upload & Analyze Document'}</span>
          </button>
        </form>
      </div>

      {/* Search Engine & Report Library */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border-2 border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <Search className="w-5 h-5 text-purple-700" />
              <span>Report Search Engine</span>
            </h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Instant keyword search across all parsed report text, extracted vitals, and notes.
            </p>
          </div>

          {/* Search Bar */}
          <div className="relative w-full sm:w-80">
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search e.g. glucose, cholesterol, BP..."
              className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border-2 border-slate-300 rounded-xl text-base font-semibold focus:outline-none focus:border-purple-700"
            />
          </div>
        </div>

        {/* Reports List */}
        {filteredReports.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 rounded-2xl border border-slate-200">
            <p className="text-base font-bold text-slate-700">No matching medical reports found.</p>
            <p className="text-sm text-slate-500 mt-1">
              Upload your lab results or test sheets above to start searching.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredReports.map((report) => (
              <div
                key={report.id}
                className="p-5 rounded-2xl border-2 border-slate-200 bg-white hover:border-blue-300 transition shadow-sm space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-black text-lg text-slate-900">{report.title}</span>
                      <span className="bg-slate-100 text-slate-700 border border-slate-300 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">
                        {report.file_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 font-semibold">
                      Date: {report.report_date} • File: {report.file_name} ({(report.file_size_bytes / 1024).toFixed(1)} KB)
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setActiveReport(report)}
                      className="bg-purple-50 hover:bg-purple-100 text-purple-900 font-bold px-3 py-1.5 rounded-xl border border-purple-200 text-xs flex items-center space-x-1"
                    >
                      <Search className="w-3.5 h-3.5 text-purple-700" />
                      <span>Search & Inspect Text</span>
                    </button>

                    <a
                      href={`/api/reports/${report.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold px-3 py-1.5 rounded-xl border border-slate-300 text-xs flex items-center space-x-1"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>View Original</span>
                    </a>

                    <button
                      onClick={() => handleDelete(report.id)}
                      className="text-red-600 hover:bg-red-50 p-2 rounded-xl transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {report.description && (
                  <p className="text-sm text-slate-600 italic">{report.description}</p>
                )}

                {/* Detected Biomarkers Row */}
                {report.biomarkers && report.biomarkers.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold text-slate-500 uppercase">Extracted Vitals:</span>
                    {report.biomarkers.map((b, idx) => (
                      <span
                        key={idx}
                        className={`text-xs font-bold px-2.5 py-1 rounded-xl border flex items-center space-x-1 ${
                          b.status === 'normal'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-amber-50 text-amber-800 border-amber-200'
                        }`}
                      >
                        <span>{b.name}:</span>
                        <span className="underline">{b.value} {b.unit}</span>
                      </span>
                    ))}

                    {/* Sync to twin button if Heart Rate exists */}
                    {report.biomarkers.some((b) => b.key === 'heart_rate') && (
                      <button
                        onClick={() => handleSyncToTwin(report.id)}
                        disabled={syncingId === report.id}
                        className="ml-auto bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3 py-1.5 rounded-xl shadow-sm transition flex items-center space-x-1"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>{syncingId === report.id ? 'Syncing...' : 'Sync Vital to Twin (Web3)'}</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* MODAL: REPORT TEXT & SEARCH INSPECTOR */}
      {activeReport && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-3xl w-full p-6 sm:p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto space-y-4">
            <button
              onClick={() => setActiveReport(null)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-700 p-2"
            >
              <X className="w-6 h-6" />
            </button>

            <div className="space-y-1">
              <h3 className="text-2xl font-black text-slate-900">{activeReport.title}</h3>
              <p className="text-xs text-slate-500 font-medium">
                Report Date: {activeReport.report_date} • Format: {activeReport.file_type.toUpperCase()}
              </p>
            </div>

            {/* Biomarkers detected */}
            {activeReport.biomarkers.length > 0 && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
                <h4 className="text-xs font-bold text-slate-500 uppercase">Identified Parameters & Reference Ranges:</h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {activeReport.biomarkers.map((b, idx) => (
                    <div key={idx} className="bg-white p-2.5 rounded-xl border border-slate-200 text-xs">
                      <p className="font-bold text-slate-900">{b.name}</p>
                      <p className="text-sm font-black text-purple-700">{b.value} {b.unit}</p>
                      <p className="text-[10px] text-slate-500">Ref: {b.reference_range}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Text Viewer */}
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-slate-800">Readable Report Content:</h4>
              <div className="p-4 bg-slate-900 text-slate-100 rounded-2xl font-mono text-xs whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed border border-slate-700">
                {activeReport.extracted_text || 'No readable text could be parsed from this document.'}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setActiveReport(null)}
                className="bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold px-6 py-2.5 rounded-xl text-sm"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
