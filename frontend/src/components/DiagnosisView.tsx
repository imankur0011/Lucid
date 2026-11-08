"use client";

import React, { useState, useRef } from "react";
import {
  DiagnosisResult,
  PortfolioImportPreviewResponse,
  ParsedHoldingPreview,
  InvalidRowError,
  downloadCsvTemplate,
  uploadHoldingsCsv,
  parseHoldingsText,
} from "../lib/api";
import {
  IconRefresh,
  IconAlertTriangle,
  IconCheck,
  IconDownload,
  IconSparkles,
  IconTarget,
  IconArrowRight,
  IconSliders,
  IconShield,
  IconX,
} from "./icons";
import { DiagnosisCopilotModal } from "./DiagnosisCopilotModal";

interface ManualRow {
  id: string;
  symbol: string;
  exchange: string;
  quantity: string;
  average_purchase_price: string;
}

interface DiagnosisViewProps {
  holdingsInput: string;
  setHoldingsInput: (input: string) => void;
  diagnosisResult: DiagnosisResult | null;
  diagnosing: boolean;
  onDiagnose: (
    customHoldings?: Array<{ symbol: string; quantity: number; average_purchase_price?: number }>
  ) => void;
  onAskAboutRebalance?: (query: string) => void;
  onResetDiagnosis?: () => void;
  riskCategory?: string;
}

type ImportTab = "table" | "csv" | "paste" | "presets";

export function DiagnosisView({
  holdingsInput,
  setHoldingsInput,
  diagnosisResult,
  diagnosing,
  onDiagnose,
  onAskAboutRebalance,
  onResetDiagnosis,
  riskCategory = "growth",
}: DiagnosisViewProps) {
  const [activeTab, setActiveTab] = useState<ImportTab>("presets");

  // Manual Table State
  const [manualRows, setManualRows] = useState<ManualRow[]>([
    { id: "1", symbol: "RELIANCE", exchange: "NSE", quantity: "40", average_purchase_price: "2500" },
    { id: "2", symbol: "TCS", exchange: "NSE", quantity: "25", average_purchase_price: "3200" },
    { id: "3", symbol: "HDFCBANK", exchange: "NSE", quantity: "60", average_purchase_price: "1650" },
    { id: "4", symbol: "INFY", exchange: "NSE", quantity: "30", average_purchase_price: "1400" },
  ]);

  // CSV Drag and Drop State
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadingCsv, setUploadingCsv] = useState(false);
  const [csvError, setCsvError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Diagnosis AI Copilot Modal State
  const [isCopilotOpen, setIsCopilotOpen] = useState<boolean>(false);
  const [copilotInitialQuery, setCopilotInitialQuery] = useState<string>("");

  // Parsing & Staging State
  const [parsingText, setParsingText] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<PortfolioImportPreviewResponse | null>(null);

  // Handle CSV Template Download
  const handleDownloadTemplate = async () => {
    try {
      const csvText = await downloadCsvTemplate();
      const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "lucid_holdings_template.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      // Fallback client template if backend fetch fails
      const fallbackCsv = "symbol,exchange,quantity,average_buy_price,purchase_date\nRELIANCE,NSE,40,2500.00,2024-01-15\nTCS,NSE,25,3200.00,2024-02-10\nHDFCBANK,NSE,60,1650.00,2024-03-01\nINFY,NSE,30,1400.00,2024-04-12\n";
      const blob = new Blob([fallbackCsv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "lucid_holdings_template.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Handle CSV File Selection / Drop
  const handleCsvFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setCsvError("Please upload a valid .csv spreadsheet file.");
      return;
    }
    setCsvError(null);
    setUploadedFileName(file.name);
    setUploadingCsv(true);
    try {
      const res = await uploadHoldingsCsv(file);
      setPreviewData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to parse CSV file";
      setCsvError(msg);
    } finally {
      setUploadingCsv(false);
    }
  };

  // Manual Row Handlers
  const handleAddManualRow = () => {
    setManualRows([
      ...manualRows,
      { id: Date.now().toString(), symbol: "", exchange: "NSE", quantity: "", average_purchase_price: "" },
    ]);
  };

  const handleRemoveManualRow = (id: string) => {
    if (manualRows.length <= 1) return;
    setManualRows(manualRows.filter((r) => r.id !== id));
  };

  const handleUpdateManualRow = (id: string, field: keyof ManualRow, value: string) => {
    setManualRows(
      manualRows.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  // Parse Manual Rows to Staging Preview
  const handleStageManualRows = async () => {
    setParseError(null);
    const validRows = manualRows.filter((r) => r.symbol.trim() && parseFloat(r.quantity) > 0);
    if (validRows.length === 0) {
      setParseError("Please specify at least one holding with a valid symbol and quantity.");
      return;
    }

    const textPayload = validRows
      .map((r) => `${r.symbol.trim().toUpperCase()}, ${r.exchange}, ${r.quantity}${r.average_purchase_price ? `, ${r.average_purchase_price}` : ""}`)
      .join("\n");

    setParsingText(true);
    try {
      const res = await parseHoldingsText(textPayload, "manual");
      setPreviewData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to validate manual holdings";
      setParseError(msg);
    } finally {
      setParsingText(false);
    }
  };

  // Parse Freeform Text to Staging Preview
  const handleStageText = async () => {
    setParseError(null);
    if (!holdingsInput.trim()) {
      setParseError("Please enter your stock holdings text.");
      return;
    }
    setParsingText(true);
    try {
      const res = await parseHoldingsText(holdingsInput, "copy_paste");
      setPreviewData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to parse holdings text";
      setParseError(msg);
    } finally {
      setParsingText(false);
    }
  };

  // Load Preset
  const handleLoadPreset = async (preset: "balanced" | "tech" | "banking") => {
    let presetText = "";
    if (preset === "tech") {
      presetText = "TCS: 50\nINFY: 60\nWIPRO: 80\nHCLTECH: 40\nTECHM: 30";
    } else if (preset === "banking") {
      presetText = "HDFCBANK: 80\nICICIBANK: 70\nSBIN: 90\nKOTAKBANK: 40";
    } else {
      presetText = "RELIANCE: 40\nTCS: 25\nHDFCBANK: 60\nINFY: 30";
    }
    setHoldingsInput(presetText);
    setParsingText(true);
    setParseError(null);
    try {
      const res = await parseHoldingsText(presetText, "copy_paste");
      setPreviewData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load preset holdings";
      setParseError(msg);
    } finally {
      setParsingText(false);
    }
  };

  // Run Diagnosis on Staged Holdings
  const handleCommitDiagnosis = () => {
    if (!previewData || previewData.valid_holdings.length === 0) return;
    const holdingsPayload = previewData.valid_holdings.map((h) => ({
      symbol: h.symbol,
      quantity: h.quantity,
      average_purchase_price: h.average_purchase_price || undefined,
    }));
    onDiagnose(holdingsPayload);
  };

  return (
    <div className="space-y-8">
      {/* 1. Header Panel */}
      <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                PORTFOLIO HEALTH &amp; INTEGER REBALANCING
              </span>
              <span className="text-[#94A3B8]">&bull;</span>
              <span className="text-xs text-[#66758A]">NSE / BSE Fiduciary Engine</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#142A3B] flex items-center gap-2">
              <IconRefresh className="w-6 h-6 text-[#285C4D]" />
              <span>Portfolio Diagnosis &amp; Rebalancing Preview</span>
            </h1>
            <p className="text-xs sm:text-sm text-[#66758A] mt-1.5 leading-relaxed max-w-3xl">
              Inspect your current equity portfolio against Lucid diversification policies (≤25% single-stock ceiling, ≤40% sector cap, aligned with SEBI suitability norms).
              Lucid generates whole-share Buy / Sell / Hold recommendations to protect and compound your capital without fractional share cash drag.
            </p>
          </div>

          <button
            type="button"
            onClick={handleDownloadTemplate}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] hover:border-[#285C4D] text-[#142A3B] text-xs font-semibold transition-all cursor-pointer shadow-xs shrink-0"
          >
            <IconDownload className="w-3.5 h-3.5 text-[#285C4D]" />
            <span>Download CSV Template</span>
          </button>
        </div>
      </div>

      {/* 2. Input Methods & Staging Step */}
      {!diagnosisResult && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-[#E5E3DA] p-6 shadow-xs">
            {/* Input Method Navigation Tabs */}
            <div className="flex flex-wrap items-center gap-2 border-b border-[#E5E3DA] pb-4 mb-6">
              <span className="text-xs font-bold text-[#66758A] uppercase tracking-wider mr-2">
                Choose Import Method:
              </span>
              <button
                type="button"
                onClick={() => setActiveTab("presets")}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "presets"
                    ? "bg-[#142A3B] text-white shadow-xs"
                    : "bg-[#F7F6F1] text-[#4A5568] hover:text-[#142A3B] border border-[#E5E3DA]"
                }`}
              >
                <IconSparkles className="w-3.5 h-3.5" />
                <span>1-Click Sample Presets</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("table")}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "table"
                    ? "bg-[#142A3B] text-white shadow-xs"
                    : "bg-[#F7F6F1] text-[#4A5568] hover:text-[#142A3B] border border-[#E5E3DA]"
                }`}
              >
                <IconSliders className="w-3.5 h-3.5" />
                <span>Table-Based Manual Entry</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("csv")}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "csv"
                    ? "bg-[#142A3B] text-white shadow-xs"
                    : "bg-[#F7F6F1] text-[#4A5568] hover:text-[#142A3B] border border-[#E5E3DA]"
                }`}
              >
                <IconDownload className="w-3.5 h-3.5" />
                <span>Upload Broker CSV</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("paste")}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "paste"
                    ? "bg-[#142A3B] text-white shadow-xs"
                    : "bg-[#F7F6F1] text-[#4A5568] hover:text-[#142A3B] border border-[#E5E3DA]"
                }`}
              >
                <IconTarget className="w-3.5 h-3.5" />
                <span>Copy &amp; Paste Text</span>
              </button>
            </div>

            {/* TAB 1: 1-Click Sample Presets */}
            {activeTab === "presets" && (
              <div className="space-y-4">
                <div className="text-xs text-[#66758A]">
                  Select a pre-built portfolio to immediately simulate diagnosis and integer rebalancing across Indian equities:
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    type="button"
                    onClick={() => handleLoadPreset("balanced")}
                    className="p-4 rounded-xl border border-[#E5E3DA] bg-[#F7F6F1] hover:border-[#285C4D] hover:bg-white text-left transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-[#142A3B] group-hover:text-[#285C4D]">
                        Balanced Bluechip Core
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">
                        Diverse
                      </span>
                    </div>
                    <p className="text-xs text-[#66758A] mb-2">
                      40 RELIANCE, 25 TCS, 60 HDFCBANK, 30 INFY across energy, IT, and banking.
                    </p>
                    <span className="text-[11px] font-semibold text-[#285C4D] flex items-center gap-1">
                      Load &amp; Stage Preset <IconArrowRight className="w-3 h-3" />
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleLoadPreset("tech")}
                    className="p-4 rounded-xl border border-[#E5E3DA] bg-[#F7F6F1] hover:border-[#285C4D] hover:bg-white text-left transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-[#142A3B] group-hover:text-[#285C4D]">
                        Concentrated IT Heavy
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">
                        High Drift
                      </span>
                    </div>
                    <p className="text-xs text-[#66758A] mb-2">
                      50 TCS, 60 INFY, 80 WIPRO, 40 HCLTECH, 30 TECHM with severe sector overweight.
                    </p>
                    <span className="text-[11px] font-semibold text-[#285C4D] flex items-center gap-1">
                      Load &amp; Stage Preset <IconArrowRight className="w-3 h-3" />
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleLoadPreset("banking")}
                    className="p-4 rounded-xl border border-[#E5E3DA] bg-[#F7F6F1] hover:border-[#285C4D] hover:bg-white text-left transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-[#142A3B] group-hover:text-[#285C4D]">
                        Banking &amp; Financials Heavy
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold">
                        Cyclical
                      </span>
                    </div>
                    <p className="text-xs text-[#66758A] mb-2">
                      80 HDFCBANK, 70 ICICIBANK, 90 SBIN, 40 KOTAKBANK across private and PSU lenders.
                    </p>
                    <span className="text-[11px] font-semibold text-[#285C4D] flex items-center gap-1">
                      Load &amp; Stage Preset <IconArrowRight className="w-3 h-3" />
                    </span>
                  </button>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-[#E5E3DA]">
                  <span className="text-xs text-[#66758A]">
                    Ready to inspect concentration risks and integer whole-share rebalance?
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      if (previewData && previewData.valid_holdings.length > 0) {
                        handleCommitDiagnosis();
                      } else {
                        onDiagnose([
                          { symbol: "RELIANCE", quantity: 40, average_purchase_price: 2500 },
                          { symbol: "TCS", quantity: 25, average_purchase_price: 3200 },
                          { symbol: "HDFCBANK", quantity: 60, average_purchase_price: 1650 },
                          { symbol: "INFY", quantity: 30, average_purchase_price: 1400 },
                        ]);
                      }
                    }}
                    disabled={diagnosing}
                    className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center gap-2"
                  >
                    <IconRefresh className="w-4 h-4 text-emerald-400" />
                    <span>Diagnose &amp; Preview Rebalance</span>
                  </button>
                </div>
              </div>
            )}

            {/* TAB 2: Table-Based Manual Entry */}
            {activeTab === "table" && (
              <div className="space-y-4">
                <div className="text-xs text-[#66758A]">
                  Enter stock symbols, whole share quantities, and optional purchase prices to track unrealized gains:
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm">
                    <thead>
                      <tr className="border-b border-[#E5E3DA] text-[#66758A] font-semibold uppercase text-[11px]">
                        <th className="pb-2 pl-2">#</th>
                        <th className="pb-2">Stock Symbol</th>
                        <th className="pb-2">Exchange</th>
                        <th className="pb-2">Shares Quantity</th>
                        <th className="pb-2">Avg Buy Price (₹ optional)</th>
                        <th className="pb-2 pr-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E3DA]">
                      {manualRows.map((row, idx) => (
                        <tr key={row.id}>
                          <td className="py-2.5 pl-2 text-[#94A3B8] font-mono">{idx + 1}</td>
                          <td className="py-2.5 pr-2">
                            <input
                              type="text"
                              value={row.symbol}
                              onChange={(e) => handleUpdateManualRow(row.id, "symbol", e.target.value.toUpperCase())}
                              placeholder="e.g. RELIANCE"
                              className="w-full px-3 py-1.5 rounded-lg border border-[#E5E3DA] bg-[#F7F6F1] focus:bg-white text-[#142A3B] font-bold text-xs uppercase"
                            />
                          </td>
                          <td className="py-2.5 pr-2">
                            <select
                              value={row.exchange}
                              onChange={(e) => handleUpdateManualRow(row.id, "exchange", e.target.value)}
                              className="px-2.5 py-1.5 rounded-lg border border-[#E5E3DA] bg-[#F7F6F1] text-xs font-semibold text-[#142A3B]"
                            >
                              <option value="NSE">NSE</option>
                              <option value="BSE">BSE</option>
                            </select>
                          </td>
                          <td className="py-2.5 pr-2">
                            <input
                              type="number"
                              min="1"
                              step="1"
                              value={row.quantity}
                              onChange={(e) => handleUpdateManualRow(row.id, "quantity", e.target.value)}
                              placeholder="e.g. 50"
                              className="w-full px-3 py-1.5 rounded-lg border border-[#E5E3DA] bg-[#F7F6F1] focus:bg-white text-[#142A3B] font-semibold text-xs tabular-nums"
                            />
                          </td>
                          <td className="py-2.5 pr-2">
                            <input
                              type="number"
                              min="0"
                              step="0.05"
                              value={row.average_purchase_price}
                              onChange={(e) => handleUpdateManualRow(row.id, "average_purchase_price", e.target.value)}
                              placeholder="e.g. 2450.00"
                              className="w-full px-3 py-1.5 rounded-lg border border-[#E5E3DA] bg-[#F7F6F1] focus:bg-white text-[#142A3B] text-xs tabular-nums"
                            />
                          </td>
                          <td className="py-2.5 pr-2 text-right">
                            <button
                              type="button"
                              onClick={() => handleRemoveManualRow(row.id)}
                              disabled={manualRows.length <= 1}
                              className="text-xs text-[#94A3B8] hover:text-rose-600 disabled:opacity-30 p-1"
                              title="Remove row"
                            >
                              <IconX className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={handleAddManualRow}
                    className="text-xs font-semibold text-[#285C4D] hover:underline cursor-pointer"
                  >
                    + Add Another Stock Row
                  </button>

                  <button
                    type="button"
                    onClick={handleStageManualRows}
                    disabled={parsingText}
                    className="px-4 py-2 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-bold transition-all shadow-xs disabled:opacity-60 cursor-pointer flex items-center gap-1.5"
                  >
                    {parsingText ? (
                      <>
                        <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Validating Universe...</span>
                      </>
                    ) : (
                      <>
                        <IconCheck className="w-3.5 h-3.5" />
                        <span>Validate &amp; Stage Portfolio</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* TAB 3: CSV File Upload */}
            {activeTab === "csv" && (
              <div className="space-y-4">
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragActive(true);
                  }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragActive(false);
                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                      handleCsvFile(e.dataTransfer.files[0]);
                    }
                  }}
                  onClick={() => fileInputRef.current?.click()}
                  className={`p-8 border-2 border-dashed rounded-2xl text-center cursor-pointer transition-all ${
                    dragActive
                      ? "border-[#285C4D] bg-[#ECF3F0]"
                      : "border-[#D6D3C8] bg-[#F7F6F1] hover:border-[#285C4D] hover:bg-white"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleCsvFile(e.target.files[0]);
                      }
                    }}
                  />
                  <div className="w-12 h-12 rounded-2xl bg-white border border-[#E5E3DA] flex items-center justify-center mx-auto mb-3 shadow-xs">
                    <IconDownload className="w-6 h-6 text-[#285C4D]" />
                  </div>
                  <h3 className="text-sm font-bold text-[#142A3B] mb-1">
                    {uploadingCsv ? "Parsing and Validating CSV..." : "Drag and drop your broker holdings CSV here"}
                  </h3>
                  <p className="text-xs text-[#66758A] max-w-sm mx-auto mb-3">
                    Compatible with Zerodha Console, Groww, Upstox holdings exports, or our standard CSV template.
                  </p>
                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-[#E5E3DA] text-xs font-semibold text-[#142A3B] shadow-xs">
                    Browse File from Computer
                  </div>
                </div>

                {uploadedFileName && (
                  <div className="text-xs text-[#142A3B] bg-[#ECF3F0] p-2.5 rounded-xl border border-[#C6D8D1] flex items-center justify-between">
                    <span>Uploaded: <strong>{uploadedFileName}</strong></span>
                    <button
                      type="button"
                      onClick={() => {
                        setUploadedFileName(null);
                        setPreviewData(null);
                      }}
                      className="text-xs text-[#66758A] hover:text-rose-600 font-semibold"
                    >
                      Clear
                    </button>
                  </div>
                )}

                {csvError && (
                  <div className="text-xs text-rose-700 bg-rose-50 p-3 rounded-xl border border-rose-200 flex items-center gap-2">
                    <IconAlertTriangle className="w-4 h-4 shrink-0" />
                    <span>{csvError}</span>
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: Copy & Paste Text */}
            {activeTab === "paste" && (
              <div className="space-y-4">
                <div className="text-xs text-[#66758A]">
                  Paste stock lines from your broker or spreadsheet. Supported formats:
                  <span className="font-mono bg-[#F7F6F1] px-1.5 py-0.5 rounded ml-1 border border-[#E5E3DA]">SYMBOL: QTY</span>,
                  <span className="font-mono bg-[#F7F6F1] px-1.5 py-0.5 rounded ml-1 border border-[#E5E3DA]">SYMBOL, QTY, BUY_PRICE</span>, or tab-delimited columns.
                </div>

                <textarea
                  rows={6}
                  value={holdingsInput}
                  onChange={(e) => setHoldingsInput(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-[#142A3B] font-mono text-xs sm:text-sm focus:bg-white focus:outline-none focus:border-[#285C4D] focus:ring-1 focus:ring-[#285C4D] transition-all"
                  placeholder="RELIANCE: 40&#10;TCS: 25&#10;HDFCBANK: 60&#10;INFY: 30"
                />

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleStageText}
                    disabled={parsingText || !holdingsInput.trim()}
                    className="px-4 py-2 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-bold transition-all shadow-xs disabled:opacity-60 cursor-pointer flex items-center gap-1.5"
                  >
                    {parsingText ? (
                      <>
                        <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Validating Listings...</span>
                      </>
                    ) : (
                      <>
                        <IconCheck className="w-3.5 h-3.5" />
                        <span>Parse &amp; Validate Holdings</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {parseError && (
              <div className="text-xs text-rose-700 bg-rose-50 p-3 rounded-xl border border-rose-200 mt-4 flex items-center gap-2">
                <IconAlertTriangle className="w-4 h-4 shrink-0" />
                <span>{parseError}</span>
              </div>
            )}
          </div>

          {/* Staging & Confirmation Table */}
          {previewData && (
            <div className="bg-white rounded-2xl border border-[#E5E3DA] p-6 shadow-xs space-y-6">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-[#E5E3DA] pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                      Step 1 of 2: Recognized Holdings Staging
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
                      {previewData.valid_count} Securities Verified
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-[#142A3B] mt-0.5">
                    Review Recognized Equities Before Optimization
                  </h3>
                </div>

                <div className="text-right">
                  <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                    Total Estimated Portfolio Value
                  </div>
                  <div className="text-xl font-bold text-[#142A3B] tabular-nums">
                    ₹{previewData.total_estimated_value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                  </div>
                </div>
              </div>

              {/* Invalid Rows Warning If Any */}
              {previewData.invalid_rows.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-2">
                  <div className="font-bold flex items-center gap-1.5">
                    <IconAlertTriangle className="w-4 h-4 text-amber-700" />
                    <span>Unrecognized Rows ({previewData.invalid_rows.length}):</span>
                  </div>
                  <div className="divide-y divide-amber-200">
                    {previewData.invalid_rows.map((inv, idx) => (
                      <div key={idx} className="py-1">
                        Line {inv.row_number}: <strong>{inv.raw_symbol}</strong> — {inv.error}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Valid Holdings Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead className="bg-[#F7F6F1] text-[#66758A] uppercase text-[11px] font-bold border-b border-[#E5E3DA]">
                    <tr>
                      <th className="py-3 px-4">Symbol</th>
                      <th className="py-3 px-4">Company Name</th>
                      <th className="py-3 px-4">Sector</th>
                      <th className="py-3 px-4 text-right">Shares</th>
                      <th className="py-3 px-4 text-right">Market Price</th>
                      <th className="py-3 px-4 text-right">Market Value</th>
                      <th className="py-3 px-4 text-right">Avg Buy Price</th>
                      <th className="py-3 px-4 text-right">Unrealized P&amp;L</th>
                      <th className="py-3 px-4 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E3DA]">
                    {previewData.valid_holdings.map((h: ParsedHoldingPreview) => (
                      <tr key={h.symbol} className="hover:bg-[#F7F6F1]/50">
                        <td className="py-3 px-4 font-bold text-[#142A3B]">{h.symbol}</td>
                        <td className="py-3 px-4 text-[#4A5568]">{h.security_name}</td>
                        <td className="py-3 px-4 text-[#66758A]">{h.sector_name}</td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-[#142A3B]">{h.quantity}</td>
                        <td className="py-3 px-4 text-right font-mono text-[#4A5568]">
                          ₹{h.latest_market_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-[#142A3B]">
                          ₹{h.current_market_value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-[#66758A]">
                          {h.average_purchase_price ? `₹${h.average_purchase_price.toLocaleString("en-IN")}` : "—"}
                        </td>
                        <td className="py-3 px-4 text-right font-mono">
                          {h.unrealized_pnl !== null && h.unrealized_pnl !== undefined ? (
                            <span className={h.unrealized_pnl >= 0 ? "text-emerald-700 font-bold" : "text-rose-700 font-bold"}>
                              {h.unrealized_pnl >= 0 ? "+" : ""}₹{h.unrealized_pnl.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                              {h.unrealized_pnl_pct !== null && h.unrealized_pnl_pct !== undefined ? ` (${h.unrealized_pnl_pct > 0 ? "+" : ""}${h.unrealized_pnl_pct}%)` : ""}
                            </span>
                          ) : (
                            <span className="text-[#94A3B8]">—</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 inline-flex items-center gap-1">
                            <IconCheck className="w-3 h-3 text-emerald-700" />
                            <span>Verified {h.exchange}</span>
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Confirmation CTA */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#E5E3DA]">
                <div className="text-xs text-[#66758A]">
                  Target Optimization Framework: <strong>{riskCategory.toUpperCase()}</strong> risk profile with <strong>≤25% single-stock ceiling</strong>.
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <button
                    type="button"
                    onClick={() => setPreviewData(null)}
                    className="px-4 py-2.5 rounded-xl border border-[#E5E3DA] hover:bg-[#F7F6F1] text-xs font-semibold text-[#4A5568] transition-all cursor-pointer"
                  >
                    Edit Holdings
                  </button>

                  <button
                    type="button"
                    onClick={handleCommitDiagnosis}
                    disabled={diagnosing || previewData.valid_holdings.length === 0}
                    className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center gap-2 disabled:opacity-60"
                  >
                    {diagnosing ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Optimizing Fiduciary Rebalance...</span>
                      </>
                    ) : (
                      <>
                        <IconRefresh className="w-4 h-4 text-emerald-300" />
                        <span>Run Fiduciary Diagnosis &amp; Preview Rebalance</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3. The 5 Plain-English Rebalance Questions & Results */}
      {diagnosisResult && (
        <div className="space-y-8">
          {/* Header Action Bar */}
          <div className="bg-[#142A3B] text-white p-5 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-widest">
                  PORTFOLIO AUDIT COMPLETE
                </span>
                <span className="text-white/40">&bull;</span>
                <span className="text-xs text-white/80">{diagnosisResult.portfolio_name}</span>
              </div>
              <h2 className="text-xl font-bold">
                Fiduciary Diagnosis &amp; Whole-Share Rebalancing Plan
              </h2>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                type="button"
                onClick={() => {
                  setCopilotInitialQuery(
                    `Explain the rebalancing trades proposed for ${diagnosisResult.portfolio_name}: why were specific stocks trimmed or added, and how does this protect my capital?`
                  );
                  setIsCopilotOpen(true);
                }}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5"
              >
                <IconSparkles className="w-3.5 h-3.5 text-emerald-300" />
                <span>Ask AI Copilot to Explain</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setPreviewData(null);
                  if (onResetDiagnosis) {
                    onResetDiagnosis();
                  }
                  if (typeof window !== "undefined") {
                    window.scrollTo({ top: 80, behavior: "smooth" });
                  }
                }}
                className="px-4 py-2 rounded-xl bg-white text-[#142A3B] text-xs font-bold hover:bg-[#F7F6F1] transition-all cursor-pointer shadow-xs"
              >
                Diagnose Another Portfolio
              </button>
            </div>
          </div>

          {/* Question 1: What does my portfolio look like today? */}
          <div className="bg-white rounded-2xl border border-[#E5E3DA] p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-[#142A3B] text-white text-xs font-bold flex items-center justify-center">
                1
              </span>
              <h3 className="text-base font-bold text-[#142A3B]">
                What does my portfolio look like today?
              </h3>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                  Total Market Valuation
                </div>
                <div className="text-xl font-bold text-[#142A3B] mt-1 tabular-nums font-mono">
                  ₹{Number(diagnosisResult.total_market_value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                  Holdings Count
                </div>
                <div className="text-xl font-bold text-[#142A3B] mt-1 tabular-nums font-mono">
                  {diagnosisResult.current_holdings ? diagnosisResult.current_holdings.length : diagnosisResult.suggestions.length} Equities
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                  Baseline Sharpe Ratio
                </div>
                <div className="text-xl font-bold text-[#285C4D] mt-1 tabular-nums font-mono">
                  {diagnosisResult.current_metrics?.sharpe_ratio || "0.44"}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                  Diversification Score
                </div>
                <div className="text-xl font-bold text-[#142A3B] mt-1 tabular-nums font-mono">
                  {diagnosisResult.current_metrics?.diversification_score || "88.0"}/100
                </div>
              </div>
            </div>

            {/* Existing Holdings Breakdown */}
            {diagnosisResult.current_holdings && diagnosisResult.current_holdings.length > 0 && (
              <div className="overflow-x-auto pt-2">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F7F6F1] text-[#66758A] uppercase font-bold border-b border-[#E5E3DA]">
                    <tr>
                      <th className="py-2.5 px-3">Holding</th>
                      <th className="py-2.5 px-3">Sector</th>
                      <th className="py-2.5 px-3 text-right">Shares</th>
                      <th className="py-2.5 px-3 text-right">Current Price</th>
                      <th className="py-2.5 px-3 text-right">Current Value</th>
                      <th className="py-2.5 px-3 text-right">Current Weight</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E3DA]">
                    {diagnosisResult.current_holdings.map((ch) => (
                      <tr key={ch.symbol}>
                        <td className="py-2.5 px-3 font-bold text-[#142A3B]">
                          {ch.symbol} <span className="text-[#66758A] font-normal">({ch.security_name})</span>
                        </td>
                        <td className="py-2.5 px-3 text-[#66758A]">{ch.sector_name}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-semibold">{ch.quantity} sh</td>
                        <td className="py-2.5 px-3 text-right font-mono text-[#4A5568]">
                          ₹{Number(ch.latest_price).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-[#142A3B]">
                          ₹{Number(ch.current_value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold">
                          <span className={ch.weight_pct > 25.0 ? "text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200" : "text-[#142A3B]"}>
                            {ch.weight_pct.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Question 2: What problems, imbalances, or risks have been identified? */}
          <div className="bg-white rounded-2xl border border-[#E5E3DA] p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-[#142A3B] text-white text-xs font-bold flex items-center justify-center">
                2
              </span>
              <h3 className="text-base font-bold text-[#142A3B]">
                What problems, imbalances, or risks have been identified?
              </h3>
            </div>

            {diagnosisResult.warnings.length > 0 ? (
              <div className="space-y-3">
                {diagnosisResult.warnings.map((w, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs sm:text-sm flex items-start gap-3"
                  >
                    <IconAlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-amber-950">
                        {w.includes("single-stock") ? "Single-Stock Concentration Policy Breach" : "High Sector Cluster Risk"}
                      </div>
                      <p className="mt-0.5 opacity-90 leading-relaxed">{w}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs sm:text-sm flex items-center gap-3">
                <IconCheck className="w-5 h-5 text-emerald-700 shrink-0" />
                <div>
                  <strong>All Lucid Risk Policy Concentration Guardrails Satisfied.</strong>
                  <p className="text-xs opacity-90 mt-0.5">
                    No individual stock exceeds the 25.0% single-stock safety ceiling and no economic sector breaches 40.0%.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Question 3 & 4: What changes does Lucid suggest, and how many shares to buy, sell, or retain? */}
          <div className="bg-white rounded-2xl border border-[#E5E3DA] p-6 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#142A3B] text-white text-xs font-bold flex items-center justify-center">
                  3 &amp; 4
                </span>
                <div>
                  <h3 className="text-base font-bold text-[#142A3B]">
                    Suggested Rebalancing Actions (Integer Shares)
                  </h3>
                  <p className="text-xs text-[#66758A] mt-0.5">
                    What changes does Lucid suggest, and how much money / shares to trade? Proposed trades strictly execute in whole-share integer quantities.
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-flex items-center gap-1.5 ${
                    diagnosisResult.rebalance_status === "no_trades_required"
                      ? "bg-blue-50 text-blue-800 border border-blue-200"
                      : "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  }`}
                >
                  {diagnosisResult.rebalance_status === "no_trades_required" ? (
                    <>
                      <IconCheck className="w-3.5 h-3.5" />
                      <span>No Trades Required</span>
                    </>
                  ) : (
                    `Rebalance Proposed (${diagnosisResult.trades_required_count || diagnosisResult.suggestions.filter(s => s.action !== "hold").length} Trades)`
                  )}
                </span>
              </div>
            </div>

            {/* Execution Metrics Ribbon */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-[#F7F6F1] p-4 rounded-xl border border-[#E5E3DA]">
              <div>
                <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                  Portfolio Turnover
                </div>
                <div className="text-base font-bold text-[#142A3B] mt-0.5 tabular-nums">
                  {diagnosisResult.rebalance_turnover_pct}%
                </div>
              </div>

              <div>
                <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                  Unallocated Cash:
                </div>
                <div className="text-base font-bold text-[#285C4D] mt-0.5 tabular-nums font-mono">
                  ₹{Number(diagnosisResult.unallocated_cash).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                </div>
                <div className="text-[10px] text-[#66758A] mt-0.5">
                  Preserved in cash for whole-share safety
                </div>
              </div>

              <div>
                <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                  Target Sharpe Contribution
                </div>
                <div className="text-base font-bold text-[#142A3B] mt-0.5 tabular-nums">
                  {diagnosisResult.target_metrics?.sharpe_ratio || "0.48"} (+{(Number(diagnosisResult.target_metrics?.sharpe_ratio || 0.48) - Number(diagnosisResult.current_metrics?.sharpe_ratio || 0.44)).toFixed(2)})
                </div>
              </div>
            </div>

            {/* Rebalance Comparison Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead className="bg-[#F7F6F1] text-[#66758A] uppercase text-[11px] font-bold border-b border-[#E5E3DA]">
                  <tr>
                    <th className="py-3 px-4">Stock</th>
                    <th className="py-3 px-4 text-center">Action</th>
                    <th className="py-3 px-4 text-right">Current Qty</th>
                    <th className="py-3 px-4 text-right">Shares to Trade</th>
                    <th className="py-3 px-4 text-right">Target Qty</th>
                    <th className="py-3 px-4 text-right">Value Delta (₹)</th>
                    <th className="py-3 px-4 text-right">Weight Shift</th>
                    <th className="py-3 px-4">Optimization Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E3DA]">
                  {diagnosisResult.suggestions.map((s) => {
                    const isBuy = s.action === "buy";
                    const isSell = s.action === "sell";
                    const isHold = s.action === "hold";
                    const curW = s.current_weight_pct !== undefined ? s.current_weight_pct : 0;
                    const tgtW = s.target_weight_pct !== undefined ? s.target_weight_pct : 0;

                    return (
                      <tr key={s.symbol} className="hover:bg-[#F7F6F1]/50 transition-colors">
                        <td className="py-3 px-4 font-bold text-[#142A3B]">
                          {s.symbol}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase inline-block ${
                              isBuy
                                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                : isSell
                                ? "bg-rose-50 text-rose-800 border border-rose-200"
                                : "bg-slate-100 text-slate-700 border border-slate-300"
                            }`}
                          >
                            {s.action}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-[#66758A]">
                          {s.current_quantity} sh
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold">
                          <span
                            className={
                              isBuy
                                ? "text-emerald-700"
                                : isSell
                                ? "text-rose-700"
                                : "text-[#66758A]"
                            }
                          >
                            {s.quantity_change > 0 ? `+${s.quantity_change}` : s.quantity_change} sh
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-[#142A3B]">
                          {s.target_quantity} sh
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold">
                          <span className={isBuy ? "text-emerald-700" : isSell ? "text-rose-700" : "text-[#66758A]"}>
                            {s.change_value > 0 ? "+" : ""}₹{Math.abs(Number(s.change_value)).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-xs">
                          <span className="text-[#66758A]">{curW.toFixed(1)}%</span>
                          <span className="text-[#94A3B8] mx-1">&rarr;</span>
                          <strong className="text-[#142A3B]">{tgtW.toFixed(1)}%</strong>
                        </td>
                        <td className="py-3 px-4 text-xs text-[#4A5568] max-w-xs leading-relaxed">
                          <div>{s.explanation}</div>
                          <button
                            type="button"
                            onClick={() => {
                              setCopilotInitialQuery(
                                isSell
                                  ? `Why are you trimming my ${s.symbol} holdings?`
                                  : isBuy
                                  ? `Why should I add ${s.symbol} to my portfolio?`
                                  : `Why is ${s.symbol} held without change?`
                              );
                              setIsCopilotOpen(true);
                            }}
                            className="mt-1 text-[11px] font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1 cursor-pointer transition-colors"
                          >
                            <IconSparkles className="w-3 h-3 text-emerald-600" />
                            <span>Ask Copilot why</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Question 5: Why are these changes suggested and what are their limitations? */}
          <div className="bg-white rounded-2xl border border-[#E5E3DA] p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-[#142A3B] text-white text-xs font-bold flex items-center justify-center">
                5
              </span>
              <h3 className="text-base font-bold text-[#142A3B]">
                Why are these changes suggested, and what are their limitations?
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                  <IconShield className="w-4 h-4" />
                  <span>Mathematical Guardrails &amp; Fiduciary Purpose</span>
                </div>
                <p className="text-xs text-[#4A5568] leading-relaxed">
                  Trades are derived using <strong>SLSQP quadratic optimization</strong> with strictly bounded constraints.
                  Overweight holdings are trimmed to respect the <strong>25.0% single-stock ceiling</strong>, while proceeds are reallocated
                  into quality compounders to improve Sharpe ratio and balance sector diversification.
                </p>
                <div className="text-[11px] text-[#66758A] font-semibold">
                  • 100% whole-share integer quantities prevent fractional execution failure.
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-[#B45309] uppercase tracking-wider">
                  <IconAlertTriangle className="w-4 h-4" />
                  <span>Non-Custodial Fiduciary Disclosures</span>
                </div>
                <p className="text-xs text-[#4A5568] leading-relaxed">
                  Lucid is a registered non-custodial advisory and intelligence engine. <strong>We do not execute broker trades on your behalf.</strong>
                  You retain complete ownership and control to execute these orders in your Demat account (Zerodha, Groww, Upstox, etc.).
                </p>
                <div className="text-[11px] text-[#66758A] font-semibold">
                  • Brokerage commissions, STT, and capital gains taxes are excluded from raw previews.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Diagnosis AI Copilot Explanation & Interactive Conversation Modal */}
      {isCopilotOpen && diagnosisResult && (
        <DiagnosisCopilotModal
          isOpen={isCopilotOpen}
          onClose={() => setIsCopilotOpen(false)}
          existingPortfolioId={diagnosisResult.existing_portfolio_id || diagnosisResult.portfolio_diagnosis_id}
          portfolioName={diagnosisResult.portfolio_name}
          initialQuery={copilotInitialQuery}
        />
      )}
    </div>
  );
}
