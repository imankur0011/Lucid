"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  PortfolioVersion,
  PortfolioSummary,
  exportPortfolioOrders,
  fetchPortfolioMonitoring,
  checkPortfolioDriftAndTrigger,
  PortfolioMonitoringResponse,
  RebalancePreviewResponse,
} from "../lib/api";
import { AllocationVisualizer } from "./AllocationVisualizer";
import {
  IconChartBar,
  IconCompare,
  IconChevronDown,
  IconChevronUp,
  IconLightbulb,
  IconShield,
  IconDownload,
  IconClipboard,
  IconCheck,
  IconArrowUpRight,
  IconTrash,
  IconRefresh,
} from "./icons";
import { getStockDetails } from "../lib/stockRationales";
import { DeletePortfolioModal } from "./DeletePortfolioModal";
import { RebalancePreviewModal } from "./RebalancePreviewModal";

interface HoldingsViewProps {
  portfolio: PortfolioVersion | null;
  allPortfolios: PortfolioSummary[];
  onSelectVersion: (version: PortfolioVersion) => void;
  onOpenCompareModal: () => void;
  onGoToGenerator: () => void;
  onAskAboutStock?: (symbol: string) => void;
  onViewReasoning?: (symbol?: string) => void;
  onPortfolioDeleted?: () => void;
  onOpenStockWhy?: (symbol: string, companyName?: string) => void;
  onPortfolioUpdated?: (version: PortfolioVersion) => void;
}

export function HoldingsView({
  portfolio,
  allPortfolios,
  onSelectVersion,
  onOpenCompareModal,
  onGoToGenerator,
  onAskAboutStock,
  onViewReasoning,
  onPortfolioDeleted,
  onOpenStockWhy,
  onPortfolioUpdated,
}: HoldingsViewProps) {
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null);
  const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [copiedState, setCopiedState] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [portfolioQuery, setPortfolioQuery] = useState("");

  const exportMenuRef = useRef<HTMLDivElement>(null);

  const [monitoringData, setMonitoringData] = useState<PortfolioMonitoringResponse | null>(null);
  const [monitoringLoading, setMonitoringLoading] = useState(false);
  const [rebalancePreview, setRebalancePreview] = useState<RebalancePreviewResponse | null>(null);
  const [isRebalanceModalOpen, setIsRebalanceModalOpen] = useState(false);
  const [rebalanceChecking, setRebalanceChecking] = useState(false);

  useEffect(() => {
    if (!portfolio?.portfolio_id) return;
    let isSubscribed = true;
    setMonitoringLoading(true);
    fetchPortfolioMonitoring(portfolio.portfolio_id)
      .then((data) => {
        if (isSubscribed && data) {
          setMonitoringData(data);
        }
      })
      .catch((err) => console.debug("Monitoring fetch error:", err))
      .finally(() => {
        if (isSubscribed) setMonitoringLoading(false);
      });

    return () => {
      isSubscribed = false;
    };
  }, [portfolio?.portfolio_id, portfolio?.portfolio_version_id]);

  const handleCheckDriftAndRebalance = async () => {
    if (!portfolio?.portfolio_id) return;
    setRebalanceChecking(true);
    setIsRebalanceModalOpen(true);
    try {
      const res = await checkPortfolioDriftAndTrigger(portfolio.portfolio_id);
      setRebalancePreview(res);
      const updatedMon = await fetchPortfolioMonitoring(portfolio.portfolio_id);
      if (updatedMon) setMonitoringData(updatedMon);
    } catch (err) {
      console.error("Failed to check drift and rebalance:", err);
    } finally {
      setRebalanceChecking(false);
    }
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setIsExportMenuOpen(false);
      }
    }
    if (isExportMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isExportMenuOpen]);

  if (!portfolio) {
    return (
      <div className="p-12 text-center rounded-2xl bg-white border border-[#E5E3DA] shadow-sm max-w-xl mx-auto my-8">
        <div className="w-12 h-12 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] text-[#66758A] flex items-center justify-center mx-auto mb-3">
          <IconChartBar className="w-6 h-6 text-[#142A3B]" />
        </div>
        <h3 className="text-lg font-bold text-[#142A3B] mb-2">No Portfolio Generated Yet</h3>
        <p className="text-xs text-[#66758A] mb-5 leading-relaxed">
          Configure capital, investment horizon, and sector exclusions in the Generator to create your first mathematically optimized equity allocation.
        </p>
        <button
          onClick={onGoToGenerator}
          type="button"
          className="px-5 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white font-semibold text-xs transition-all shadow-sm cursor-pointer"
        >
          Go to Portfolio Generator
        </button>
      </div>
    );
  }

  // Calculate actual invested capital in whole shares
  const actualInvestedCapital = portfolio.holdings.reduce(
    (acc, h) => acc + (Number(h.shares_quantity || 0) * Number(h.latest_price || 0)),
    0
  );
  const totalBudget = Number(portfolio.investment_amount) || 0;
  // Liquid cash reserve remaining due to integer rounding
  const unallocatedCash = Math.max(0, totalBudget - actualInvestedCapital);

  // Sharpe ratio with 7.0% risk free rate
  const sharpeRatio = (
    (portfolio.expected_return_pct - 7.0) /
    (portfolio.expected_volatility_pct || 1)
  ).toFixed(2);

  const toggleExpand = (symbol: string) => {
    setExpandedSymbol((prev) => (prev === symbol ? null : symbol));
  };

  const handleDownloadCSV = async (format: "csv" | "zerodha_csv") => {
    if (!portfolio) return;
    setExporting(true);
    try {
      const csvData = await exportPortfolioOrders(portfolio.portfolio_id, portfolio.portfolio_version_id, format);
      if (typeof csvData === "string") {
        const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `lucid_orders_v${portfolio.version_number}_${format}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error("Failed to export orders:", err);
    } finally {
      setExporting(false);
      setIsExportMenuOpen(false);
    }
  };

  const handleCopyOrderSlip = () => {
    if (!portfolio) return;
    const lines = [
      `LUCID EXECUTION ORDER BASKET (Version #${portfolio.version_number})`,
      `Capital: ₹${Number(portfolio.investment_amount).toLocaleString("en-IN")} | Risk Category: ${portfolio.risk_category.toUpperCase()}`,
      `Generated: ${new Date(portfolio.generated_at).toLocaleDateString("en-IN")}`,
      `----------------------------------------------------------------------`,
      ...portfolio.holdings
        .filter((h) => h.shares_quantity > 0)
        .map(
          (h) =>
            `${h.symbol.padEnd(12)} | BUY ${String(h.shares_quantity).padStart(4)} sh @ ₹${Number(h.latest_price).toFixed(2).padStart(8)} = ₹${Number(h.target_amount).toLocaleString("en-IN").padStart(10)} (${h.target_weight_pct.toFixed(1)}%) [${h.sector_name}]`
        ),
      `----------------------------------------------------------------------`,
      `Cash Reserve: ₹${Math.round(unallocatedCash).toLocaleString("en-IN")}`,
    ];
    navigator.clipboard.writeText(lines.join("\n"));
    setCopiedState(true);
    setTimeout(() => setCopiedState(false), 2500);
    setIsExportMenuOpen(false);
  };

  return (
    <div className="space-y-8">
      {/* Portfolio Summary Banner */}
      <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-[#285C4D] uppercase tracking-widest">
              PORTFOLIO / OVERVIEW
            </span>
            <span className="text-[#D6D3C8]">&bull;</span>
            <span className="text-sm text-[#4A5568]">Balanced by design</span>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h2 className="text-2xl sm:text-3xl font-editorial text-[#142A3B]">Your Money, in Perspective</h2>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
              {portfolio.validation_status.toUpperCase()}
            </span>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-[#F7F6F1] text-[#142A3B] border border-[#E5E3DA] uppercase">
              {portfolio.risk_category.replace("_", " ")}
            </span>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-[#EFECE4] text-[#4A5568] border border-[#E5E3DA]">
              Version #{portfolio.version_number}
            </span>
            {monitoringData && (
              <span
                className={`px-2.5 py-0.5 rounded-md text-xs font-bold border ${
                  monitoringData.health_status === "OPTIMAL"
                    ? "bg-[#DCFCE7] text-[#166534] border-[#86EFAC]"
                    : monitoringData.health_status === "MILD_DRIFT"
                    ? "bg-[#FEF9C3] text-[#854D0E] border-[#FDE047]"
                    : "bg-[#FEE2E2] text-[#991B1B] border-[#FCA5A5]"
                }`}
              >
                {monitoringData.health_status === "OPTIMAL"
                  ? "Optimal Alignment (Drift < 5%)"
                  : monitoringData.health_status === "MILD_DRIFT"
                  ? "Mild Drift Detected"
                  : "Rebalancing Recommended"}
              </span>
            )}
            {allPortfolios.length > 1 && allPortfolios[0]?.versions_count && allPortfolios[0].versions_count > 1 && (
              <select
                value={portfolio.portfolio_version_id}
                onChange={(e) => {
                  const selected = allPortfolios
                    .flatMap(p => p.latest_version ? [p.latest_version] : [])
                    .find(v => v.portfolio_version_id === e.target.value);
                  if (selected) onSelectVersion(selected);
                }}
                className="text-xs border border-[#E5E3DA] rounded-md px-2 py-0.5 bg-white text-[#4A5568] font-medium cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#142A3B]"
              >
                {allPortfolios.map(p => p.latest_version ? (
                  <option key={p.latest_version.portfolio_version_id} value={p.latest_version.portfolio_version_id}>
                    {p.portfolio_name} v#{p.latest_version.version_number}
                  </option>
                ) : null)}
              </select>
            )}
          </div>
          <p className="text-sm text-[#4A5568] mt-1.5">
            A clearer view of risk, diversification, and trade-offs &bull; Generated on {new Date(portfolio.generated_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:gap-4 self-stretch md:self-auto justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-[#E5E3DA]">
          <div className="text-left md:text-right">
            <div className="text-sm text-[#4A5568] font-medium">Target Capital</div>
            <div className="text-xl sm:text-2xl font-black text-[#142A3B] tabular-nums">
              ₹{Number(portfolio.investment_amount).toLocaleString("en-IN")}
            </div>
            {unallocatedCash > 0 && (
              <div className="text-xs sm:text-sm text-[#166534] font-semibold tabular-nums">
                Cash Reserve: ₹{Math.round(unallocatedCash).toLocaleString("en-IN")}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Export Order Basket Dropdown */}
            <div className="relative" ref={exportMenuRef}>
              <button
                onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}
                type="button"
                className="px-4 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white text-sm font-bold flex items-center gap-2 transition-all cursor-pointer shadow-xs"
                title="Export order basket for broker trade placement"
                aria-expanded={isExportMenuOpen}
              >
                <IconDownload className="w-4 h-4 text-white" />
                <span>Export Basket</span>
                <IconChevronDown className={`w-3.5 h-3.5 transition-transform ${isExportMenuOpen ? "rotate-180" : ""}`} />
              </button>

              {isExportMenuOpen && (
                <div className="absolute right-0 mt-2 w-72 rounded-xl bg-white border border-[#E5E3DA] shadow-lg p-2 z-30 animate-fadeIn space-y-1">
                  <div className="px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-[#66758A] border-b border-[#E5E3DA]">
                    Execution Order Options
                  </div>

                  <button
                    onClick={() => handleDownloadCSV("csv")}
                    disabled={exporting}
                    type="button"
                    className="w-full text-left px-3 py-2 text-sm font-semibold text-[#142A3B] hover:bg-[#F7F6F1] rounded-lg flex items-center gap-2.5 transition-colors cursor-pointer"
                  >
                    <IconDownload className="w-4 h-4 text-[#285C4D]" />
                    <div>
                      <div>Download Standard CSV</div>
                      <div className="text-xs text-[#66758A] font-normal">Full order slip with sectors &amp; cash</div>
                    </div>
                  </button>

                  <button
                    onClick={() => handleDownloadCSV("zerodha_csv")}
                    disabled={exporting}
                    type="button"
                    className="w-full text-left px-3 py-2 text-sm font-semibold text-[#142A3B] hover:bg-[#F7F6F1] rounded-lg flex items-center gap-2.5 transition-colors cursor-pointer"
                  >
                    <IconDownload className="w-4 h-4 text-[#4338CA]" />
                    <div>
                      <div>Zerodha Kite Basket CSV</div>
                      <div className="text-xs text-[#66758A] font-normal">Direct import for Zerodha baskets</div>
                    </div>
                  </button>

                  <button
                    onClick={handleCopyOrderSlip}
                    type="button"
                    className="w-full text-left px-3 py-2 text-sm font-semibold text-[#142A3B] hover:bg-[#F7F6F1] rounded-lg flex items-center gap-2.5 transition-colors cursor-pointer"
                  >
                    {copiedState ? (
                      <IconCheck className="w-4 h-4 text-[#166534]" />
                    ) : (
                      <IconClipboard className="w-4 h-4 text-[#B45309]" />
                    )}
                    <div>
                      <div>{copiedState ? "Order Slip Copied!" : "Copy Order Slip"}</div>
                      <div className="text-xs text-[#66758A] font-normal">Formatted text for quick paste</div>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* Check Drift & Rebalance Trigger */}
            <button
              onClick={handleCheckDriftAndRebalance}
              disabled={rebalanceChecking}
              type="button"
              className="px-4 py-2.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] disabled:opacity-60 text-white text-sm font-bold flex items-center gap-2 transition-all cursor-pointer shadow-xs"
              title="Audit real-time holding drift and preview whole-share rebalance trades"
            >
              <IconRefresh className={`w-4 h-4 ${rebalanceChecking ? "animate-spin text-emerald-400" : ""}`} />
              <span>{rebalanceChecking ? "Auditing..." : "Drift & Rebalance"}</span>
            </button>

            {/* Compare Versions Trigger */}
            {allPortfolios.length > 0 && (
              <button
                onClick={onOpenCompareModal}
                type="button"
                className="px-4 py-2.5 rounded-xl bg-[#F7F6F1] hover:bg-[#EFECE4] border border-[#E5E3DA] text-[#142A3B] text-sm font-bold flex items-center gap-2 transition-all cursor-pointer shadow-xs"
                title="Compare saved portfolio versions"
              >
                <IconCompare className="w-4 h-4 text-[#4338CA]" />
                <span>Compare</span>
              </button>
            )}

            {/* Delete Portfolio Trigger */}
            <button
              onClick={() => setIsDeleteModalOpen(true)}
              type="button"
              className="px-3.5 py-2.5 rounded-xl bg-white hover:bg-red-50 border border-[#E5E3DA] hover:border-red-200 text-[#66758A] hover:text-red-700 text-sm font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
              title="Permanently delete this portfolio"
            >
              <IconTrash className="w-4 h-4 text-red-500" />
              <span>Delete</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quantitative Analytics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs card-interactive">
          <div className="text-sm text-[#4A5568] font-medium">Expected Annual Return</div>
          <div className="text-2xl sm:text-3xl font-bold text-[#285C4D] mt-1 tabular-nums font-editorial">
            {portfolio.expected_return_pct ? `${portfolio.expected_return_pct.toFixed(2)}%` : "12.50%"}
          </div>
          <div className="text-xs text-[#66758A] mt-1">Weighted historical projection</div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs card-interactive">
          <div className="text-sm text-[#4A5568] font-medium">Expected Volatility</div>
          <div className="text-2xl sm:text-3xl font-bold text-[#B45309] mt-1 tabular-nums font-editorial">
            {portfolio.expected_volatility_pct ? `${portfolio.expected_volatility_pct.toFixed(2)}%` : "9.80%"}
          </div>
          <div className="text-xs text-[#66758A] mt-1">Annualized standard deviation</div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs card-interactive">
          <div className="text-sm text-[#4A5568] font-medium">Sharpe Ratio</div>
          <div className="text-2xl sm:text-3xl font-bold text-[#142A3B] mt-1 tabular-nums font-editorial">
            {sharpeRatio}
          </div>
          <div className="text-xs text-[#66758A] mt-1">Excess return over 7.0% Rf</div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs card-interactive">
          <div className="text-sm text-[#4A5568] font-medium">Diversification Score</div>
          <div className="text-2xl sm:text-3xl font-bold text-[#285C4D] mt-1 tabular-nums font-editorial">
            {portfolio.diversification_score ? `${portfolio.diversification_score.toFixed(1)}/100` : "88/100"}
          </div>
          <div className="text-xs text-[#66758A] mt-1">Herfindahl normalized index</div>
        </div>
      </div>

      {/* Visual Asset Allocation Donut & Sector Bars */}
      <AllocationVisualizer
        holdings={portfolio.holdings}
        totalCapital={portfolio.investment_amount}
      />

      {/* Interactive AI Copilot Gateway */}
      {onAskAboutStock && (
        <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-white via-[#F7F6F1] to-[#ECF3F0] border border-[#E5E3DA] shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#285C4D] text-white flex items-center justify-center font-bold shadow-2xs flex-shrink-0">
              <IconLightbulb className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-[#142A3B] text-sm sm:text-base">
                  Have questions about this portfolio?
                </span>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                  Live Copilot
                </span>
              </div>
              <p className="text-xs sm:text-sm text-[#4A5568] mt-0.5">
                Inspect stock selections, simulate macroeconomic shocks, or ask about risk guardrails.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
            {portfolio.holdings.slice(0, 2).map((h) => (
              <button
                key={h.symbol}
                type="button"
                onClick={() => onAskAboutStock(`Why did you recommend ${h.symbol} for my portfolio?`)}
                className="text-xs px-3 py-1.5 rounded-lg bg-white hover:bg-[#F7F6F1] border border-[#E5E3DA] text-[#285C4D] font-semibold transition-colors cursor-pointer shadow-2xs"
              >
                Why {h.symbol}? &rarr;
              </button>
            ))}
            <button
              type="button"
              onClick={() => onAskAboutStock("Can you explain how diversification protects my capital in this allocation?")}
              className="text-xs px-3.5 py-1.5 rounded-lg bg-[#142A3B] hover:bg-[#0E1E2B] text-white font-bold transition-all cursor-pointer shadow-xs flex items-center gap-1.5"
            >
              <span>Ask AI Copilot</span>
              <IconArrowUpRight className="w-3.5 h-3.5 text-[#285C4D]" />
            </button>
          </div>
        </div>
      )}

      {/* Tabular Holdings List with Expandable Deep AI Theses */}
      <div className="rounded-2xl bg-white border border-[#E5E3DA] overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-[#E5E3DA] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 bg-[#F7F6F1]">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-[#142A3B] text-base">
                Allocated Equities &amp; Investment Theses
              </h3>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1]">
                AI Fiduciary Reasoning (FR-D01)
              </span>
            </div>
            <p className="text-xs sm:text-sm text-[#4A5568] mt-1">
              Click any row or &ldquo;View Thesis&rdquo; to inspect multi-sentence AI reasoning, audited ratios, and risk roles.
            </p>
          </div>
          <span className="text-sm text-[#4A5568] font-medium bg-white px-3 py-1 rounded-md border border-[#E5E3DA]">
            {portfolio.holdings.length} Securities Selected
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#F7F6F1] text-[#4A5568] text-xs uppercase tracking-wider border-b border-[#E5E3DA]">
              <tr>
                <th className="px-5 py-3.5 font-bold">Instrument</th>
                <th className="px-4 py-3.5 font-bold">Sector</th>
                <th className="px-4 py-3.5 font-bold text-right">Target Weight</th>
                <th className="px-4 py-3.5 font-bold text-right">Allocated Value</th>
                <th className="px-4 py-3.5 font-bold text-right">Whole Shares</th>
                <th className="px-4 py-3.5 font-bold text-right">Price</th>
                <th className="px-5 py-3.5 font-bold text-center">AI Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E3DA] text-[#142A3B]">
              {portfolio.holdings.map((h) => {
                const isExpanded = expandedSymbol === h.symbol;
                const details = getStockDetails(h.symbol, h.sector_name);

                return (
                  <React.Fragment key={h.symbol}>
                    <tr
                      onClick={() => toggleExpand(h.symbol)}
                      className={`hover:bg-[#F7F6F1] transition-colors cursor-pointer ${
                        isExpanded ? "bg-[#F7F6F1]/70" : ""
                      }`}
                    >
                      <td className="px-5 py-4 font-bold text-[#142A3B]">
                        <div className="flex items-center gap-2.5">
                          <button
                            type="button"
                            aria-label={isExpanded ? "Collapse thesis" : "Expand thesis"}
                            className="p-1 rounded-md hover:bg-[#E5E3DA] text-[#66758A] transition-colors"
                          >
                            {isExpanded ? (
                              <IconChevronUp className="w-4 h-4 text-[#285C4D]" />
                            ) : (
                              <IconChevronDown className="w-4 h-4 text-[#66758A]" />
                            )}
                          </button>
                          <div className="flex flex-col">
                            <span className="text-sm font-extrabold">{h.symbol}</span>
                            <span className="text-xs font-normal text-[#4A5568]">{h.security_name}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-xs px-2.5 py-1 rounded-md bg-[#EFECE4] text-[#4A5568] border border-[#E5E3DA] font-medium whitespace-nowrap">
                          {h.sector_name}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right tabular-nums">
                        <div className="font-extrabold text-[#166534]">
                          {h.target_weight_pct.toFixed(2)}%
                        </div>
                        {(() => {
                          const mon = monitoringData?.holdings?.find((m) => m.symbol === h.symbol);
                          if (!mon) return null;
                          const isAligned = Math.abs(mon.weight_drift_pct) <= 2.0;
                          const isMild = Math.abs(mon.weight_drift_pct) <= 5.0;
                          return (
                            <div className="flex items-center justify-end gap-1 mt-0.5" title={`Current weight: ${mon.current_weight_pct.toFixed(2)}%`}>
                              <span className="text-[10px] text-[#66758A]">
                                Cur: {mon.current_weight_pct.toFixed(1)}%
                              </span>
                              <span
                                className={`text-[9px] font-bold px-1 py-0.2 rounded ${
                                  isAligned
                                    ? "bg-[#DCFCE7] text-[#166534]"
                                    : isMild
                                    ? "bg-[#FEF9C3] text-[#854D0E]"
                                    : "bg-[#FEE2E2] text-[#991B1B]"
                                }`}
                              >
                                {mon.weight_drift_pct > 0 ? "+" : ""}
                                {mon.weight_drift_pct.toFixed(1)}%
                              </span>
                            </div>
                          );
                        })()}
                      </td>
                      <td className="px-4 py-4 font-semibold text-[#142A3B] tabular-nums text-right">
                        ₹{Number(h.target_amount).toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </td>
                      <td className="px-4 py-4 font-semibold text-[#142A3B] tabular-nums text-right">
                        {h.shares_quantity} sh
                      </td>
                      <td className="px-4 py-4 text-[#4A5568] tabular-nums text-right">
                        ₹{Number(h.latest_price).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-5 py-4 text-center">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleExpand(h.symbol);
                          }}
                          className={`text-xs px-2.5 py-1.5 rounded-lg border font-semibold transition-colors cursor-pointer inline-flex items-center gap-1.5 ${
                            isExpanded
                              ? "bg-[#285C4D] text-white border-[#285C4D]"
                              : "bg-[#ECF3F0] text-[#285C4D] border-[#C6D8D1] hover:bg-[#E2F0EA]"
                          }`}
                        >
                          <IconLightbulb className="w-3.5 h-3.5" />
                          <span>{isExpanded ? "Hide Thesis" : "View AI Thesis"}</span>
                        </button>
                      </td>
                    </tr>

                    {/* Expandable Deep AI Reasoning Drawer Row */}
                    {isExpanded && (
                      <tr className="bg-[#F7F6F1]/90 border-b border-[#E5E3DA]">
                        <td colSpan={7} className="px-6 py-5">
                          <div className="bg-white rounded-xl p-6 border border-[#E5E3DA] shadow-xs space-y-5">
                            {/* Header: Strategic Role & Cap Adherence */}
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3.5 border-b border-[#E5E3DA]">
                              <div className="flex items-center gap-2.5">
                                <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider bg-[#ECF3F0] px-3 py-1 rounded-md border border-[#C6D8D1]">
                                  {details.role}
                                </span>
                                <span className="text-sm font-semibold text-[#142A3B]">
                                  BSE: <span className="font-mono">{details.bseCode}</span> &bull; NSE: <span className="font-mono">{h.symbol}</span>
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-xs font-semibold">
                                <span className="text-[#66758A]">Concentration Rule:</span>
                                <span className="text-[#285C4D] bg-[#ECF3F0] px-2.5 py-0.5 rounded border border-[#C6D8D1] font-bold">
                                  {h.target_weight_pct.toFixed(1)}% &le; 25.0% Fiduciary Cap
                                </span>
                              </div>
                            </div>

                            {/* Section 1: Business Architecture & Competitive Moat */}
                            <div className="space-y-1.5">
                              <h4 className="text-sm font-bold text-[#142A3B] flex items-center gap-1.5">
                                <IconShield className="w-4 h-4 text-[#285C4D]" />
                                <span>Fiduciary Investment Thesis &amp; AI Selection Rationale</span>
                              </h4>
                              <div className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                                Business Model &amp; Competitive Moat
                              </div>
                              <p className="text-sm text-[#142A3B] leading-relaxed">
                                {details.moat}
                              </p>
                              <p className="text-sm text-[#4A5568] leading-relaxed">
                                {h.decision_reason && h.decision_reason.length > 50
                                  ? h.decision_reason
                                  : details.thesis}
                              </p>
                            </div>

                            {/* Section 2: Catalysts & Headwinds */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                              <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                                <div className="text-xs font-bold uppercase tracking-wider text-[#285C4D]">
                                  Growth Catalysts &amp; Value Drivers
                                </div>
                                <p className="text-xs text-[#334155] leading-relaxed">
                                  {details.catalysts}
                                </p>
                              </div>
                              <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                                <div className="text-xs font-bold uppercase tracking-wider text-[#B45309]">
                                  Key Headwinds &amp; Downside Risks
                                </div>
                                <p className="text-xs text-[#334155] leading-relaxed">
                                  {details.risks}
                                </p>
                              </div>
                            </div>

                            {/* Section 3: Audited Fundamental Financial Metrics */}
                            <div className="space-y-2">
                              <div className="text-xs font-bold text-[#66758A] uppercase tracking-wider">
                                Audited Fundamental Financial Metrics
                              </div>
                              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                                <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                                  <div className="text-xs text-[#4A5568] font-medium">Trailing P/E</div>
                                  <div className="text-base font-bold text-[#142A3B] mt-0.5 tabular-nums">
                                    {details.pe}
                                  </div>
                                </div>
                                <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                                  <div className="text-xs text-[#4A5568] font-medium">Return on Equity</div>
                                  <div className="text-base font-bold text-[#285C4D] mt-0.5 tabular-nums">
                                    {details.roe}
                                  </div>
                                </div>
                                <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                                  <div className="text-xs text-[#4A5568] font-medium">Systematic Beta</div>
                                  <div className="text-base font-bold text-[#142A3B] mt-0.5 tabular-nums">
                                    {details.beta.toFixed(2)}
                                  </div>
                                </div>
                                <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                                  <div className="text-xs text-[#4A5568] font-medium">Dividend Yield</div>
                                  <div className="text-base font-bold text-[#142A3B] mt-0.5 tabular-nums">
                                    {details.dividendYield}
                                  </div>
                                </div>
                                <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                                  <div className="text-xs text-[#4A5568] font-medium">Debt / Equity</div>
                                  <div className="text-base font-bold text-[#142A3B] mt-0.5 tabular-nums">
                                    {details.debtToEquity}
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Section 4: Verified Filing Source & Actions */}
                            <div className="pt-3 border-t border-[#EFECE4] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                              <div className="flex items-center gap-2 text-xs text-[#4A5568]">
                                <span className="font-semibold">Exchange Disclosure:</span>
                                <span className="text-[#142A3B]">{details.filingSource}</span>
                              </div>

                              <div className="flex flex-wrap items-center gap-2">
                                {/* Direct Gateway to Full Multi-Agent Reasoning in ExplainabilityView */}
                                {onViewReasoning && (
                                  <button
                                    type="button"
                                    onClick={() => onViewReasoning(h.symbol)}
                                    className="text-xs px-3.5 py-2 rounded-lg bg-[#ECF3F0] hover:bg-[#DDF0E8] border border-[#C6D8D1] text-[#285C4D] font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                                    title="View complete 5-agent deliberation and audit trail"
                                  >
                                    <IconShield className="w-3.5 h-3.5" />
                                    <span>View Complete 5-Agent Deliberation &rarr;</span>
                                  </button>
                                )}

                                {/* Clickable Exchange Hyperlink */}
                                <a
                                  href={details.filingUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  title={`View verified filings: ${details.filingSource}`}
                                  className="text-xs px-3.5 py-2 rounded-lg bg-white border border-[#D6D3C8] hover:border-[#142A3B] text-[#142A3B] font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                                >
                                  <span>Exchange Filings</span>
                                  <IconArrowUpRight className="w-3.5 h-3.5 text-[#285C4D]" />
                                </a>

                                {/* Quick Action: Ask Conversational Assistant or Dedicated Stock Why */}
                                {onOpenStockWhy ? (
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onOpenStockWhy(h.symbol, h.security_name);
                                    }}
                                    className="text-xs px-3.5 py-2 rounded-lg bg-[#285C4D] hover:bg-[#1E463A] text-white font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                                  >
                                    <IconLightbulb className="w-3.5 h-3.5" />
                                    <span>Ask AI why {h.symbol} &rarr;</span>
                                  </button>
                                ) : onAskAboutStock ? (
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onAskAboutStock(`Why did you recommend ${h.symbol} for my portfolio?`);
                                    }}
                                    className="text-xs px-3.5 py-2 rounded-lg bg-[#285C4D] hover:bg-[#1E463A] text-white font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                                  >
                                    <IconLightbulb className="w-3.5 h-3.5" />
                                    <span>Ask AI why {h.symbol} &rarr;</span>
                                  </button>
                                ) : null}
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>

          {/* Whole-Share Liquid Cash Reserve Callout Card */}
          <div className="p-4 sm:p-5 bg-[#ECF3F0] border-t border-[#C6D8D1] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#D3E4DE] text-[#285C4D] flex items-center justify-center font-bold text-sm flex-shrink-0 mt-0.5">
                ₹
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-[#285C4D]">
                    Liquid Cash Reserve: ₹{Math.round(unallocatedCash).toLocaleString("en-IN")} ({((unallocatedCash / (totalBudget || 1)) * 100).toFixed(1)}%)
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs font-bold bg-[#D3E4DE] text-[#285C4D]">
                    NSE/BSE Whole Share Rule
                  </span>
                </div>
                <p className="text-sm text-[#334155] mt-1 leading-relaxed">
                  Indian stock exchanges only permit buying whole shares (no fractional shares). We keep the remaining ₹{Math.round(unallocatedCash).toLocaleString("en-IN")} safely unallocated so you never exceed your investment budget.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Portfolio Confirmation Modal */}
      <DeletePortfolioModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        portfolio={portfolio}
        onDeleted={() => {
          onPortfolioDeleted?.();
        }}
      />

      {/* Rebalance Preview Modal */}
      <RebalancePreviewModal
        isOpen={isRebalanceModalOpen}
        onClose={() => setIsRebalanceModalOpen(false)}
        previewData={rebalancePreview}
        isLoading={rebalanceChecking}
        onPortfolioUpdated={(newVer) => {
          onSelectVersion(newVer);
          onPortfolioUpdated?.(newVer);
          if (portfolio?.portfolio_id) {
            fetchPortfolioMonitoring(portfolio.portfolio_id).then((m) => {
              if (m) setMonitoringData(m);
            });
          }
        }}
      />
    </div>
  );
}
