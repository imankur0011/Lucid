"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  PortfolioSummary,
  PortfolioComparisonResult,
  comparePortfolioVersions,
  fetchPortfolioVersions,
} from "../lib/api";
import {
  IconCompare,
  IconX,
  IconArrowUpRight,
  IconArrowDownRight,
  IconAlertCircle,
  IconCheck,
  IconShield,
} from "./icons";

interface VersionComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  allPortfolios: PortfolioSummary[];
}

export interface ComparisonOption {
  version_id: string;
  portfolio_id: string;
  portfolio_name: string;
  version_number: number;
  risk_category: string;
  investment_amount: number;
  holdings_count: number;
  label: string;
}

export function VersionComparisonModal({
  isOpen,
  onClose,
  allPortfolios,
}: VersionComparisonModalProps) {
  // Build initial options directly from allPortfolios latest versions
  const initialOptions: ComparisonOption[] = useMemo(() => {
    return allPortfolios.flatMap((p) => {
      if (!p.latest_version) return [];
      const v = p.latest_version;
      const capital = v.investment_amount
        ? Number(v.investment_amount).toLocaleString("en-IN")
        : "2,50,000";
      const holdings = v.holdings?.length ?? 0;
      const risk = (v.risk_category || "moderate").replace("_", " ").toUpperCase();
      return [
        {
          version_id: v.portfolio_version_id,
          portfolio_id: p.portfolio_id,
          portfolio_name: p.portfolio_name || `Portfolio v#${v.version_number}`,
          version_number: v.version_number,
          risk_category: v.risk_category || "moderate",
          investment_amount: Number(v.investment_amount) || 0,
          holdings_count: holdings,
          label: `${p.portfolio_name || "Portfolio"} • v#${v.version_number} (${risk} • ₹${capital} • ${holdings} stocks)`,
        },
      ];
    });
  }, [allPortfolios]);

  const [options, setOptions] = useState<ComparisonOption[]>(initialOptions);
  const [versionAId, setVersionAId] = useState<string>("");
  const [versionBId, setVersionBId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [comparisonResult, setComparisonResult] = useState<PortfolioComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [activeViewMode, setActiveViewMode] = useState<"stocks" | "sectors">("stocks");

  // Keep options in sync when allPortfolios changes
  useEffect(() => {
    setOptions(initialOptions);
  }, [initialOptions]);

  // Fetch all historical versions for each portfolio to uncover past versions (v1, v2, etc.)
  useEffect(() => {
    let isMounted = true;
    async function loadAllVersions() {
      if (!allPortfolios || allPortfolios.length === 0) return;
      try {
        const results = await Promise.all(
          allPortfolios.map(async (p) => {
            try {
              const versions = await fetchPortfolioVersions(p.portfolio_id);
              if (versions && versions.length > 0) {
                return versions.map((v) => {
                  const capital = v.investment_amount
                    ? Number(v.investment_amount).toLocaleString("en-IN")
                    : "2,50,000";
                  const holdings = v.holdings?.length ?? 0;
                  const risk = (v.risk_category || "moderate").replace("_", " ").toUpperCase();
                  return {
                    version_id: v.portfolio_version_id,
                    portfolio_id: p.portfolio_id,
                    portfolio_name: p.portfolio_name || `Portfolio v#${v.version_number}`,
                    version_number: v.version_number,
                    risk_category: v.risk_category || "moderate",
                    investment_amount: Number(v.investment_amount) || 0,
                    holdings_count: holdings,
                    label: `${p.portfolio_name || "Portfolio"} • v#${v.version_number} (${risk} • ₹${capital} • ${holdings} stocks)`,
                  };
                });
              }
            } catch {
              // Ignore failure for individual portfolio version fetch
            }
            return [];
          })
        );

        const flattened = results.flat();
        if (isMounted && flattened.length > 0) {
          const seen = new Set<string>();
          const deduped: ComparisonOption[] = [];
          for (const item of flattened) {
            if (!seen.has(item.version_id)) {
              seen.add(item.version_id);
              deduped.push(item);
            }
          }
          if (deduped.length > 0) {
            setOptions(deduped);
          }
        }
      } catch {
        // Non-blocking fallback
      }
    }

    if (isOpen) {
      loadAllVersions();
    }

    return () => {
      isMounted = false;
    };
  }, [allPortfolios, isOpen]);

  // Initialize defaults: Option 1 vs Option 2 (or Option 1 vs Option 1 if only 1 exists)
  useEffect(() => {
    if (!isOpen || options.length === 0) return;

    if (!versionAId || !options.some((o) => o.version_id === versionAId)) {
      setVersionAId(options[0].version_id);
    }

    if (!versionBId || !options.some((o) => o.version_id === versionBId)) {
      if (options.length > 1) {
        setVersionBId(options[1].version_id);
      } else {
        setVersionBId(options[0].version_id);
      }
    }
  }, [isOpen, options, versionAId, versionBId]);

  // Comparison execution routine
  const executeComparison = useCallback(async (vA: string, vB: string) => {
    if (!vA || !vB) return;

    setLoading(true);
    setError(null);
    try {
      // Find portfolio id if both belong to same portfolio, or null for universal
      const itemA = options.find((o) => o.version_id === vA);
      const itemB = options.find((o) => o.version_id === vB);
      const portId = itemA && itemB && itemA.portfolio_id === itemB.portfolio_id ? itemA.portfolio_id : null;

      const res = await comparePortfolioVersions(portId, vA, vB);
      setComparisonResult(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to compare versions";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [options]);

  // Automatically trigger comparison when selections change
  useEffect(() => {
    if (isOpen && versionAId && versionBId) {
      executeComparison(versionAId, versionBId);
    }
  }, [isOpen, versionAId, versionBId, executeComparison]);

  // Swap sides button
  const handleSwapSides = () => {
    const temp = versionAId;
    setVersionAId(versionBId);
    setVersionBId(temp);
  };

  // Selected option entities
  const selectedA = options.find((o) => o.version_id === versionAId);
  const selectedB = options.find((o) => o.version_id === versionBId);

  // Sector differences computed from holdings
  const sectorDifferences = useMemo(() => {
    if (!comparisonResult) return [];
    const map: Record<string, { sector: string; weightA: number; weightB: number }> = {};
    for (const h of comparisonResult.holdings_comparison) {
      const sec = h.sector_name || "General";
      if (!map[sec]) map[sec] = { sector: sec, weightA: 0, weightB: 0 };
      map[sec].weightA += h.weight_version_a;
      map[sec].weightB += h.weight_version_b;
    }
    return Object.values(map)
      .map((s) => ({
        ...s,
        weightA: Math.round(s.weightA * 100) / 100,
        weightB: Math.round(s.weightB * 100) / 100,
        delta: Math.round((s.weightB - s.weightA) * 100) / 100,
      }))
      .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  }, [comparisonResult]);

  // Filtered holdings for search
  const filteredHoldings = useMemo(() => {
    if (!comparisonResult) return [];
    const q = searchFilter.trim().toLowerCase();
    if (!q) return comparisonResult.holdings_comparison;
    return comparisonResult.holdings_comparison.filter(
      (h) =>
        h.symbol.toLowerCase().includes(q) ||
        h.security_name.toLowerCase().includes(q) ||
        h.sector_name.toLowerCase().includes(q)
    );
  }, [comparisonResult, searchFilter]);

  if (!isOpen) return null;

  const isIdentical = versionAId === versionBId;

  return (
    <div className="fixed inset-0 z-50 bg-[#142A3B]/50 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 overflow-y-auto animate-fadeIn">
      <div className="bg-white border border-[#E5E3DA] rounded-3xl max-w-5xl w-full p-5 sm:p-7 shadow-2xl relative my-6 max-h-[92vh] flex flex-col animate-scaleUp">
        {/* Modal Header */}
        <div className="flex justify-between items-start pb-4 border-b border-[#E5E3DA] shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                Portfolio &amp; Version Comparison
              </span>
              <span className="text-[#94A3B8]">&bull;</span>
              <span className="text-xs text-[#66758A]">Side-by-Side Allocation &amp; Risk Audit</span>
            </div>
            <h2 className="text-xl font-bold text-[#142A3B] flex items-center gap-2">
              <IconCompare className="w-5 h-5 text-[#285C4D]" />
              <span>Compare Portfolios &amp; Versions</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="p-2 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] hover:border-[#D6D3C8] text-[#66758A] hover:text-[#142A3B] transition-colors cursor-pointer"
            aria-label="Close comparison dialog"
          >
            <IconX className="w-5 h-5" />
          </button>
        </div>

        {/* Dropdown Selectors Toolbar (NO raw UUIDs!) */}
        <div className="py-4 border-b border-[#E5E3DA] shrink-0 bg-[#FDFBF7] -mx-5 sm:-mx-7 px-5 sm:px-7">
          <div className="grid grid-cols-1 md:grid-cols-11 gap-3 items-center">
            {/* Baseline Dropdown (Version A) */}
            <div className="md:col-span-5 space-y-1">
              <label
                htmlFor="compare-select-a"
                className="block text-xs font-bold text-[#4A5568] uppercase tracking-wider flex items-center gap-1.5"
              >
                <span className="w-2 h-2 rounded-full bg-[#142A3B]"></span>
                <span>Baseline (Portfolio / Version A)</span>
              </label>
              <select
                id="compare-select-a"
                value={versionAId}
                onChange={(e) => setVersionAId(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-white border border-[#E5E3DA] text-xs font-medium text-[#142A3B] shadow-2xs focus:outline-none focus:border-[#285C4D] focus:ring-1 focus:ring-[#285C4D] cursor-pointer"
              >
                {options.map((opt) => (
                  <option key={`a-${opt.version_id}`} value={opt.version_id}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Quick Swap Button */}
            <div className="md:col-span-1 flex items-center justify-center pt-2 md:pt-4">
              <button
                onClick={handleSwapSides}
                type="button"
                className="p-2 rounded-xl bg-white hover:bg-[#F7F6F1] border border-[#E5E3DA] hover:border-[#285C4D] text-[#142A3B] transition-all cursor-pointer shadow-2xs flex items-center justify-center"
                title="Swap baseline and target comparison"
                aria-label="Swap sides"
              >
                <IconCompare className="w-4 h-4 text-[#285C4D]" />
              </button>
            </div>

            {/* Target Dropdown (Version B) */}
            <div className="md:col-span-5 space-y-1">
              <label
                htmlFor="compare-select-b"
                className="block text-xs font-bold text-[#4A5568] uppercase tracking-wider flex items-center gap-1.5"
              >
                <span className="w-2 h-2 rounded-full bg-[#285C4D]"></span>
                <span>Comparison Target (Portfolio / Version B)</span>
              </label>
              <select
                id="compare-select-b"
                value={versionBId}
                onChange={(e) => setVersionBId(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-white border border-[#E5E3DA] text-xs font-medium text-[#142A3B] shadow-2xs focus:outline-none focus:border-[#285C4D] focus:ring-1 focus:ring-[#285C4D] cursor-pointer"
              >
                {options.map((opt) => (
                  <option key={`b-${opt.version_id}`} value={opt.version_id}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Contextual guidance */}
          {options.length <= 1 ? (
            <div className="mt-3 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
              <IconShield className="w-4 h-4 text-amber-700 shrink-0" />
              <span>
                You currently have 1 portfolio version saved. Build an additional portfolio or rebalance to compare two distinct allocations side-by-side.
              </span>
            </div>
          ) : isIdentical ? (
            <div className="mt-2 text-center text-xs text-[#66758A]">
              Comparing the same portfolio version against itself. Pick a different target from the dropdown above to observe allocation and risk deltas.
            </div>
          ) : null}
        </div>

        {error && (
          <div className="my-3 p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
            <IconAlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto py-4 space-y-5">
          {loading ? (
            <div className="py-16 text-center text-xs text-[#66758A] space-y-2">
              <div className="inline-block w-6 h-6 border-2 border-[#285C4D]/30 border-t-[#285C4D] rounded-full animate-spin"></div>
              <p className="font-semibold text-[#142A3B]">Computing cross-portfolio deltas and holdings...</p>
            </div>
          ) : comparisonResult ? (
            <div className="space-y-5">
              {/* Visual Side-by-Side Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Side A Card */}
                <div className="p-4 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-[#142A3B] uppercase tracking-wider bg-white px-2 py-0.5 rounded border border-[#E5E3DA]">
                      BASELINE (SIDE A)
                    </span>
                    <span className="text-xs text-[#66758A] font-semibold">
                      v#{comparisonResult.version_a.version_number}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#142A3B] truncate">
                      {comparisonResult.version_a.portfolio_name || selectedA?.portfolio_name || "Portfolio A"}
                    </h3>
                    <div className="text-xs text-[#66758A] flex items-center gap-2 mt-0.5">
                      <span className="font-bold text-[#285C4D]">
                        ₹{Number(comparisonResult.version_a.investment_amount).toLocaleString("en-IN")}
                      </span>
                      <span>•</span>
                      <span className="uppercase font-semibold text-[#4A5568]">
                        {(comparisonResult.version_a.risk_category || selectedA?.risk_category || "moderate").replace("_", " ")}
                      </span>
                      <span>•</span>
                      <span>{comparisonResult.version_a.holdings_count ?? selectedA?.holdings_count ?? 0} holdings</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 pt-1 border-t border-[#E5E3DA]/60 text-xs">
                    <div>
                      <span className="text-[#66758A] text-[10px] uppercase font-bold block">Exp Return</span>
                      <span className="font-bold text-[#142A3B]">{comparisonResult.version_a.expected_return_pct?.toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-[#66758A] text-[10px] uppercase font-bold block">Volatility</span>
                      <span className="font-bold text-[#142A3B]">{comparisonResult.version_a.expected_volatility_pct?.toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-[#66758A] text-[10px] uppercase font-bold block">Diversification</span>
                      <span className="font-bold text-[#285C4D]">{comparisonResult.version_a.diversification_score?.toFixed(1)}/100</span>
                    </div>
                  </div>
                </div>

                {/* Side B Card */}
                <div className="p-4 rounded-2xl bg-[#ECF3F0]/60 border border-[#C6D8D1] space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-[#285C4D] uppercase tracking-wider bg-white px-2 py-0.5 rounded border border-[#C6D8D1]">
                      TARGET (SIDE B)
                    </span>
                    <span className="text-xs text-[#285C4D] font-semibold">
                      v#{comparisonResult.version_b.version_number}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#142A3B] truncate">
                      {comparisonResult.version_b.portfolio_name || selectedB?.portfolio_name || "Portfolio B"}
                    </h3>
                    <div className="text-xs text-[#66758A] flex items-center gap-2 mt-0.5">
                      <span className="font-bold text-[#285C4D]">
                        ₹{Number(comparisonResult.version_b.investment_amount).toLocaleString("en-IN")}
                      </span>
                      <span>•</span>
                      <span className="uppercase font-semibold text-[#4A5568]">
                        {(comparisonResult.version_b.risk_category || selectedB?.risk_category || "moderate").replace("_", " ")}
                      </span>
                      <span>•</span>
                      <span>{comparisonResult.version_b.holdings_count ?? selectedB?.holdings_count ?? 0} holdings</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 pt-1 border-t border-[#C6D8D1]/60 text-xs">
                    <div>
                      <span className="text-[#285C4D] text-[10px] uppercase font-bold block">Exp Return</span>
                      <span className="font-bold text-[#142A3B]">{comparisonResult.version_b.expected_return_pct?.toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-[#285C4D] text-[10px] uppercase font-bold block">Volatility</span>
                      <span className="font-bold text-[#142A3B]">{comparisonResult.version_b.expected_volatility_pct?.toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-[#285C4D] text-[10px] uppercase font-bold block">Diversification</span>
                      <span className="font-bold text-[#285C4D]">{comparisonResult.version_b.diversification_score?.toFixed(1)}/100</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Metric Deltas Highlights */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] shadow-2xs">
                  <div className="text-[11px] text-[#66758A] font-bold uppercase tracking-wider">
                    Expected Return Delta
                  </div>
                  <div
                    className={`text-xl font-bold mt-1 tabular-nums flex items-center gap-1 ${
                      comparisonResult.deltas.delta_return_pct > 0
                        ? "text-[#166534]"
                        : comparisonResult.deltas.delta_return_pct < 0
                        ? "text-[#B91C1C]"
                        : "text-[#66758A]"
                    }`}
                  >
                    {comparisonResult.deltas.delta_return_pct > 0 ? (
                      <IconArrowUpRight className="w-4 h-4" />
                    ) : comparisonResult.deltas.delta_return_pct < 0 ? (
                      <IconArrowDownRight className="w-4 h-4" />
                    ) : null}
                    <span>
                      {comparisonResult.deltas.delta_return_pct > 0 ? "+" : ""}
                      {comparisonResult.deltas.delta_return_pct.toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-[11px] text-[#66758A] mt-0.5">
                    {comparisonResult.version_a.expected_return_pct?.toFixed(2)}% &rarr; {comparisonResult.version_b.expected_return_pct?.toFixed(2)}%
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] shadow-2xs">
                  <div className="text-[11px] text-[#66758A] font-bold uppercase tracking-wider">
                    Expected Volatility Delta
                  </div>
                  <div
                    className={`text-xl font-bold mt-1 tabular-nums flex items-center gap-1 ${
                      comparisonResult.deltas.delta_volatility_pct < 0
                        ? "text-[#166534]"
                        : comparisonResult.deltas.delta_volatility_pct > 0
                        ? "text-[#B45309]"
                        : "text-[#66758A]"
                    }`}
                  >
                    <span>
                      {comparisonResult.deltas.delta_volatility_pct > 0 ? "+" : ""}
                      {comparisonResult.deltas.delta_volatility_pct.toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-[11px] text-[#66758A] mt-0.5">
                    {comparisonResult.version_a.expected_volatility_pct?.toFixed(2)}% &rarr; {comparisonResult.version_b.expected_volatility_pct?.toFixed(2)}%
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] shadow-2xs">
                  <div className="text-[11px] text-[#66758A] font-bold uppercase tracking-wider">
                    Diversification Delta
                  </div>
                  <div
                    className={`text-xl font-bold mt-1 tabular-nums flex items-center gap-1 ${
                      comparisonResult.deltas.delta_diversification > 0
                        ? "text-[#285C4D]"
                        : comparisonResult.deltas.delta_diversification < 0
                        ? "text-[#B91C1C]"
                        : "text-[#66758A]"
                    }`}
                  >
                    <span>
                      {comparisonResult.deltas.delta_diversification > 0 ? "+" : ""}
                      {comparisonResult.deltas.delta_diversification.toFixed(1)} pts
                    </span>
                  </div>
                  <div className="text-[11px] text-[#66758A] mt-0.5">
                    {comparisonResult.version_a.diversification_score?.toFixed(1)} &rarr; {comparisonResult.version_b.diversification_score?.toFixed(1)} / 100
                  </div>
                </div>
              </div>

              {/* Comparison Tabs (Stocks vs Sectors) */}
              <div className="rounded-2xl border border-[#E5E3DA] overflow-hidden bg-white shadow-xs">
                <div className="px-4 py-3 bg-[#FDFBF7] border-b border-[#E5E3DA] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setActiveViewMode("stocks")}
                      type="button"
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        activeViewMode === "stocks"
                          ? "bg-[#142A3B] text-white shadow-2xs"
                          : "bg-white text-[#66758A] border border-[#E5E3DA] hover:bg-[#F7F6F1]"
                      }`}
                    >
                      Individual Stocks ({comparisonResult.holdings_comparison.length})
                    </button>
                    <button
                      onClick={() => setActiveViewMode("sectors")}
                      type="button"
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        activeViewMode === "sectors"
                          ? "bg-[#142A3B] text-white shadow-2xs"
                          : "bg-white text-[#66758A] border border-[#E5E3DA] hover:bg-[#F7F6F1]"
                      }`}
                    >
                      Sector Distribution ({sectorDifferences.length})
                    </button>
                  </div>

                  {activeViewMode === "stocks" && (
                    <input
                      type="text"
                      placeholder="Search stock or sector..."
                      value={searchFilter}
                      onChange={(e) => setSearchFilter(e.target.value)}
                      className="w-full sm:w-56 px-3 py-1.5 rounded-lg bg-white border border-[#E5E3DA] text-xs focus:outline-none focus:border-[#285C4D]"
                    />
                  )}
                </div>

                {/* Tab 1: Individual Stocks Table */}
                {activeViewMode === "stocks" && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#F7F6F1] text-[#4A5568] uppercase border-b border-[#E5E3DA] text-[11px] font-bold">
                        <tr>
                          <th className="px-4 py-3">Instrument &amp; Company</th>
                          <th className="px-4 py-3">Sector</th>
                          <th className="px-4 py-3 text-right">Baseline Wt (A)</th>
                          <th className="px-4 py-3 text-right">Target Wt (B)</th>
                          <th className="px-4 py-3 text-right">Weight Delta</th>
                          <th className="px-4 py-3 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E5E3DA]">
                        {filteredHoldings.map((item) => {
                          const isUp = item.weight_delta > 0;
                          const isDown = item.weight_delta < 0;
                          const inA = item.weight_version_a > 0;
                          const inB = item.weight_version_b > 0;

                          return (
                            <tr key={item.symbol} className="hover:bg-[#FDFBF7] transition-colors">
                              <td className="px-4 py-3 font-bold text-[#142A3B]">
                                <div>{item.symbol}</div>
                                <div className="text-[11px] font-normal text-[#66758A] truncate max-w-[200px]">
                                  {item.security_name}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-[#4A5568] font-medium">{item.sector_name}</td>
                              <td className="px-4 py-3 text-right font-medium tabular-nums">
                                {item.weight_version_a > 0 ? `${item.weight_version_a.toFixed(2)}%` : "—"}
                              </td>
                              <td className="px-4 py-3 text-right font-medium tabular-nums">
                                {item.weight_version_b > 0 ? `${item.weight_version_b.toFixed(2)}%` : "—"}
                              </td>
                              <td className="px-4 py-3 text-right font-bold tabular-nums">
                                <span
                                  className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                    isUp
                                      ? "bg-[#F0FDF4] text-[#166534] border border-[#BBF7D0]"
                                      : isDown
                                      ? "bg-[#FEF2F2] text-[#B91C1C] border border-[#FECACA]"
                                      : "text-[#66758A]"
                                  }`}
                                >
                                  {isUp ? "+" : ""}
                                  {item.weight_delta.toFixed(2)}%
                                </span>
                              </td>
                              <td className="px-4 py-3 text-center">
                                {inA && inB ? (
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                                    Both Held
                                  </span>
                                ) : inB ? (
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-50 text-green-700 border border-green-200">
                                    + Added in B
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                                    Removed in B
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Tab 2: Sector Distribution Table */}
                {activeViewMode === "sectors" && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#F7F6F1] text-[#4A5568] uppercase border-b border-[#E5E3DA] text-[11px] font-bold">
                        <tr>
                          <th className="px-4 py-3">Economic Sector</th>
                          <th className="px-4 py-3 text-right">Baseline Wt (A)</th>
                          <th className="px-4 py-3 text-right">Target Wt (B)</th>
                          <th className="px-4 py-3 text-right">Net Sector Shift</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E5E3DA]">
                        {sectorDifferences.map((sec) => {
                          const isUp = sec.delta > 0;
                          const isDown = sec.delta < 0;
                          return (
                            <tr key={sec.sector} className="hover:bg-[#FDFBF7] transition-colors">
                              <td className="px-4 py-3 font-bold text-[#142A3B]">{sec.sector}</td>
                              <td className="px-4 py-3 text-right font-medium tabular-nums">
                                {sec.weightA.toFixed(2)}%
                              </td>
                              <td className="px-4 py-3 text-right font-medium tabular-nums">
                                {sec.weightB.toFixed(2)}%
                              </td>
                              <td className="px-4 py-3 text-right font-bold tabular-nums">
                                <span
                                  className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                    isUp
                                      ? "bg-[#F0FDF4] text-[#166534] border border-[#BBF7D0]"
                                      : isDown
                                      ? "bg-[#FEF2F2] text-[#B91C1C] border border-[#FECACA]"
                                      : "text-[#66758A]"
                                  }`}
                                >
                                  {isUp ? "+" : ""}
                                  {sec.delta.toFixed(2)}%
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-xs text-[#66758A]">
              Choose two portfolios or versions from the dropdowns above to generate comparison metrics.
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="pt-4 border-t border-[#E5E3DA] flex items-center justify-between shrink-0">
          <div className="text-[11px] text-[#66758A]">
            Lucid Risk Advisory: Comparative models reflect mathematical weight deltas and historical factor sensitivities.
          </div>
          <button
            onClick={onClose}
            type="button"
            className="px-5 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-xs font-bold transition-all cursor-pointer shadow-xs"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
}

export default VersionComparisonModal;
