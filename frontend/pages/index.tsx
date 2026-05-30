import { useState, useCallback } from "react";
import Head from "next/head";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import toast from "react-hot-toast";
import {
  FileText, Upload, BarChart2, TrendingUp,
  AlertTriangle, CheckCircle, Loader2, Download,
  ChevronRight, Building2
} from "lucide-react";

import FinancialCharts from "../components/FinancialCharts";
import MetricsTable from "../components/MetricsTable";
import ReportSummary from "../components/ReportSummary";
import StepIndicator from "../components/StepIndicator";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STEPS = [
  { id: 1, label: "Upload Document",  icon: Upload },
  { id: 2, label: "AI Extraction",    icon: BarChart2 },
  { id: 3, label: "Generating Charts",icon: TrendingUp },
  { id: 4, label: "Building Report",  icon: FileText },
];

export default function Home() {
  const [companyName, setCompanyName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) {
      setFile(accepted[0]);
      setError(null);
      toast.success(`File ready: ${accepted[0].name}`);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf":  [".pdf"],
      "text/plain":       [".txt"],
      "text/csv":         [".csv"],
    },
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024, // 20 MB
  });

  const simulateSteps = async () => {
    for (let i = 1; i <= 4; i++) {
      setCurrentStep(i);
      await new Promise(r => setTimeout(r, i === 2 ? 8000 : 1500));
    }
  };

  const handleAnalyze = async () => {
    if (!companyName.trim()) {
      toast.error("Please enter a company name.");
      return;
    }
    if (!file) {
      toast.error("Please upload a financial document.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentStep(1);

    const stepTimer = simulateSteps();

    try {
      const form = new FormData();
      form.append("company_name", companyName.trim());
      form.append("file", file);

      const response = await axios.post(`${API_URL}/analyze`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });

      await stepTimer;
      setResult(response.data);
      setCurrentStep(4);
      toast.success("Report generated successfully!");

    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        "Analysis failed. Please try again.";
      setError(msg);
      toast.error(msg);
      setCurrentStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result?.report_url) return;
    window.open(`${API_URL}${result.report_url}`, "_blank");
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setCurrentStep(0);
    setFile(null);
    setCompanyName("");
  };

  return (
    <>
      <Head>
        <title>Geojit Financial Analyzer – AI Equity Research</title>
        <meta name="description" content="AI-powered financial document analyzer and report generator" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-[#EBF1FA] via-[#F7F9FC] to-[#E8EFF9]">

        {/* ── Header ────────────────────────────────────────────── */}
        <header className="bg-white border-b border-geojit-border shadow-sm">
          <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-geojit-blue text-white px-2 py-1 rounded font-black text-lg tracking-tight">
                G
              </div>
              <div>
                <div className="text-geojit-blue font-black text-xl tracking-tight leading-none">
                  GEOJIT
                </div>
                <div className="text-[10px] text-gray-400 tracking-widest uppercase leading-none">
                  People You Prosper With
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs font-semibold text-geojit-blue uppercase tracking-wider">
                AI Equity Research Analyzer
              </div>
              <div className="text-[10px] text-gray-400">
                Powered by OpenAI GPT-4o
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">

          {/* ── Hero ──────────────────────────────────────────── */}
          {!result && (
            <div className="mb-8 text-center">
              <h1 className="text-3xl font-black text-gray-900 mb-2">
                Financial Document Analyzer
              </h1>
              <p className="text-gray-500 text-base max-w-xl mx-auto">
                Upload any financial report (PDF, TXT, CSV). Our AI extracts key metrics,
                generates charts, and produces a professional Geojit-style PDF report.
              </p>
            </div>
          )}

          {/* ── Upload Form ───────────────────────────────────── */}
          {!result && (
            <div className="max-w-2xl mx-auto mb-8 fade-in">
              <div className="bg-white rounded-2xl shadow-md border border-geojit-border p-8">

                {/* Company Name */}
                <div className="mb-5">
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                    <Building2 size={14} className="inline mr-1.5 text-geojit-blue" />
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={e => setCompanyName(e.target.value)}
                    placeholder="e.g. Eternal Limited"
                    className="w-full border border-geojit-border rounded-lg px-4 py-2.5 text-sm
                               focus:outline-none focus:ring-2 focus:ring-geojit-blue/30 focus:border-geojit-blue
                               transition-all placeholder-gray-300"
                  />
                </div>

                {/* File Dropzone */}
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                    <FileText size={14} className="inline mr-1.5 text-geojit-blue" />
                    Financial Document
                  </label>
                  <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                      ${isDragActive
                        ? "border-geojit-blue bg-blue-50 scale-[1.01]"
                        : file
                          ? "border-geojit-green bg-green-50"
                          : "border-geojit-border bg-geojit-bg hover:border-geojit-blue hover:bg-blue-50/30"
                      }`}
                  >
                    <input {...getInputProps()} />
                    {file ? (
                      <div className="flex flex-col items-center gap-2">
                        <CheckCircle size={32} className="text-geojit-green" />
                        <span className="font-semibold text-geojit-green text-sm">{file.name}</span>
                        <span className="text-xs text-gray-400">
                          {(file.size / 1024).toFixed(1)} KB · Click to change
                        </span>
                      </div>
                    ) : isDragActive ? (
                      <div className="flex flex-col items-center gap-2">
                        <Upload size={32} className="text-geojit-blue animate-bounce" />
                        <span className="text-geojit-blue font-semibold text-sm">Drop it here!</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-2">
                        <Upload size={32} className="text-gray-300" />
                        <span className="font-semibold text-gray-600 text-sm">
                          Drag & drop your document
                        </span>
                        <span className="text-xs text-gray-400">
                          PDF, TXT, or CSV · Max 20 MB
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Step Indicator */}
                {loading && (
                  <div className="mb-5">
                    <StepIndicator steps={STEPS} currentStep={currentStep} />
                  </div>
                )}

                {/* Error */}
                {error && (
                  <div className="mb-4 flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
                    <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="w-full bg-geojit-blue text-white font-bold py-3 rounded-xl
                             hover:bg-[#164d82] active:scale-[0.99] transition-all
                             disabled:opacity-60 disabled:cursor-not-allowed
                             flex items-center justify-center gap-2 text-sm"
                >
                  {loading ? (
                    <>
                      <Loader2 size={18} className="spinner" />
                      Analyzing Document...
                    </>
                  ) : (
                    <>
                      <BarChart2 size={18} />
                      Analyze &amp; Generate Report
                      <ChevronRight size={16} />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* ── Results ───────────────────────────────────────── */}
          {result && (
            <div className="fade-in">
              {/* Success header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={22} className="text-geojit-green" />
                    <h2 className="text-xl font-black text-gray-900">
                      {result.financial_data.company_name}
                    </h2>
                    <span className={`
                      px-3 py-0.5 rounded text-sm font-bold
                      ${result.financial_data.rating === "BUY" ? "bg-green-100 text-green-800" :
                        result.financial_data.rating === "HOLD" ? "bg-blue-100 text-blue-800" :
                        "bg-red-100 text-red-800"}
                    `}>
                      {result.financial_data.rating}
                    </span>
                  </div>
                  <p className="text-gray-500 text-sm mt-0.5 ml-7">
                    {result.financial_data.sector}
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 border border-geojit-border text-gray-600 rounded-lg
                               text-sm font-medium hover:bg-gray-50 transition-colors"
                  >
                    New Analysis
                  </button>
                  {result.report_url && (
                    <button
                      onClick={handleDownload}
                      className="px-5 py-2 bg-geojit-blue text-white rounded-lg text-sm
                                 font-bold flex items-center gap-2 hover:bg-[#164d82] transition-colors"
                    >
                      <Download size={16} />
                      Download PDF Report
                    </button>
                  )}
                </div>
              </div>

              {/* Report Summary Cards */}
              <ReportSummary data={result.financial_data} />

              {/* Charts */}
              <FinancialCharts data={result.financial_data} chartUrls={result.chart_urls} apiUrl={API_URL} />

              {/* Metrics Table */}
              <MetricsTable data={result.financial_data} />

              {/* Outlook & Highlights */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-5">

                {/* Highlights */}
                <div className="bg-white rounded-xl border border-geojit-border p-5 shadow-sm">
                  <h3 className="text-sm font-bold text-geojit-blue mb-3 uppercase tracking-wide">
                    Key Highlights
                  </h3>
                  <ul className="space-y-2">
                    {(result.financial_data.highlights || []).map((h: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-geojit-blue font-bold mt-0.5">•</span>
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Outlook */}
                <div className="bg-white rounded-xl border border-geojit-border p-5 shadow-sm">
                  <h3 className="text-sm font-bold text-geojit-blue mb-3 uppercase tracking-wide">
                    Outlook &amp; Valuation
                  </h3>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {result.financial_data.outlook}
                  </p>
                  {result.financial_data.valuation_basis && (
                    <div className="mt-3 p-2.5 bg-geojit-bg rounded-lg border border-geojit-border">
                      <span className="text-xs font-semibold text-gray-500">Valuation Basis: </span>
                      <span className="text-xs text-gray-700">{result.financial_data.valuation_basis}</span>
                    </div>
                  )}
                  {/* Risks */}
                  {result.financial_data.risks?.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-xs font-bold text-geojit-orange mb-2 uppercase tracking-wide">
                        ⚠ Key Risks
                      </h4>
                      <ul className="space-y-1">
                        {result.financial_data.risks.map((r: string, i: number) => (
                          <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                            <span className="text-geojit-orange">›</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>

        {/* ── Footer ───────────────────────────────────────────── */}
        <footer className="mt-16 border-t border-geojit-border bg-white py-5 text-center">
          <div className="text-xs text-gray-400 max-w-3xl mx-auto px-4">
            <strong className="text-geojit-blue">GEOJIT AI Research Analyzer</strong>
            {" "}· This tool is for informational purposes only. AI-extracted data may contain errors.
            Always verify with official company filings. Investment in securities market are subject to market risks.
          </div>
        </footer>
      </div>
    </>
  );
}
