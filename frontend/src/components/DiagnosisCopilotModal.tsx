"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  fetchDiagnosisExplanation,
  sendDiagnosisChat,
  DiagnosisCopilotExplanation,
  DiagnosisTradeExplanation,
} from "../lib/api";
import {
  IconX,
  IconSparkles,
  IconShield,
  IconAlertTriangle,
  IconCheck,
  IconArrowRight,
  IconTrendingUp,
  IconTrendingDown,
  IconRefresh,
  IconSend,
  IconScale,
  IconInfo,
} from "./icons";

interface DiagnosisCopilotModalProps {
  isOpen: boolean;
  onClose: () => void;
  existingPortfolioId: string;
  portfolioName?: string;
  initialQuery?: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
}

export function DiagnosisCopilotModal({
  isOpen,
  onClose,
  existingPortfolioId,
  portfolioName,
  initialQuery,
}: DiagnosisCopilotModalProps) {
  const [activeTab, setActiveTab] = useState<"analysis" | "chat">("analysis");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<DiagnosisCopilotExplanation | null>(null);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [isSending, setIsSending] = useState<boolean>(false);
  const [followups, setFollowups] = useState<string[]>([]);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !existingPortfolioId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchDiagnosisExplanation(existingPortfolioId)
      .then((data) => {
        if (!isMounted) return;
        setExplanation(data);
        setFollowups(data.suggested_followups || []);
        setLoading(false);

        // Prepopulate first assistant message in chat
        const initialAssistantMsg: ChatMessage = {
          id: "welcome",
          role: "assistant",
          text: `### Fiduciary Analysis for ${data.portfolio_name}\n\nI have evaluated your portfolio against your configured single-stock ceiling (**${data.effective_stock_limit.toFixed(1)}%**) and sector cap (**${data.effective_sector_limit.toFixed(1)}%**).\n\n${data.section_1_portfolio_summary}\n\nYou can review the structured 7-section audit or ask any specific question below regarding individual stock trims, additions, or downside scenarios.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages([initialAssistantMsg]);

        // If an initial query was passed, send it automatically
        if (initialQuery) {
          handleSendMessage(initialQuery);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || "Failed to load rebalancing diagnosis explanation.");
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, existingPortfolioId]);

  useEffect(() => {
    if (activeTab === "chat") {
      chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, activeTab]);

  if (!isOpen) return null;

  const handleSendMessage = async (textToSend: string) => {
    const q = textToSend.trim();
    if (!q || isSending) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsSending(true);

    try {
      const historyPayload = messages.map((m) => ({ role: m.role, content: m.text }));
      const res = await sendDiagnosisChat(existingPortfolioId, q, historyPayload);

      const botMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        text: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
      if (res.suggested_followups && res.suggested_followups.length > 0) {
        setFollowups(res.suggested_followups);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        text: `Unable to complete query: ${err.message || "Network error. Please try again."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-[#142A3B]/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-5xl max-h-[92vh] flex flex-col bg-[#FBFBFA] rounded-2xl border border-[#E5E3DA] shadow-2xl overflow-hidden"
        role="dialog"
        aria-modal="true"
      >
        {/* Top Header */}
        <div className="px-6 py-4 bg-white border-b border-[#E5E3DA] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <IconSparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100/60 px-2 py-0.5 rounded-md">
                  Lucid Fiduciary Copilot
                </span>
                <span className="text-xs text-[#5A6E7C]">
                  {explanation ? `Audited against ${explanation.effective_stock_limit}% single-stock / ${explanation.effective_sector_limit}% sector rules` : "SEBI Non-Custodial Engine"}
                </span>
              </div>
              <h2 className="text-lg font-bold text-[#142A3B] leading-tight">
                {explanation?.portfolio_name || portfolioName || "Brokerage Portfolio"} — Rebalancing Audit & Explanation
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Switcher Tabs */}
            <div className="flex items-center bg-[#F7F6F1] p-1 rounded-xl border border-[#E5E3DA]">
              <button
                type="button"
                onClick={() => setActiveTab("analysis")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeTab === "analysis"
                    ? "bg-white text-[#142A3B] shadow-xs"
                    : "text-[#5A6E7C] hover:text-[#142A3B]"
                }`}
              >
                7-Section Audit
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("chat")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "chat"
                    ? "bg-white text-[#142A3B] shadow-xs"
                    : "text-[#5A6E7C] hover:text-[#142A3B]"
                }`}
              >
                <span>Interactive Copilot</span>
                {messages.length > 1 && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                )}
              </button>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="w-9 h-9 rounded-xl bg-[#F7F6F1] hover:bg-[#E5E3DA] text-[#5A6E7C] hover:text-[#142A3B] flex items-center justify-center transition-all cursor-pointer ml-1"
              aria-label="Close Modal"
            >
              <IconX className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#FBFBFA]">
          {loading && (
            <div className="py-24 flex flex-col items-center justify-center space-y-3">
              <IconRefresh className="w-8 h-8 text-emerald-600 animate-spin" />
              <p className="text-sm font-semibold text-[#142A3B]">
                Reconstructing deterministic trade rationale and fiduciary boundaries...
              </p>
              <p className="text-xs text-[#5A6E7C]">
                Analyzing single-stock limits, whole-share allocations, and sector exposure.
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 space-y-3">
              <div className="flex items-center gap-2 font-bold text-sm">
                <IconAlertTriangle className="w-4 h-4 text-rose-600" />
                <span>Unable to load portfolio diagnosis explanation</span>
              </div>
              <p className="text-xs text-rose-700 leading-relaxed">{error}</p>
              <button
                type="button"
                onClick={() => {
                  setLoading(true);
                  setError(null);
                  fetchDiagnosisExplanation(existingPortfolioId)
                    .then((d) => {
                      setExplanation(d);
                      setLoading(false);
                    })
                    .catch((err) => {
                      setError(err.message);
                      setLoading(false);
                    });
                }}
                className="px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition-all cursor-pointer"
              >
                Retry Audit
              </button>
            </div>
          )}

          {!loading && !error && explanation && activeTab === "analysis" && (
            <div className="space-y-6">
              {/* Summary Stats Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 bg-white rounded-xl border border-[#E5E3DA]">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#5A6E7C]">Total Valuation</div>
                  <div className="text-lg font-bold text-[#142A3B] mt-0.5">{formatCurrency(explanation.total_market_value)}</div>
                </div>
                <div className="p-3.5 bg-white rounded-xl border border-[#E5E3DA]">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#5A6E7C]">Single-Stock Cap</div>
                  <div className="text-lg font-bold text-emerald-700 mt-0.5">{explanation.effective_stock_limit.toFixed(1)}% Max</div>
                </div>
                <div className="p-3.5 bg-white rounded-xl border border-[#E5E3DA]">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#5A6E7C]">Sector Cap</div>
                  <div className="text-lg font-bold text-emerald-700 mt-0.5">{explanation.effective_sector_limit.toFixed(1)}% Max</div>
                </div>
                <div className="p-3.5 bg-white rounded-xl border border-[#E5E3DA]">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#5A6E7C]">Unallocated Cash</div>
                  <div className="text-lg font-bold text-[#142A3B] mt-0.5">{formatCurrency(explanation.unallocated_cash)}</div>
                </div>
              </div>

              {/* Section 1: Portfolio Summary */}
              <div className="p-5 bg-white rounded-2xl border border-[#E5E3DA] space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-md bg-[#142A3B] text-white text-[11px] font-bold flex items-center justify-center">1</span>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#142A3B]">Portfolio Status & Context</h3>
                </div>
                <p className="text-xs text-[#2C3E50] leading-relaxed">
                  {explanation.section_1_portfolio_summary}
                </p>
              </div>

              {/* Section 2: Identified Problems */}
              <div className="p-5 bg-white rounded-2xl border border-[#E5E3DA] space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-md bg-amber-600 text-white text-[11px] font-bold flex items-center justify-center">2</span>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#142A3B]">Identified Imbalances & Vulnerabilities</h3>
                </div>
                <div className="space-y-2">
                  {explanation.section_2_problems_identified.map((prob, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs space-y-1">
                      <div className="font-bold text-amber-900 flex items-center gap-1.5">
                        <IconAlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        <span>{prob.issue}</span>
                      </div>
                      <div className="text-[11px] text-amber-800">
                        <span className="font-semibold">Regulatory/Policy Basis:</span> {prob.policy_origin}
                      </div>
                      <div className="text-[11px] text-amber-800">
                        <span className="font-semibold">Fiduciary Impact:</span> {prob.impact}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 3: Proposed Trades Table */}
              <div className="p-5 bg-white rounded-2xl border border-[#E5E3DA] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-md bg-emerald-600 text-white text-[11px] font-bold flex items-center justify-center">3</span>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-[#142A3B]">
                      Proposed Whole-Share Rebalancing Plan
                    </h3>
                  </div>
                  <span className="text-[11px] font-semibold text-[#5A6E7C]">
                    100% Executable Integer Lots
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#E5E3DA] text-[11px] font-bold uppercase text-[#5A6E7C] bg-[#F7F6F1]/60">
                        <th className="py-2.5 px-3">Instrument</th>
                        <th className="py-2.5 px-2">Action</th>
                        <th className="py-2.5 px-2 text-right">Current Qty</th>
                        <th className="py-2.5 px-2 text-right">Target Qty</th>
                        <th className="py-2.5 px-2 text-right">Trade Shares</th>
                        <th className="py-2.5 px-2 text-right">Ref Price</th>
                        <th className="py-2.5 px-2 text-right">Est. Trade Value</th>
                        <th className="py-2.5 px-3">Plain-Language Rationale</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E3DA]/60">
                      {explanation.section_3_proposed_trades.map((trade, idx) => {
                        const isSell = trade.action === "SELL";
                        const isBuy = trade.action === "BUY";
                        return (
                          <tr key={idx} className="hover:bg-[#F7F6F1]/50 transition-colors">
                            <td className="py-2.5 px-3">
                              <div className="font-bold text-[#142A3B]">{trade.symbol}</div>
                              <div className="text-[10px] text-[#5A6E7C]">{trade.sector}</div>
                            </td>
                            <td className="py-2.5 px-2">
                              <span
                                className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${
                                  isSell
                                    ? "bg-rose-100 text-rose-800"
                                    : isBuy
                                    ? "bg-emerald-100 text-emerald-800"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                {trade.action}
                              </span>
                            </td>
                            <td className="py-2.5 px-2 text-right font-medium text-[#142A3B]">
                              {trade.current_quantity}
                              <span className="text-[10px] text-[#5A6E7C] block">
                                {trade.current_weight_pct.toFixed(1)}%
                              </span>
                            </td>
                            <td className="py-2.5 px-2 text-right font-medium text-[#142A3B]">
                              {trade.target_quantity}
                              <span className="text-[10px] text-[#5A6E7C] block">
                                {trade.target_weight_pct.toFixed(1)}%
                              </span>
                            </td>
                            <td className="py-2.5 px-2 text-right font-bold">
                              <span
                                className={
                                  isSell ? "text-rose-700" : isBuy ? "text-emerald-700" : "text-slate-600"
                                }
                              >
                                {isSell ? `-${trade.proposed_trade_quantity}` : isBuy ? `+${trade.proposed_trade_quantity}` : "0"}
                              </span>
                            </td>
                            <td className="py-2.5 px-2 text-right text-[#5A6E7C]">
                              ₹{trade.reference_price.toLocaleString("en-IN", { maximumFractionDigits: 1 })}
                            </td>
                            <td className="py-2.5 px-2 text-right font-semibold text-[#142A3B]">
                              {trade.estimated_trade_value > 0
                                ? `₹${trade.estimated_trade_value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
                                : "—"}
                            </td>
                            <td className="py-2.5 px-3 text-[11px] text-[#2C3E50] max-w-xs leading-relaxed">
                              {trade.reason}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Section 4: Why Recommended */}
              <div className="p-5 bg-white rounded-2xl border border-[#E5E3DA] space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-md bg-blue-600 text-white text-[11px] font-bold flex items-center justify-center">4</span>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#142A3B]">Why This Plan Is Recommended</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {explanation.section_4_why_recommended.map((reason, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-xs text-[#2C3E50] flex items-start gap-2">
                      <IconCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{reason}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 5: Before vs. After Comparison Table */}
              <div className="p-5 bg-white rounded-2xl border border-[#E5E3DA] space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-md bg-purple-600 text-white text-[11px] font-bold flex items-center justify-center">5</span>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#142A3B]">Before vs. After Comparison</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#E5E3DA] text-[11px] font-bold uppercase text-[#5A6E7C] bg-[#F7F6F1]/60">
                        <th className="py-2.5 px-3">Metric</th>
                        <th className="py-2.5 px-3 text-right">Current Portfolio</th>
                        <th className="py-2.5 px-3 text-right">Proposed Rebalanced Portfolio</th>
                        <th className="py-2.5 px-3">Target Improvement</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E3DA]/60">
                      <tr>
                        <td className="py-2.5 px-3 font-semibold text-[#142A3B]">Total Portfolio Valuation</td>
                        <td className="py-2.5 px-3 text-right font-bold text-[#142A3B]">{explanation.section_5_before_after_comparison.total_portfolio_value?.current}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-800">{explanation.section_5_before_after_comparison.total_portfolio_value?.proposed}</td>
                        <td className="py-2.5 px-3 text-[#5A6E7C]">Capital preserved (excluding broker fees)</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-semibold text-[#142A3B]">Equities Count</td>
                        <td className="py-2.5 px-3 text-right font-bold text-[#142A3B]">{explanation.section_5_before_after_comparison.holdings_count?.current} stocks</td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-800">{explanation.section_5_before_after_comparison.holdings_count?.proposed} stocks</td>
                        <td className="py-2.5 px-3 text-emerald-700 font-semibold">Broadened cross-sector breadth</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-semibold text-[#142A3B]">Largest Single Stock Weight</td>
                        <td className="py-2.5 px-3 text-right font-bold text-rose-700">{explanation.section_5_before_after_comparison.largest_stock_weight?.current}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-800">{explanation.section_5_before_after_comparison.largest_stock_weight?.proposed}</td>
                        <td className="py-2.5 px-3 text-emerald-700 font-semibold">Capped at {explanation.effective_stock_limit}% ceiling</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-semibold text-[#142A3B]">IT Sector Exposure</td>
                        <td className="py-2.5 px-3 text-right font-bold text-rose-700">{explanation.section_5_before_after_comparison.it_sector_exposure?.current}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-800">{explanation.section_5_before_after_comparison.it_sector_exposure?.proposed}</td>
                        <td className="py-2.5 px-3 text-emerald-700 font-semibold">Brought within {explanation.effective_sector_limit}% sector cap</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-semibold text-[#142A3B]">Diversification Score</td>
                        <td className="py-2.5 px-3 text-right font-bold text-amber-700">{explanation.section_5_before_after_comparison.diversification_score?.current}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-800">{explanation.section_5_before_after_comparison.diversification_score?.proposed}</td>
                        <td className="py-2.5 px-3 text-emerald-700 font-semibold">Substantial risk-reduction gain</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-semibold text-[#142A3B]">Cash Remaining (Buffer)</td>
                        <td className="py-2.5 px-3 text-right font-bold text-[#142A3B]">{explanation.section_5_before_after_comparison.cash_remaining?.current}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-800">{explanation.section_5_before_after_comparison.cash_remaining?.proposed}</td>
                        <td className="py-2.5 px-3 text-[#5A6E7C]">Liquid buffer after whole-share sizing</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Section 6: Remaining Risks & Limitations */}
              <div className="p-5 bg-white rounded-2xl border border-[#E5E3DA] space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-md bg-slate-700 text-white text-[11px] font-bold flex items-center justify-center">6</span>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#142A3B]">Downside Realities & Limitations</h3>
                </div>
                <div className="space-y-2">
                  {explanation.section_6_remaining_risks.map((risk, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-[#2C3E50] flex items-start gap-2">
                      <IconInfo className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{risk}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 7: Final Fiduciary Summary */}
              <div className="p-5 bg-emerald-50/60 rounded-2xl border border-emerald-200 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-md bg-emerald-700 text-white text-[11px] font-bold flex items-center justify-center">7</span>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-900">Final Fiduciary Summary</h3>
                </div>
                <p className="text-xs text-emerald-950 leading-relaxed font-medium">
                  {explanation.section_7_final_fiduciary_summary}
                </p>

                <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-emerald-200/80">
                  <span className="text-[11px] text-emerald-800">
                    Ready to ask specific questions about individual stocks or market drop simulations?
                  </span>
                  <button
                    type="button"
                    onClick={() => setActiveTab("chat")}
                    className="px-4 py-2 rounded-xl bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition-all cursor-pointer flex items-center gap-1.5 shadow-xs"
                  >
                    <span>Chat With Diagnosis Copilot</span>
                    <IconArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Interactive Chat Tab */}
          {activeTab === "chat" && (
            <div className="flex flex-col h-full space-y-4">
              {/* Messages list */}
              <div className="flex-1 overflow-y-auto space-y-4 pr-1 min-h-[360px] max-h-[500px]">
                {messages.map((m) => {
                  const isUser = m.role === "user";
                  return (
                    <div
                      key={m.id}
                      className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
                    >
                      <div className="flex items-center gap-2 mb-1 px-1">
                        <span className="text-[10px] font-bold uppercase text-[#5A6E7C]">
                          {isUser ? "You" : "Lucid Fiduciary Copilot"}
                        </span>
                        <span className="text-[10px] text-[#5A6E7C]">{m.timestamp}</span>
                      </div>
                      <div
                        className={`p-4 rounded-2xl text-xs leading-relaxed max-w-[85%] whitespace-pre-wrap ${
                          isUser
                            ? "bg-[#142A3B] text-white rounded-tr-xs"
                            : "bg-white text-[#142A3B] border border-[#E5E3DA] rounded-tl-xs shadow-xs"
                        }`}
                      >
                        {m.text}
                      </div>
                    </div>
                  );
                })}
                {isSending && (
                  <div className="flex items-center gap-2 p-3 bg-white rounded-xl border border-[#E5E3DA] w-fit text-xs text-[#5A6E7C]">
                    <IconRefresh className="w-3.5 h-3.5 animate-spin text-emerald-600" />
                    <span>Analyzing portfolio trades and calculating response...</span>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Suggested Followups */}
              {followups.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-[#E5E3DA]">
                  <div className="text-[10px] font-bold uppercase text-[#5A6E7C]">Suggested Inquiries:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {followups.map((q, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSendMessage(q)}
                        disabled={isSending}
                        className="px-2.5 py-1 rounded-lg bg-white hover:bg-emerald-50 border border-[#E5E3DA] hover:border-emerald-300 text-[11px] font-medium text-[#142A3B] transition-all cursor-pointer text-left"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input Form */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage(inputQuery);
                }}
                className="flex items-center gap-2 pt-2"
              >
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Ask why a stock was trimmed/added, test a 30% crash, or ask what happens if you don't rebalance..."
                  disabled={isSending}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-[#E5E3DA] bg-white text-xs text-[#142A3B] placeholder-[#5A6E7C] focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600"
                />
                <button
                  type="submit"
                  disabled={!inputQuery.trim() || isSending}
                  className="px-4 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-[#E5E3DA] text-white text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5"
                >
                  <IconSend className="w-3.5 h-3.5" />
                  <span>Send</span>
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

