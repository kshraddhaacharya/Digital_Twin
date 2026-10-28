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
  Activity,
  ChevronDown
} from 'lucide-react';
import { MedicalReport } from '../types';
import { api } from '../services/api';
import { formatISTDateOnly, formatIST } from '../utils/dateUtils';

interface ReportsViewProps {
  patientId: string;
  reports: MedicalReport[];
  onReportsChanged: () => void;
  onNavigateToTwin: () => void;
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  patientId,
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
  const [latestUploadedReport, setLatestUploadedReport] = useState<MedicalReport | null>(null);

  const [activeReport, setActiveReport] = useState<MedicalReport | null>(null);
  const [confirmModalReport, setConfirmModalReport] = useState<MedicalReport | null>(null);
  const [confirmedItems, setConfirmedItems] = useState<Record<string, { key: string; value: number; unit?: string; selected: boolean }>>({});
  const [confirmingBiomarkers, setConfirmingBiomarkers] = useState<boolean>(false);
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [bannerMsg, setBannerMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const openConfirmModal = (report: MedicalReport) => {
    setConfirmModalReport(report);
    const initial: Record<string, { key: string; value: number; unit?: string; selected: boolean }> = {};
    (report.biomarkers || []).forEach((b) => {
      initial[b.key] = {
        key: b.key,
        value: typeof b.value === 'number' ? b.value : parseFloat(String(b.value)) || 0,
        unit: b.unit,
        selected: true,
      };
    });
    setConfirmedItems(initial);
  };

  const handleConfirmBiomarkers = async () => {
    if (!confirmModalReport) return;
    setConfirmingBiomarkers(true);
    try {
      const itemsToConfirm = Object.values(confirmedItems)
        .filter((i) => i.selected)
        .map((i) => ({ key: i.key, value: i.value, unit: i.unit }));

      if (itemsToConfirm.length === 0) {
        alert('Please select at least one extracted vital to confirm.');
        setConfirmingBiomarkers(false);
        return;
      }

      let confirmedCount = 0;
      for (const item of itemsToConfirm) {
        if (item.key === 'heart_rate') {
          await api.confirmReportBiomarkers(confirmModalReport.id, {
            key: item.key,
            value: item.value,
            unit: item.unit || 'bpm',
            context: 'resting',
          });
          confirmedCount++;
        }
      }

      setBannerMsg({
        text: `✓ Successfully confirmed ${confirmedCount} clinical vital reading(s)! Digital twin updated and anchored on-chain.`,
        type: 'success'
      });
      setConfirmModalReport(null);
      onReportsChanged();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to confirm biomarkers.');
    } finally {
      setConfirmingBiomarkers(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setBannerMsg({ text: 'Please select a PDF, JPG, or PNG report file to upload.', type: 'error' });
      return;
    }

    setUploading(true);
    setBannerMsg(null);
    try {
      const res = await api.uploadReport(selectedFile, uploadTitle, uploadDate, uploadDesc, patientId);
      setLatestUploadedReport(res.report);
      setBannerMsg({
        text: `Report "${res.report.title}" uploaded & analyzed! Extracted ${res.report.biomarkers?.length || 0} clinical parameter(s).`,
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
            className="bg-purple-700 hover:bg-purple-800 text-white font-extrabold text-lg px-8 py-3.5 rounded-2xl shadow-md transition flex items-center space-x-2 min-h-[48px] disabled:opacity-50"
          >
            <Upload className="w-5 h-5" />
            <span>{uploading ? 'Extracting Text & Clinical Parameters...' : 'Upload & Analyze Document'}</span>
          </button>
        </form>
      </div>

      {/* RECENTLY PROCESSED REPORT SUMMARY CARD */}
      {latestUploadedReport && (
        <div className="bg-white p-6 sm:p-8 rounded-3xl border-2 border-purple-400 shadow-md space-y-5 animate-in fade-in duration-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-100 pb-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="bg-purple-100 text-purple-900 font-bold text-xs px-3 py-1 rounded-full uppercase">
                  Latest Processed Report
                </span>
                <span className="bg-emerald-100 text-emerald-900 font-bold text-xs px-3 py-1 rounded-full flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                  <span>Processed & Saved</span>
                </span>
              </div>
              <h3 className="text-2xl font-black text-slate-900">{latestUploadedReport.title}</h3>
              <p className="text-xs text-slate-500 font-semibold">
                Report Date: {formatISTDateOnly(latestUploadedReport.report_date)} • Uploaded: {formatIST(latestUploadedReport.created_at)} • Format: {latestUploadedReport.file_type?.toUpperCase()} ({(latestUploadedReport.file_size_bytes / 1024).toFixed(1)} KB) • Patient: {latestUploadedReport.patient_id || patientId}
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setLatestUploadedReport(null)}
                className="text-slate-400 hover:text-slate-600 p-2 rounded-xl transition"
                title="Dismiss"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Structured Clinical Summary Box */}
          <div className="p-5 bg-purple-50/80 border-2 border-purple-200 rounded-2xl space-y-2">
            <h4 className="text-sm font-bold text-purple-950 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-purple-700" />
              <span>Report Clinical Summary</span>
            </h4>
            <p className="text-base text-slate-800 leading-relaxed font-medium">
              {latestUploadedReport.summary || latestUploadedReport.description || 'Document uploaded and analyzed.'}
            </p>
          </div>

          {/* Extracted Parameters Table / Cards */}
          {latestUploadedReport.biomarkers && latestUploadedReport.biomarkers.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                  Recognized Clinical Parameters ({latestUploadedReport.biomarkers.length}):
                </h4>
                <button
                  onClick={() => openConfirmModal(latestUploadedReport)}
                  className="bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs px-4 py-2 rounded-xl shadow-sm transition flex items-center space-x-1.5"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>Review & Confirm Vitals</span>
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse bg-slate-50 rounded-2xl overflow-hidden border border-slate-200">
                  <thead className="bg-slate-100 text-slate-700 font-extrabold text-xs uppercase border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Biomarker / Vital</th>
                      <th className="px-4 py-3">Observed Value</th>
                      <th className="px-4 py-3">Standard Reference Range</th>
                      <th className="px-4 py-3">Clinical Status</th>
                      <th className="px-4 py-3 text-right">Confirmation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 font-semibold text-slate-900">
                    {latestUploadedReport.biomarkers.map((b, idx) => (
                      <tr key={idx} className="hover:bg-white transition-colors">
                        <td className="px-4 py-3 font-bold text-slate-900">{b.name}</td>
                        <td className="px-4 py-3">
                          <span className="text-base font-black text-purple-900">{b.value}</span>{' '}
                          <span className="text-xs text-slate-600">{b.unit}</span>
                        </td>
                        <td className="px-4 py-3 text-slate-600 font-mono text-xs">{b.reference_range}</td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold capitalize ${
                              b.status === 'normal'
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : 'bg-amber-100 text-amber-800 border border-amber-300'
                            }`}
                          >
                            {b.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-xs text-slate-500">
                          {b.requires_confirmation ? 'Awaiting Review' : 'Auto-detected'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : latestUploadedReport.is_scanned ? (
            <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-2xl text-amber-950 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h5 className="font-bold text-sm text-amber-900">Scanned Document Notice</h5>
                <p className="text-xs text-amber-800 mt-0.5">
                  Text extraction was unsuccessful because no digital text layer was found in this scanned or image-based file. Automated OCR is not configured. Please consult the document file directly or enter vitals manually in Vital Readings.
                </p>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl text-slate-600 text-sm">
              Document parsed successfully. No standard cardiovascular or metabolic parameters matched configured vital patterns.
            </div>
          )}

          {/* Real Extracted Text Preview */}
          {latestUploadedReport.extracted_text && (
            <details className="mt-3 group">
              <summary className="cursor-pointer text-xs font-bold text-purple-700 hover:text-purple-900 flex items-center space-x-1 select-none">
                <span>View Raw Extracted Document Text</span>
                <ChevronDown className="w-4 h-4 transition group-open:rotate-180" />
              </summary>
              <div className="mt-2 p-4 bg-slate-900 text-slate-100 rounded-2xl font-mono text-xs whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed border border-slate-700">
                {latestUploadedReport.extracted_text}
              </div>
            </details>
          )}
        </div>
      )}

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
                className="p-5 rounded-2xl border-2 border-slate-200 bg-white hover:border-purple-300 transition shadow-sm space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-black text-lg text-slate-900">{report.title}</span>
                      <span className="bg-slate-100 text-slate-700 border border-slate-300 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">
                        {report.file_type}
                      </span>
                      {report.is_scanned && (
                        <span className="bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-bold px-2 py-0.5 rounded-full">
                          Scanned
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 font-semibold">
                      Date: {formatISTDateOnly(report.report_date)} • Uploaded: {formatIST(report.created_at)} • File: {report.file_name} ({(report.file_size_bytes / 1024).toFixed(1)} KB)
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

                {/* Readable Summary */}
                {report.summary ? (
                  <div className="p-3 bg-purple-50/60 rounded-xl border border-purple-100 text-xs text-slate-800 leading-relaxed font-medium">
                    <span className="font-bold text-purple-950">Summary: </span>
                    {report.summary}
                  </div>
                ) : report.description ? (
                  <p className="text-sm text-slate-600 italic">{report.description}</p>
                ) : null}

                {/* Detected Biomarkers Row */}
                {report.biomarkers && report.biomarkers.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-bold text-slate-500 uppercase">Extracted Parameters:</span>
                      {report.biomarkers.map((b, idx) => (
                        <span
                          key={idx}
                          className={`text-xs font-bold px-2.5 py-1 rounded-xl border flex items-center space-x-1.5 ${
                            b.status === 'normal'
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                              : 'bg-amber-50 text-amber-800 border-amber-300'
                          }`}
                        >
                          <span>{b.name}:</span>
                          <span className="underline font-black">{b.value} {b.unit}</span>
                          <span className="text-[10px] text-slate-500">({b.reference_range})</span>
                          <span className="capitalize text-[10px] bg-white/70 px-1.5 py-0.2 rounded font-extrabold">{b.status}</span>
                        </span>
                      ))}
                    </div>

                    {/* Action buttons for extracted vitals */}
                    <div className="flex items-center space-x-2 pt-1">
                      <button
                        onClick={() => openConfirmModal(report)}
                        className="bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs px-3 py-1.5 rounded-xl shadow-sm transition flex items-center space-x-1"
                      >
                        <FileCheck className="w-3.5 h-3.5" />
                        <span>Review & Confirm Vitals</span>
                      </button>

                      {report.biomarkers.some((b) => b.key === 'heart_rate') && (
                        <button
                          onClick={() => handleSyncToTwin(report.id)}
                          disabled={syncingId === report.id}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3 py-1.5 rounded-xl shadow-sm transition flex items-center space-x-1"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>{syncingId === report.id ? 'Syncing...' : 'Sync Vital to Twin (Web3)'}</span>
                        </button>
                      )}
                    </div>
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
                Report Date: {formatISTDateOnly(activeReport.report_date)} • Uploaded: {formatIST(activeReport.created_at)} • Format: {activeReport.file_type.toUpperCase()}
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

      {/* MODAL: BIOMARKER REVIEW & CONFIRM */}
      {confirmModalReport && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto space-y-6">
            <button
              onClick={() => setConfirmModalReport(null)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-700 p-2"
            >
              <X className="w-6 h-6" />
            </button>

            <div className="space-y-1">
              <div className="inline-flex items-center space-x-2 bg-purple-100 text-purple-900 px-3 py-1 rounded-full text-xs font-bold">
                <FileCheck className="w-3.5 h-3.5" />
                <span>Patient Review & Confirmation Protocol</span>
              </div>
              <h3 className="text-2xl font-black text-slate-900">
                Confirm Extracted Vitals for Digital Twin
              </h3>
              <p className="text-sm text-slate-600 font-medium">
                From report: <strong>{confirmModalReport.title}</strong> ({formatISTDateOnly(confirmModalReport.report_date)})
              </p>
            </div>

            <div className="p-4 bg-amber-50 border-2 border-amber-200 rounded-2xl text-xs text-amber-900 leading-relaxed">
              <strong>Clinical Safety Step:</strong> Review each extracted parameter before incorporating it into your physiological state. You can edit values or uncheck parameters if OCR or laboratory extraction was inaccurate.
            </div>

            {/* List of biomarkers to confirm */}
            <div className="space-y-3">
              {confirmModalReport.biomarkers.map((b) => {
                const item = confirmedItems[b.key] || {
                  key: b.key,
                  value: typeof b.value === 'number' ? b.value : 0,
                  unit: b.unit,
                  selected: true
                };
                return (
                  <div
                    key={b.key}
                    className={`p-4 rounded-2xl border-2 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                      item.selected
                        ? 'bg-purple-50/50 border-purple-300'
                        : 'bg-slate-50 border-slate-200 opacity-60'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={item.selected}
                        onChange={(e) =>
                          setConfirmedItems({
                            ...confirmedItems,
                            [b.key]: { ...item, selected: e.target.checked }
                          })
                        }
                        className="w-5 h-5 rounded text-purple-700 focus:ring-purple-600 cursor-pointer"
                      />
                      <div>
                        <span className="font-bold text-slate-900 text-base">{b.name}</span>
                        <div className="text-xs text-slate-500">
                          Reference: {b.reference_range} • Status: <span className="capitalize font-semibold">{b.status}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 pl-8 sm:pl-0">
                      <input
                        type="number"
                        step="any"
                        value={item.value}
                        onChange={(e) =>
                          setConfirmedItems({
                            ...confirmedItems,
                            [b.key]: { ...item, value: parseFloat(e.target.value) || 0 }
                          })
                        }
                        disabled={!item.selected}
                        className="w-24 p-2 text-base font-bold bg-white border-2 border-slate-300 rounded-xl focus:outline-none focus:border-purple-600 disabled:bg-slate-100"
                      />
                      <span className="text-sm font-semibold text-slate-600 w-16">{item.unit || b.unit}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex flex-col sm:flex-row justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                onClick={() => setConfirmModalReport(null)}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-5 py-3 rounded-xl text-sm"
              >
                Cancel
              </button>

              <button
                onClick={handleConfirmBiomarkers}
                disabled={confirmingBiomarkers}
                className="bg-purple-700 hover:bg-purple-800 text-white font-extrabold px-6 py-3 rounded-xl text-sm shadow-md transition flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <FileCheck className="w-4 h-4" />
                <span>{confirmingBiomarkers ? 'Updating Twin State...' : 'Confirm & Feed Into Twin'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
