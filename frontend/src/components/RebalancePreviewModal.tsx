"use client";

import React, { useState } from "react";
import {
  RebalancePreviewResponse,
  RebalanceTradeItem,
  PortfolioVersion,
  applyPortfolioRebalance,
} from "../lib/api";
import {
  IconCheck,
  IconAlertTriangle,
  IconX,
  IconClipboard,
  IconShield,
  IconRefresh,
  IconLayers,
  IconScale,
  IconInfo,
  IconTrendingDown,
  IconTrendingUp,
} from "./icons";

interface RebalancePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  previewData: RebalancePreviewResponse | null;
  isLoading?: boolean;
  onPortfolioUpdated?: (newVersion: PortfolioVersion) => void;
}

export function RebalancePreviewModal({
  isOpen,
  onClose,
  previewData,
  isLoading = false,
  onPortfolioUpdated,
}: RebalancePreviewModalProps) {
  const [activeTab, setActiveTab] = useState<"trades" | "preview">("trades");
  const [tradeFilter, setTradeFilter] = useState<"ALL" | "SELL" | "BUY" | "HOLD">("ALL");
  const [copied, setCopied] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [appliedVersion, setAppliedVersion] = useState<PortfolioVersion | null>(null);
  const [applySuccessMsg, setApplySuccessMsg] = useState<string | null>(null);
  const [applyErrorMsg, setApplyErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (!previewData) return;
    const lines = [
      `LUCID REBALANCING PLAN - ${previewData.portfolio_name || "Portfolio"}`,
      `Generated: ${new Date().toLocaleDateString("en-IN")}`,
      `Status: ${previewData.trigger_status}`,
      `Turnover: ₹${Math.round(previewData.turnover_amount).toLocaleString("en-IN")} (${previewData.turnover_pct.toFixed(1)}%)`,
      `Post-Rebalance Cash: ₹${Math.round(previewData.post_rebalance_cash).toLocaleString("en-IN")}`,
      `----------------------------------------------------------------------`,
      ...previewData.trades.map(
        (t) =>
          `${t.action.padEnd(4)} | ${t.symbol.padEnd(10)} | ${
            t.trade_quantity > 0 ? "+" : ""
          }${t.trade_quantity} sh @ ₹${(t.latest_price || t.reference_price).toFixed(2)} | Val: ₹${Math.round(
            t.trade_value
          ).toLocaleString("en-IN")} | ${t.rationale}`
      ),
      `----------------------------------------------------------------------`,
      `Non-custodial fiduciary advice under SEBI guidelines. Lucid does not place broker orders automatically.`,
    ];
    navigator.clipboard.writeText(lines.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleApply = async () => {
    if (!previewData || !previewData.portfolio_id) return;
    setIsApplying(true);
    setApplyErrorMsg(null);
    try {
      const updatedVersion = await applyPortfolioRebalance(previewData.portfolio_id);
      setAppliedVersion(updatedVersion);
      setApplySuccessMsg(
        `Portfolio successfully updated to Version #${updatedVersion.version_number}! All holdings, integer share counts, and cash reserves are now re-aligned.`
      );
      if (onPortfolioUpdated) {
        onPortfolioUpdated(updatedVersion);
      }
      // Switch to preview tab so user sees the newly aligned portfolio
      setActiveTab("preview");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to apply rebalance";
      setApplyErrorMsg(msg);
    } finally {
      setIsApplying(false);
    }
  };

  const trades = previewData?.trades || [];
  const sellTrades = trades.filter((t) => t.action === "SELL");
  const buyTrades = trades.filter((t) => t.action === "BUY");
  const holdTrades = trades.filter((t) => t.action === "HOLD");

  const filteredTrades =
    tradeFilter === "ALL"
      ? trades
      : tradeFilter === "SELL"
      ? sellTrades
      : tradeFilter === "BUY"
      ? buyTrades
      : holdTrades;

  const totalInvested =
    previewData?.total_post_rebalance_invested ??
    trades.reduce(
      (acc, t) => acc + (t.target_quantity || 0) * (t.latest_price || t.reference_price || 0),
      0
    );

  const txCosts = previewData?.transaction_costs;
  const sectorSummary = previewData?.post_rebalance_sectors || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-4xl w-full p-6 sm:p-8 max-h-[92vh] overflow-y-auto border border-[#E5E3DA] shadow-2xl relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          type="button"
          className="absolute top-6 right-6 p-2 text-[#66758A] hover:text-[#142A3B] rounded-full hover:bg-[#F7F6F1] transition-colors cursor-pointer"
          aria-label="Close modal"
        >
          <IconX className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-[#285C4D]/10 border border-[#285C4D]/20 flex items-center justify-center text-[#285C4D]">
            <IconShield className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold tracking-widest text-[#285C4D] uppercase">
              PORTFOLIO DRIFT &amp; WHOLE-SHARE REBALANCING
            </span>
            <h2 className="text-xl font-bold text-[#142A3B]">
              {previewData?.portfolio_name || "Portfolio"} Audit &amp; Rebalance
            </h2>
          </div>
        </div>

        {/* Tab Navigation Switcher */}
        <div className="flex border-b border-[#E5E3DA] mb-5 gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("trades")}
            className={`flex items-center gap-2 pb-3 px-3 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "trades"
                ? "border-[#285C4D] text-[#285C4D]"
                : "border-transparent text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            <IconLayers className="w-4 h-4" />
            <span>Execution Trades &amp; Why</span>
            <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-[#F7F6F1] text-[#142A3B] font-extrabold border border-[#E5E3DA]">
              {previewData?.trades_count || 0} Orders
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("preview")}
            className={`flex items-center gap-2 pb-3 px-3 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "preview"
                ? "border-[#285C4D] text-[#285C4D]"
                : "border-transparent text-[#66758A] hover:text-[#142A3B]"
            }`}
          >
            <IconScale className="w-4 h-4" />
            <span>Updated Portfolio Preview</span>
            <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-[#E8F5E9] text-[#285C4D] font-extrabold border border-[#C8E6C9]">
              {trades.length} Holdings
            </span>
          </button>
        </div>

        {isLoading ? (
          <div className="py-16 text-center">
            <div className="w-10 h-10 border-4 border-[#285C4D] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm font-semibold text-[#142A3B]">Evaluating Real-Time Price Drift &amp; Whole Shares...</p>
            <p className="text-xs text-[#66758A] mt-1">Inspecting 5% single-stock drift and 10% sector thresholds</p>
          </div>
        ) : !previewData ? (
          <div className="py-12 text-center text-[#66758A]">
            <p>No rebalance preview data available.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Success Banner if Rebalance was Applied */}
            {applySuccessMsg && (
              <div className="p-4 rounded-2xl bg-[#ECFDF5] border border-[#6EE7B7] text-[#065F46] flex items-start gap-3 animate-fadeIn">
                <div className="w-6 h-6 rounded-full bg-[#10B981] text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <IconCheck className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold">Portfolio Updated Successfully!</h4>
                  <p className="text-xs mt-0.5 leading-relaxed">{applySuccessMsg}</p>
                </div>
              </div>
            )}

            {/* Error Banner if Rebalance Failed */}
            {applyErrorMsg && (
              <div className="p-4 rounded-2xl bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] flex items-start gap-3">
                <IconAlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-[#DC2626]" />
                <div>
                  <h4 className="text-sm font-bold">Failed to Update Portfolio</h4>
                  <p className="text-xs mt-0.5">{applyErrorMsg}</p>
                </div>
              </div>
            )}

            {/* Status Summary Banner */}
            <div
              className={`p-4 rounded-2xl border ${
                previewData.trigger_status === "REBALANCE_TRIGGERED"
                  ? "bg-[#FEF2F2] border-[#FCA5A5] text-[#991B1B]"
                  : "bg-[#F0FDF4] border-[#86EFAC] text-[#166534]"
              } flex items-start gap-3`}
            >
              {previewData.trigger_status === "REBALANCE_TRIGGERED" ? (
                <IconAlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-[#DC2626]" />
              ) : (
                <IconCheck className="w-5 h-5 flex-shrink-0 mt-0.5 text-[#16A34A]" />
              )}
              <div>
                <h4 className="text-sm font-bold">
                  {previewData.trigger_status === "REBALANCE_TRIGGERED"
                    ? "Rebalancing Threshold Breached"
                    : "Portfolio Within Drift Tolerance"}
                </h4>
                <p className="text-xs mt-0.5 opacity-90">
                  {previewData.triggers_breached.length > 0
                    ? previewData.triggers_breached.join("; ")
                    : "All holdings and sector exposures are aligned with target allocation boundaries."}
                </p>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[10px] uppercase font-bold text-[#66758A]">Total Valuation</div>
                <div className="text-base font-extrabold text-[#142A3B] mt-0.5">
                  ₹{Math.round(previewData.total_portfolio_value).toLocaleString("en-IN")}
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[10px] uppercase font-bold text-[#66758A]">Turnover Amount</div>
                <div className="text-base font-extrabold text-[#142A3B] mt-0.5">
                  ₹{Math.round(previewData.turnover_amount).toLocaleString("en-IN")}
                  <span className="text-xs font-normal text-[#66758A] ml-1">
                    ({previewData.turnover_pct.toFixed(1)}%)
                  </span>
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[10px] uppercase font-bold text-[#66758A]">Trades Proposed</div>
                <div className="text-base font-extrabold text-[#142A3B] mt-0.5">
                  {previewData.trades_count} Orders
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                <div className="text-[10px] uppercase font-bold text-[#66758A]">Post-Rebalance Cash</div>
                <div className="text-base font-extrabold text-[#285C4D] mt-0.5">
                  ₹{Math.round(previewData.post_rebalance_cash).toLocaleString("en-IN")}
                </div>
              </div>
            </div>

            {/* TAB 1: EXECUTION TRADES & WHY */}
            {activeTab === "trades" && (
              <div className="space-y-4 animate-fadeIn">
                {/* Filter Pills */}
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-[#66758A] mr-1">Filter:</span>
                    <button
                      type="button"
                      onClick={() => setTradeFilter("ALL")}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                        tradeFilter === "ALL"
                          ? "bg-[#142A3B] text-white"
                          : "bg-[#F7F6F1] text-[#66758A] hover:bg-[#E5E3DA]"
                      }`}
                    >
                      All ({trades.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setTradeFilter("SELL")}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                        tradeFilter === "SELL"
                          ? "bg-[#DC2626] text-white"
                          : "bg-[#FEE2E2] text-[#991B1B] hover:bg-[#FCA5A5]/40"
                      }`}
                    >
                      Sells ({sellTrades.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setTradeFilter("BUY")}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                        tradeFilter === "BUY"
                          ? "bg-[#16A34A] text-white"
                          : "bg-[#DCFCE7] text-[#166534] hover:bg-[#86EFAC]/40"
                      }`}
                    >
                      Buys ({buyTrades.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setTradeFilter("HOLD")}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                        tradeFilter === "HOLD"
                          ? "bg-[#475569] text-white"
                          : "bg-[#F1F5F9] text-[#475569] hover:bg-[#E2E8F0]"
                      }`}
                    >
                      Holds ({holdTrades.length})
                    </button>
                  </div>
                  <span className="text-[11px] text-[#66758A]">
                    Integer lots only (Zero fractional shares)
                  </span>
                </div>

                {/* Proposed Trade Plan Table */}
                <div className="border border-[#E5E3DA] rounded-2xl overflow-hidden">
                  <div className="px-5 py-3 bg-[#F7F6F1] border-b border-[#E5E3DA] flex items-center justify-between">
                    <span className="text-xs font-bold text-[#142A3B] uppercase tracking-wider">
                      Whole-Share Execution Orders &amp; Rationales
                    </span>
                    <span className="text-[11px] font-medium text-[#285C4D]">
                      Showing {filteredTrades.length} of {trades.length} securities
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-white text-[#66758A] uppercase border-b border-[#E5E3DA]">
                        <tr>
                          <th className="px-4 py-3 font-bold">Action</th>
                          <th className="px-4 py-3 font-bold">Security</th>
                          <th className="px-4 py-3 font-bold">Sector</th>
                          <th className="px-4 py-3 font-bold text-right">Shares Shift</th>
                          <th className="px-4 py-3 font-bold text-right">Price</th>
                          <th className="px-4 py-3 font-bold text-right">Trade Value</th>
                          <th className="px-4 py-3 font-bold">Why Rebalance (Rationale)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E5E3DA]">
                        {filteredTrades.map((t, idx) => {
                          const price = t.latest_price || t.reference_price;
                          return (
                            <tr
                              key={t.security_id || t.symbol || `trade-${idx}`}
                              className="hover:bg-[#F7F6F1]/50 transition-colors"
                            >
                              <td className="px-4 py-3">
                                <span
                                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-extrabold ${
                                    t.action === "BUY"
                                      ? "bg-[#DCFCE7] text-[#166534] border border-[#86EFAC]"
                                      : t.action === "SELL"
                                      ? "bg-[#FEE2E2] text-[#991B1B] border border-[#FCA5A5]"
                                      : "bg-[#F1F5F9] text-[#475569] border border-[#CBD5E1]"
                                  }`}
                                >
                                  {t.action === "BUY" && <IconTrendingUp className="w-3 h-3" />}
                                  {t.action === "SELL" && <IconTrendingDown className="w-3 h-3" />}
                                  {t.action}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-bold text-[#142A3B]">
                                <div>{t.symbol}</div>
                                <div className="text-[10px] font-normal text-[#66758A]">
                                  {t.company_name}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-[#4A5568] whitespace-nowrap">{t.sector}</td>
                              <td className="px-4 py-3 text-right font-bold tabular-nums">
                                <div
                                  className={
                                    t.trade_quantity > 0
                                      ? "text-[#166534]"
                                      : t.trade_quantity < 0
                                      ? "text-[#991B1B]"
                                      : "text-[#66758A]"
                                  }
                                >
                                  {t.trade_quantity > 0
                                    ? `+${t.trade_quantity}`
                                    : t.trade_quantity}{" "}
                                  sh
                                </div>
                                <div className="text-[10px] font-normal text-[#66758A]">
                                  {t.current_quantity} → {t.target_quantity} sh
                                </div>
                              </td>
                              <td className="px-4 py-3 text-right text-[#4A5568] tabular-nums">
                                ₹{price.toFixed(2)}
                              </td>
                              <td className="px-4 py-3 text-right font-bold text-[#142A3B] tabular-nums">
                                ₹{Math.round(t.trade_value).toLocaleString("en-IN")}
                              </td>
                              <td className="px-4 py-3 text-[#334155] text-[11px] max-w-sm leading-relaxed">
                                {t.rationale}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Transaction Costs & Cash Impact Card */}
                {txCosts && (
                  <div className="p-4 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA]">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <IconInfo className="w-4 h-4 text-[#285C4D]" />
                        <span className="text-xs font-bold text-[#142A3B] uppercase tracking-wider">
                          Statutory Indian Equity Transaction Costs Breakdown
                        </span>
                      </div>
                      <span className="text-[11px] font-bold text-[#285C4D]">
                        Total Costs: ₹{(txCosts.total_estimated_costs ?? 0).toFixed(2)}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-center text-xs">
                      <div className="p-2 rounded-lg bg-white border border-[#E5E3DA]">
                        <div className="text-[10px] text-[#66758A]">STT / CTT</div>
                        <div className="font-bold text-[#142A3B] mt-0.5">
                          ₹{(txCosts.stt ?? txCosts.stt_ctt ?? 0).toFixed(2)}
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-white border border-[#E5E3DA]">
                        <div className="text-[10px] text-[#66758A]">Brokerage</div>
                        <div className="font-bold text-[#142A3B] mt-0.5">
                          ₹{(txCosts.brokerage ?? 0).toFixed(2)}
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-white border border-[#E5E3DA]">
                        <div className="text-[10px] text-[#66758A]">Exch Turnover</div>
                        <div className="font-bold text-[#142A3B] mt-0.5">
                          ₹{(txCosts.exchange_charges ?? txCosts.exchange_turnover_charges ?? 0).toFixed(2)}
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-white border border-[#E5E3DA]">
                        <div className="text-[10px] text-[#66758A]">SEBI Fees</div>
                        <div className="font-bold text-[#142A3B] mt-0.5">
                          ₹{(txCosts.sebi_charges ?? txCosts.sebi_turnover_fees ?? 0).toFixed(2)}
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-white border border-[#E5E3DA]">
                        <div className="text-[10px] text-[#66758A]">Stamp Duty</div>
                        <div className="font-bold text-[#142A3B] mt-0.5">
                          ₹{(txCosts.stamp_duty ?? 0).toFixed(2)}
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-white border border-[#E5E3DA]">
                        <div className="text-[10px] text-[#66758A]">GST (18%)</div>
                        <div className="font-bold text-[#142A3B] mt-0.5">
                          ₹{(txCosts.gst ?? 0).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: UPDATED PORTFOLIO PREVIEW */}
            {activeTab === "preview" && (
              <div className="space-y-4 animate-fadeIn">
                {/* Post-Rebalance Summary Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-[#E8F5E9]/50 border border-[#C8E6C9]">
                    <div className="text-[10px] uppercase font-bold text-[#285C4D]">
                      Post-Rebalance Valuation
                    </div>
                    <div className="text-base font-extrabold text-[#142A3B] mt-0.5">
                      ₹{Math.round(previewData.total_portfolio_value).toLocaleString("en-IN")}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                    <div className="text-[10px] uppercase font-bold text-[#66758A]">Equities Invested</div>
                    <div className="text-base font-extrabold text-[#142A3B] mt-0.5">
                      ₹{Math.round(totalInvested).toLocaleString("en-IN")}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                    <div className="text-[10px] uppercase font-bold text-[#66758A]">
                      Liquid Cash Reserve
                    </div>
                    <div className="text-base font-extrabold text-[#285C4D] mt-0.5">
                      ₹{Math.round(previewData.post_rebalance_cash).toLocaleString("en-IN")}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                    <div className="text-[10px] uppercase font-bold text-[#66758A]">Allocation Status</div>
                    <div className="text-base font-extrabold text-[#16A34A] mt-0.5 flex items-center gap-1">
                      <IconCheck className="w-4 h-4" /> Aligned
                    </div>
                  </div>
                </div>

                {/* Updated Holdings Table */}
                <div className="border border-[#E5E3DA] rounded-2xl overflow-hidden">
                  <div className="px-5 py-3 bg-[#F7F6F1] border-b border-[#E5E3DA] flex items-center justify-between">
                    <span className="text-xs font-bold text-[#142A3B] uppercase tracking-wider">
                      Resulting Portfolio Holdings (After Rebalance)
                    </span>
                    <span className="text-[11px] font-medium text-[#285C4D]">
                      {trades.filter((t) => t.target_quantity > 0).length} Active Holdings
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-white text-[#66758A] uppercase border-b border-[#E5E3DA]">
                        <tr>
                          <th className="px-4 py-3 font-bold">Security</th>
                          <th className="px-4 py-3 font-bold">Sector</th>
                          <th className="px-4 py-3 font-bold text-right">Shares (Q)</th>
                          <th className="px-4 py-3 font-bold text-right">Price</th>
                          <th className="px-4 py-3 font-bold text-right">Holding Value</th>
                          <th className="px-4 py-3 font-bold text-right">New Weight</th>
                          <th className="px-4 py-3 font-bold text-right">Target Weight</th>
                          <th className="px-4 py-3 font-bold text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E5E3DA]">
                        {trades.map((t, idx) => {
                          const price = t.latest_price || t.reference_price;
                          const postValue = t.target_quantity * price;
                          const postWeight =
                            t.post_rebalance_weight_pct ??
                            (previewData.total_portfolio_value > 0
                              ? (postValue / previewData.total_portfolio_value) * 100
                              : 0);

                          return (
                            <tr
                              key={t.security_id || t.symbol || `post-${idx}`}
                              className="hover:bg-[#F7F6F1]/50 transition-colors"
                            >
                              <td className="px-4 py-3 font-bold text-[#142A3B]">
                                <div>{t.symbol}</div>
                                <div className="text-[10px] font-normal text-[#66758A]">
                                  {t.company_name}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-[#4A5568] whitespace-nowrap">{t.sector}</td>
                              <td className="px-4 py-3 text-right font-bold text-[#142A3B] tabular-nums">
                                {t.target_quantity} sh
                              </td>
                              <td className="px-4 py-3 text-right text-[#4A5568] tabular-nums">
                                ₹{price.toFixed(2)}
                              </td>
                              <td className="px-4 py-3 text-right font-bold text-[#142A3B] tabular-nums">
                                ₹{Math.round(postValue).toLocaleString("en-IN")}
                              </td>
                              <td className="px-4 py-3 text-right font-bold text-[#285C4D] tabular-nums">
                                {postWeight.toFixed(1)}%
                              </td>
                              <td className="px-4 py-3 text-right text-[#66758A] tabular-nums">
                                {t.target_weight_pct.toFixed(1)}%
                              </td>
                              <td className="px-4 py-3 text-center">
                                {t.action === "SELL" ? (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A]">
                                    Trimmed ({t.trade_quantity} sh)
                                  </span>
                                ) : t.action === "BUY" ? (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-[#DCFCE7] text-[#166534] border border-[#86EFAC]">
                                    Added (+{t.trade_quantity} sh)
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#F1F5F9] text-[#475569] border border-[#CBD5E1]">
                                    Aligned
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Post-Rebalance Sector Breakdown vs House 40% Limit */}
                {sectorSummary.length > 0 && (
                  <div className="p-4 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA]">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <IconScale className="w-4 h-4 text-[#285C4D]" />
                        <span className="text-xs font-bold text-[#142A3B] uppercase tracking-wider">
                          Post-Rebalance Sector Exposure vs. 40.0% House Ceiling
                        </span>
                      </div>
                      <span className="text-[11px] font-bold text-[#16A34A] flex items-center gap-1">
                        <IconCheck className="w-3.5 h-3.5" /> All Sectors Compliant
                      </span>
                    </div>

                    <div className="space-y-2.5">
                      {sectorSummary.map((sec, sIdx) => (
                        <div key={sec.sector || `sec-${sIdx}`} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-[#142A3B]">{sec.sector}</span>
                            <span className="tabular-nums font-bold text-[#285C4D]">
                              {sec.post_rebalance_weight_pct.toFixed(1)}%{" "}
                              <span className="text-[10px] font-normal text-[#66758A]">
                                / {sec.policy_cap_pct.toFixed(0)}% Cap
                              </span>
                            </span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-[#E5E3DA] overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                sec.within_limit ? "bg-[#285C4D]" : "bg-[#DC2626]"
                              }`}
                              style={{
                                width: `${Math.min(
                                  100,
                                  (sec.post_rebalance_weight_pct / sec.policy_cap_pct) * 100
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* SEBI Fiduciary Disclaimer */}
            <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-[11px] text-[#66758A] leading-relaxed">
              <strong>SEBI Fiduciary &amp; Execution Disclosure:</strong> Lucid operates strictly as an intelligent investment research and mathematical advisory interface under SEBI (Investment Advisers) Regulations, 2013 standards. Lucid does not have direct broker connectivity or discretionary trading power. Clicking &ldquo;Apply Rebalance &amp; Update Portfolio&rdquo; records the rebalanced allocations, quantities, and cash balance in Lucid. Please execute the recommended trade orders through your registered broker.
            </div>

            {/* Actions Bar */}
            <div className="flex items-center justify-between pt-2 flex-wrap gap-3">
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-[#E5E3DA] hover:bg-[#F7F6F1] text-[#142A3B] text-xs font-bold transition-all shadow-xs cursor-pointer"
              >
                <IconClipboard className="w-4 h-4 text-[#285C4D]" />
                {copied ? "Copied Order Slip!" : "Copy Rebalancing Plan"}
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl border border-[#E5E3DA] hover:bg-[#F7F6F1] text-[#66758A] hover:text-[#142A3B] text-xs font-semibold transition-all cursor-pointer"
                >
                  Close Audit
                </button>

                {appliedVersion ? (
                  <button
                    type="button"
                    disabled
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#10B981] text-white text-xs font-bold transition-all shadow-sm"
                  >
                    <IconCheck className="w-4 h-4" />
                    Portfolio Updated (v#{appliedVersion.version_number})
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleApply}
                    disabled={isApplying}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E453A] disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md cursor-pointer hover:shadow-lg active:scale-98"
                  >
                    {isApplying ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Updating Portfolio...
                      </>
                    ) : (
                      <>
                        <IconRefresh className="w-4 h-4" />
                        Apply Rebalance &amp; Update Portfolio
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
