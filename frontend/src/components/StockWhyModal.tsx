"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  fetchStockWhyExplanation,
  sendStockWhyChat,
  StockWhyExplanationResponse,
  TwoLevelParameterExplanation,
} from "../lib/api";
import {
  IconX,
  IconShield,
  IconTarget,
  IconChartBar,
  IconSliders,
  IconAlertTriangle,
  IconArrowUpRight,
  IconCheck,
  IconChevronDown,
  IconChevronUp,
  IconGlobe,
  IconNewspaper,
  IconSparkles,
  IconRefresh,
  IconInfo,
  IconFileText,
  IconScale,
} from "./icons";

interface StockWhyModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: string;
  versionId: string;
  symbol: string | null;
  companyName?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function StockWhyModal({
  isOpen,
  onClose,
  portfolioId,
  versionId,
  symbol,
  companyName,
}: StockWhyModalProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<StockWhyExplanationResponse | null>(null);

  // Active section tab
  const [activeTab, setActiveTab] = useState<string>("all");

  // Track expanded deep dive cards for parameters
  const [expandedParams, setExpandedParams] = useState<Record<string, boolean>>({});

  // Follow-up chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>("");
  const [isSendingChat, setIsSendingChat] = useState<boolean>(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !symbol || !portfolioId || !versionId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);
    setChatMessages([]);
    setExpandedParams({});

    fetchStockWhyExplanation(portfolioId, versionId, symbol)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load equity research explanation");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, symbol, portfolioId, versionId]);

  useEffect(() => {
    if (chatMessages.length > 0 && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, isSendingChat]);

  if (!isOpen) return null;

  const toggleParam = (paramName: string) => {
    setExpandedParams((prev) => ({ ...prev, [paramName]: !prev[paramName] }));
  };

  const handleSendChat = async (promptText?: string) => {
    const textToSend = promptText || chatInput;
    if (!textToSend.trim() || !symbol || !portfolioId || !versionId || isSendingChat) return;

    const newMessages: ChatMessage[] = [...chatMessages, { role: "user", content: textToSend }];
    setChatMessages(newMessages);
    setChatInput("");
    setIsSendingChat(true);

    try {
      const historyPayload = newMessages.map((m) => ({ role: m.role, content: m.content }));
      const res = await sendStockWhyChat(portfolioId, versionId, symbol, textToSend, historyPayload);
      setChatMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Unable to complete analysis inquiry: ${err.message || "Network error"}. Please retry.`,
        },
      ]);
    } finally {
      setIsSendingChat(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-xs overflow-y-auto animate-fade-in">
      <div className="relative w-full max-w-5xl bg-[#FAF9F5] border border-[#E5E3DA] rounded-2xl shadow-2xl overflow-hidden my-auto max-h-[92vh] flex flex-col">
        {/* Header Bar */}
        <div className="p-5 sm:p-6 bg-white border-b border-[#E5E3DA] flex items-start justify-between gap-4 shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="text-[11px] font-bold text-[#285C4D] bg-[#ECF3F0] px-2.5 py-0.5 rounded border border-[#C6D8D1] flex items-center gap-1.5">
                <IconShield className="w-3.5 h-3.5 text-[#285C4D]" />
                <span>SEBI Fiduciary Equity Research</span>
              </span>
              <span className="text-xs text-[#94A3B8]">&bull;</span>
              <span className="text-xs font-bold text-[#142A3B]">{data?.sector || "Equities"}</span>
              <span className="text-xs text-[#94A3B8]">&bull;</span>
              <span className="text-xs font-mono font-bold text-[#66758A]">NSE/BSE Listed</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold font-editorial text-[#142A3B] flex items-center gap-2">
              <span>{data?.company_name || companyName || symbol}</span>
              <span className="text-base sm:text-lg font-mono font-normal text-[#66758A]">({symbol})</span>
            </h2>
            {data && (
              <div className="flex items-center gap-3 mt-2 text-xs text-[#4A5568] flex-wrap">
                <span className="font-semibold text-[#142A3B]">
                  Weight: <strong className="text-[#285C4D] font-mono">{data.target_weight_pct.toFixed(1)}%</strong>
                </span>
                <span>&bull;</span>
                <span>
                  Allocation: <strong className="font-mono text-[#142A3B]">₹{data.actual_allocated_amount.toLocaleString("en-IN")}</strong>
                </span>
                <span>&bull;</span>
                <span>
                  Execution: <strong className="font-mono text-[#142A3B]">{data.shares_quantity} shares</strong> @ ₹{data.current_price.toLocaleString("en-IN")}
                </span>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-[#66758A] hover:text-[#142A3B] hover:bg-[#F7F6F1] transition-all cursor-pointer"
            aria-label="Close modal"
          >
            <IconX className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="bg-white border-b border-[#E5E3DA] px-5 sm:px-6 py-2 flex items-center gap-2 overflow-x-auto shrink-0 scrollbar-none">
          {[
            { id: "all", label: "Complete 10-Section Thesis" },
            { id: "fundamentals", label: "Audited Fundamentals (Two-Level)" },
            { id: "allocation", label: "Whole-Share Math & Constraints" },
            { id: "committee", label: "Multi-Agent Deliberation" },
            { id: "invalidation", label: "What Could Make This Wrong?" },
            { id: "chat", label: "Interactive Copilot Q&A" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                activeTab === tab.id
                  ? "bg-[#285C4D] text-white shadow-xs"
                  : "text-[#66758A] hover:text-[#142A3B] hover:bg-[#F7F6F1]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Body Content Stream */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-8 space-y-8">
          {loading && (
            <div className="py-16 text-center space-y-3">
              <div className="w-10 h-10 border-2 border-[#285C4D] border-t-transparent rounded-full animate-spin mx-auto" />
              <div className="text-sm font-semibold text-[#142A3B]">
                Synthesizing multi-agent equity research for {symbol}...
              </div>
              <p className="text-xs text-[#66758A] max-w-md mx-auto">
                Auditing balance sheet health, integer lot constraints, valuation multiples, and SEBI fiduciary rules.
              </p>
            </div>
          )}

          {error && (
            <div className="p-6 rounded-xl bg-red-50 border border-red-200 text-red-800 space-y-2">
              <div className="flex items-center gap-2 font-bold text-sm">
                <IconAlertTriangle className="w-4 h-4 text-red-600" />
                <span>Failed to retrieve research report</span>
              </div>
              <p className="text-xs leading-relaxed">{error}</p>
              <button
                type="button"
                onClick={() => {
                  setLoading(true);
                  setError(null);
                  fetchStockWhyExplanation(portfolioId, versionId, symbol!)
                    .then((res) => {
                      setData(res);
                      setLoading(false);
                    })
                    .catch((err) => {
                      setError(err.message);
                      setLoading(false);
                    });
                }}
                className="mt-2 text-xs font-bold px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 cursor-pointer"
              >
                Retry Research Query
              </button>
            </div>
          )}

          {data && !loading && (
            <>
              {/* SECTION 1: Why Was This Stock Selected? */}
              {(activeTab === "all" || activeTab === "committee") && (
                <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-[#EFECE4] pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        1
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Strategic Selection Rationale &amp; Portfolio Role
                      </h3>
                    </div>
                    <span className="text-xs text-[#285C4D] font-bold bg-[#ECF3F0] px-2.5 py-0.5 rounded border border-[#C6D8D1]">
                      {data.section_1_why_selected.portfolio_role}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs leading-relaxed">
                    <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5">
                      <span className="font-bold text-[#142A3B] flex items-center gap-1.5">
                        <IconTarget className="w-3.5 h-3.5 text-[#285C4D]" /> Core Investment Thesis
                      </span>
                      <p className="text-[#4A5568]">{data.section_1_why_selected.core_thesis}</p>
                    </div>

                    <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5">
                      <span className="font-bold text-[#142A3B] flex items-center gap-1.5">
                        <IconScale className="w-3.5 h-3.5 text-[#285C4D]" /> Alternatives Evaluated
                      </span>
                      <p className="text-[#4A5568]">{data.section_1_why_selected.alternatives_evaluated}</p>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#ECF3F0] border border-[#C6D8D1] text-xs text-[#285C4D]">
                    <strong>Fiduciary Suitability:</strong> {data.section_1_why_selected.investor_alignment}
                  </div>
                </div>
              )}

              {/* SECTION 2: Audited Fundamental Parameters (Two-Level Deck) */}
              {(activeTab === "all" || activeTab === "fundamentals") && (
                <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-[#EFECE4] pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        2
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Audited Fundamental Parameters (Level 1 Summary &amp; Level 2 Deep Dive)
                      </h3>
                    </div>
                    <span className="text-[11px] text-[#66758A]">
                      Click any parameter to expand formula, peer benchmarks &amp; limitations
                    </span>
                  </div>

                  <p className="text-xs text-[#66758A]">
                    {data.section_2_fundamental_analysis.fiduciary_summary}
                  </p>

                  <div className="space-y-3">
                    {data.section_2_fundamental_analysis.parameters.map((param, idx) => {
                      const isExpanded = !!expandedParams[param.parameter_name];
                      const l1 = param.level_1_summary;
                      const l2 = param.level_2_deep_dive;

                      return (
                        <div
                          key={idx}
                          className="rounded-xl border border-[#E5E3DA] bg-[#F7F6F1] overflow-hidden transition-all"
                        >
                          {/* Parameter Header & Level 1 Summary */}
                          <div className="p-4 bg-white border-b border-[#EFECE4]">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-bold text-[#142A3B]">
                                    {param.parameter_name}
                                  </span>
                                  <span className="text-[10px] font-mono font-bold bg-[#ECF3F0] text-[#285C4D] px-2 py-0.5 rounded">
                                    {l2.verification_status}
                                  </span>
                                </div>
                                <div className="text-xs text-[#4A5568] mt-1">
                                  <strong>What it is:</strong> {l1.what_it_means}
                                </div>
                              </div>

                              <div className="text-right shrink-0">
                                <div className="text-base font-bold font-mono text-[#285C4D]">
                                  {param.value}
                                </div>
                                <div className="text-[10px] text-[#66758A]">{param.unit}</div>
                              </div>
                            </div>

                            {/* Level 1 Contextual Interpretation */}
                            <div className="mt-3 pt-3 border-t border-[#F2EFE9] grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                              <div>
                                <span className="font-semibold text-[#142A3B]">How to interpret:</span>{" "}
                                <span className="text-[#4A5568]">{l1.how_to_interpret}</span>
                              </div>
                              <div>
                                <span className="font-semibold text-[#142A3B]">Portfolio relevance:</span>{" "}
                                <span className="text-[#4A5568]">{l1.why_it_matters_for_portfolio}</span>
                              </div>
                            </div>

                            {/* Deep Dive Toggle Button */}
                            <div className="mt-3 flex justify-end">
                              <button
                                type="button"
                                onClick={() => toggleParam(param.parameter_name)}
                                className="text-[11px] font-bold text-[#285C4D] hover:text-[#1E463A] flex items-center gap-1 cursor-pointer transition-colors"
                              >
                                <span>{isExpanded ? "Hide Deep Dive" : "Expand Level 2 Deep Dive Analysis"}</span>
                                {isExpanded ? (
                                  <IconChevronUp className="w-3.5 h-3.5" />
                                ) : (
                                  <IconChevronDown className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          </div>

                          {/* Level 2 Deep Dive Body */}
                          {isExpanded && (
                            <div className="p-4 bg-[#FAF9F5] border-t border-[#E5E3DA] space-y-3 text-xs animate-fade-in">
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div className="space-y-1">
                                  <span className="font-bold text-[#142A3B]">Formula &amp; Methodology:</span>
                                  <p className="text-[#4A5568] font-mono text-[11px] bg-white p-2 rounded border border-[#E5E3DA]">
                                    {l2.calculation_methodology}
                                  </p>
                                </div>

                                <div className="space-y-1">
                                  <span className="font-bold text-[#142A3B]">Benchmark Comparison:</span>
                                  <p className="text-[#4A5568] bg-white p-2 rounded border border-[#E5E3DA]">
                                    {l2.benchmark_comparison}
                                  </p>
                                </div>
                              </div>

                              <div className="space-y-1">
                                <span className="font-bold text-[#142A3B]">Why Favorable / Neutral in Context:</span>
                                <p className="text-[#4A5568]">{l2.why_favorable_or_unfavorable}</p>
                              </div>

                              <div className="space-y-1">
                                <span className="font-bold text-[#142A3B]">Limitations &amp; Analytical Caveats:</span>
                                <p className="text-[#991B1B] bg-red-50/50 p-2 rounded border border-red-100">
                                  {l2.limitations}
                                </p>
                              </div>

                              <div className="flex items-center justify-between text-[11px] text-[#66758A] pt-2 border-t border-[#EFECE4]">
                                <span>Source: {l2.evidence_source}</span>
                                <span>Observed: {l2.observation_date}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* SECTION 3 & 4: Valuation & Market/Sector Dynamics */}
              {(activeTab === "all" || activeTab === "fundamentals") && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Section 3: Valuation */}
                  <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-3">
                    <div className="flex items-center gap-2 border-b border-[#EFECE4] pb-3">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        3
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Valuation Multiple Corridor
                      </h3>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-center">
                      <div className="p-3 bg-[#F7F6F1] rounded-xl border border-[#E5E3DA]">
                        <div className="text-[10px] uppercase font-bold text-[#66758A]">Trailing P/E</div>
                        <div className="text-base font-bold font-mono text-[#142A3B]">
                          {data.section_3_valuation_analysis.trailing_pe}x
                        </div>
                      </div>
                      <div className="p-3 bg-[#F7F6F1] rounded-xl border border-[#E5E3DA]">
                        <div className="text-[10px] uppercase font-bold text-[#66758A]">Sector Median P/E</div>
                        <div className="text-base font-bold font-mono text-[#66758A]">
                          {data.section_3_valuation_analysis.industry_pe_median}x
                        </div>
                      </div>
                    </div>

                    <p className="text-xs text-[#4A5568] leading-relaxed">
                      {data.section_3_valuation_analysis.valuation_verdict}
                    </p>

                    <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E5E3DA] text-[11px] text-[#4A5568]">
                      <strong>Multiple Compression Risk:</strong> {data.section_3_valuation_analysis.multiple_compression_risk}
                    </div>
                  </div>

                  {/* Section 4: Market Dynamics */}
                  <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-3">
                    <div className="flex items-center gap-2 border-b border-[#EFECE4] pb-3">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        4
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Market &amp; Sector Dynamics
                      </h3>
                    </div>

                    <div className="p-3 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1 text-xs">
                      <span className="font-bold text-[#142A3B] flex items-center gap-1.5">
                        <IconGlobe className="w-3.5 h-3.5 text-[#285C4D]" /> Sector Demand Tailwinds
                      </span>
                      <p className="text-[#4A5568]">{data.section_4_market_and_sector.sector_headwinds_tailwinds}</p>
                    </div>

                    <p className="text-xs text-[#4A5568] leading-relaxed">
                      {data.section_4_market_and_sector.relative_performance_vs_nifty}
                    </p>

                    <div className="p-2.5 rounded-lg bg-[#ECF3F0] border border-[#C6D8D1] text-[11px] text-[#285C4D]">
                      <strong>Policy Cap Check:</strong> {data.section_4_market_and_sector.sector_concentration_check}
                    </div>
                  </div>
                </div>
              )}

              {/* SECTION 5 & 6: Macro/Filings & Risk/Stress Testing */}
              {(activeTab === "all" || activeTab === "allocation") && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Section 5: Macro & Filings */}
                  <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-3">
                    <div className="flex items-center gap-2 border-b border-[#EFECE4] pb-3">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        5
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Macro Climate &amp; Verified Filings
                      </h3>
                    </div>

                    <p className="text-xs text-[#4A5568] leading-relaxed">
                      {data.section_5_macro_and_news.rbi_monetary_policy_impact}
                    </p>

                    <div className="space-y-2 pt-1">
                      <div className="flex items-center justify-between">
                        <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                          Verified Exchange Filings (BSE / NSE):
                        </div>
                        {data.section_5_macro_and_news.primary_filing_url && (
                          <a
                            href={data.section_5_macro_and_news.primary_filing_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-[#285C4D] hover:text-[#1E463A] font-bold flex items-center gap-1 hover:underline"
                            title={`Open official corporate filing portal for ${symbol}`}
                          >
                            <span>Open Official Filing Portal</span>
                            <IconArrowUpRight className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                      {data.section_5_macro_and_news.verified_exchange_filings.map((filing, idx) => (
                        <div key={idx} className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5 text-xs">
                          <div className="flex items-center justify-between flex-wrap gap-2">
                            <span className="font-semibold text-[#142A3B]">{filing.filing_type}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-mono text-[#66758A] bg-white px-2 py-0.5 rounded border border-[#E5E3DA]">
                                {filing.date}
                              </span>
                              {filing.portal_url && (
                                <a
                                  href={filing.portal_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[11px] font-bold text-[#285C4D] hover:underline flex items-center gap-1"
                                >
                                  <span>{filing.exchange} Filings</span>
                                  <IconArrowUpRight className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          </div>
                          <p className="text-[#4A5568] text-[11px] leading-relaxed">{filing.summary}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Section 6: Risk & Downside Containment */}
                  <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-3">
                    <div className="flex items-center gap-2 border-b border-[#EFECE4] pb-3">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        6
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Risk Profile &amp; Downside Containment
                      </h3>
                    </div>

                    <p className="text-xs text-[#4A5568]">
                      {data.section_6_risk_analysis.systematic_risk}
                    </p>

                    <div className="space-y-2 pt-1">
                      <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                        Tail-Risk Crash Simulation:
                      </div>
                      {Object.values(data.section_6_risk_analysis.stress_test_simulations).map((sim: any, idx: number) => (
                        <div key={idx} className="p-3 rounded-lg bg-[#FAF9F5] border border-[#E5E3DA] space-y-1 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-[#142A3B]">{sim.scenario}</span>
                            <span className="font-mono font-bold text-red-700">{sim.projected_stock_impact_pct || sim.projected_portfolio_impact_pct}</span>
                          </div>
                          <p className="text-[11px] text-[#4A5568]">{sim.containment_strategy}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* SECTION 7: Mathematical Allocation & Whole-Share Audit */}
              {(activeTab === "all" || activeTab === "allocation") && (
                <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-[#EFECE4] pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        7
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Why This Allocation? Whole-Share Mathematical Audit
                      </h3>
                    </div>
                    <span className="text-xs font-bold text-[#285C4D] bg-[#ECF3F0] px-2.5 py-0.5 rounded border border-[#C6D8D1]">
                      SLSQP Optimizer Calibrated
                    </span>
                  </div>

                  {/* Math Proof Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
                    <div className="p-3 bg-[#F7F6F1] rounded-xl border border-[#E5E3DA]">
                      <div className="text-[10px] uppercase font-bold text-[#66758A]">Target Weight</div>
                      <div className="text-base font-bold font-mono text-[#285C4D]">
                        {data.section_7_why_this_allocation.target_weight_pct.toFixed(2)}%
                      </div>
                    </div>
                    <div className="p-3 bg-[#F7F6F1] rounded-xl border border-[#E5E3DA]">
                      <div className="text-[10px] uppercase font-bold text-[#66758A]">Reference Price</div>
                      <div className="text-base font-bold font-mono text-[#142A3B]">
                        ₹{data.section_7_why_this_allocation.current_price.toLocaleString("en-IN")}
                      </div>
                    </div>
                    <div className="p-3 bg-[#F7F6F1] rounded-xl border border-[#E5E3DA]">
                      <div className="text-[10px] uppercase font-bold text-[#66758A]">Whole Shares</div>
                      <div className="text-base font-bold font-mono text-[#142A3B]">
                        {data.section_7_why_this_allocation.shares_quantity}
                      </div>
                    </div>
                    <div className="p-3 bg-[#F7F6F1] rounded-xl border border-[#E5E3DA]">
                      <div className="text-[10px] uppercase font-bold text-[#66758A]">Capital Deployed</div>
                      <div className="text-base font-bold font-mono text-[#142A3B]">
                        ₹{data.section_7_why_this_allocation.actual_allocated_amount.toLocaleString("en-IN")}
                      </div>
                    </div>
                    <div className="p-3 bg-[#F7F6F1] rounded-xl border border-[#E5E3DA]">
                      <div className="text-[10px] uppercase font-bold text-[#66758A]">Residual Cash</div>
                      <div className="text-base font-bold font-mono text-[#285C4D]">
                        ₹{data.section_7_why_this_allocation.unallocated_cash_remainder.toLocaleString("en-IN")}
                      </div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#FAF9F5] border border-[#E5E3DA] space-y-2 text-xs">
                    <div className="font-mono font-semibold text-[#142A3B]">
                      Exact Mathematical Proof: {data.section_7_why_this_allocation.math_proof}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-[#EFECE4]">
                      <div>
                        <strong>Why not higher?</strong> {data.section_7_why_this_allocation.why_not_higher}
                      </div>
                      <div>
                        <strong>Why not lower?</strong> {data.section_7_why_this_allocation.why_not_lower}
                      </div>
                    </div>
                  </div>

                  <div className="text-[11px] text-[#66758A]">
                    {data.section_7_why_this_allocation.whole_share_enforcement}
                  </div>
                </div>
              )}

              {/* SECTION 8: Multi-Agent Committee Contributions */}
              {(activeTab === "all" || activeTab === "committee") && (
                <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-[#EFECE4] pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        8
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Multi-Agent Committee Deliberation Log
                      </h3>
                    </div>
                    <span className="text-xs text-[#285C4D] font-bold">Unanimous Consensus</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {data.section_8_agent_contributions.contributions.map((agent, idx) => (
                      <div key={idx} className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-[#142A3B]">{agent.agent_name}</span>
                          <span className="text-[10px] text-[#285C4D] font-semibold">{agent.role}</span>
                        </div>
                        <p className="text-[#4A5568] leading-relaxed text-[11px]">{agent.finding}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SECTION 9: Invalidation Criteria ("What Could Make This Wrong?") */}
              {(activeTab === "all" || activeTab === "invalidation") && (
                <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-[#EFECE4] pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[#ECF3F0] text-[#285C4D] text-xs font-bold flex items-center justify-center">
                        9
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Thesis Invalidation Criteria ("What Could Make This Recommendation Wrong?")
                      </h3>
                    </div>
                    <span className="text-xs font-bold text-[#991B1B] bg-red-50 px-2.5 py-0.5 rounded border border-red-200">
                      Ongoing Fiduciary Surveillance
                    </span>
                  </div>

                  <p className="text-xs text-[#4A5568]">
                    Lucid does not believe in blind buy-and-hold advice. Our multi-agent committee has established objective criteria that would invalidate this recommendation:
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {data.section_9_what_could_make_this_wrong.thesis_invalidation_catalysts.map((cat, idx) => (
                      <div key={idx} className="p-3.5 rounded-xl bg-red-50/40 border border-red-100 text-xs text-[#991B1B] space-y-1">
                        <span className="font-bold flex items-center gap-1.5">
                          <IconAlertTriangle className="w-3.5 h-3.5 text-red-600" /> Invalidation Catalyst #{idx + 1}
                        </span>
                        <p className="text-[#7F1D1D] leading-relaxed">{cat}</p>
                      </div>
                    ))}
                  </div>

                  <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E5E3DA] text-xs text-[#4A5568]">
                    <strong>Automated Rebalancing Trigger:</strong> {data.section_9_what_could_make_this_wrong.monitoring_triggers}
                  </div>
                </div>
              )}

              {/* SECTION 10: Final Fiduciary Conclusion */}
              {(activeTab === "all" || activeTab === "committee") && (
                <div className="bg-[#ECF3F0] p-6 rounded-2xl border border-[#C6D8D1] shadow-xs space-y-3">
                  <div className="flex items-center justify-between border-b border-[#C6D8D1] pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[#285C4D] text-white text-xs font-bold flex items-center justify-center">
                        10
                      </span>
                      <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                        Final Fiduciary Conclusion
                      </h3>
                    </div>
                    <span className="text-xs font-bold text-[#285C4D] flex items-center gap-1">
                      <IconCheck className="w-3.5 h-3.5 text-[#285C4D]" /> Verified Approved
                    </span>
                  </div>

                  <p className="text-xs text-[#142A3B] leading-relaxed font-medium">
                    {data.section_10_final_conclusion.executive_summary}
                  </p>

                  <div className="pt-2 border-t border-[#C6D8D1] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 text-xs text-[#285C4D]">
                    <span>{data.section_10_final_conclusion.suitability_statement}</span>
                    <span className="font-bold">Chief Risk: {data.section_10_final_conclusion.primary_risk_to_monitor}</span>
                  </div>
                </div>
              )}

              {/* INTERACTIVE COPILOT CHAT STREAM (Maintains Stock Context) */}
              <div className="bg-white p-6 rounded-2xl border border-[#E5E3DA] shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-[#EFECE4] pb-3">
                  <div className="flex items-center gap-2">
                    <IconSparkles className="w-5 h-5 text-[#285C4D]" />
                    <h3 className="text-base font-bold font-editorial text-[#142A3B]">
                      Ask AI Copilot About {symbol}
                    </h3>
                  </div>
                  <span className="text-[11px] text-[#66758A]">
                    Context-aware interactive equity research
                  </span>
                </div>

                {/* Suggested Quick Question Chips */}
                <div className="space-y-1.5">
                  <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                    Suggested Analytical Follow-Ups:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {data.suggested_followups.map((chip, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSendChat(chip)}
                        disabled={isSendingChat}
                        className="text-xs px-3 py-1.5 rounded-lg bg-[#F7F6F1] hover:bg-[#ECF3F0] border border-[#E5E3DA] text-[#142A3B] font-medium transition-all cursor-pointer text-left"
                      >
                        {chip}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Chat Messages Stream */}
                {chatMessages.length > 0 && (
                  <div className="space-y-3 pt-3 border-t border-[#EFECE4] max-h-64 overflow-y-auto pr-1">
                    {chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-xl text-xs leading-relaxed ${
                          msg.role === "user"
                            ? "bg-[#142A3B] text-white ml-8"
                            : "bg-[#F7F6F1] text-[#142A3B] border border-[#E5E3DA] mr-8 whitespace-pre-line"
                        }`}
                      >
                        <div className="text-[10px] font-bold uppercase tracking-wider opacity-70 mb-1">
                          {msg.role === "user" ? "You" : "Lucid Equity Research Copilot"}
                        </div>
                        {msg.content}
                      </div>
                    ))}
                    {isSendingChat && (
                      <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-xs text-[#66758A] mr-8 flex items-center gap-2">
                        <div className="w-3.5 h-3.5 border-2 border-[#285C4D] border-t-transparent rounded-full animate-spin" />
                        <span>Analyzing {symbol} evidence and financial factors...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>
                )}

                {/* Input Deck */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendChat();
                  }}
                  className="flex items-center gap-2 pt-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder={`Ask anything specific to ${symbol}'s allocation, financials, or risks...`}
                    disabled={isSendingChat}
                    className="flex-1 px-4 py-2.5 rounded-xl border border-[#E5E3DA] bg-[#FAF9F5] text-xs text-[#142A3B] placeholder-[#94A3B8] focus:outline-hidden focus:border-[#285C4D] focus:ring-1 focus:ring-[#285C4D]"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isSendingChat}
                    className="px-4 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] disabled:opacity-50 text-white font-semibold text-xs flex items-center gap-1.5 transition-all shadow-xs cursor-pointer shrink-0"
                  >
                    <span>Ask</span>
                    <IconArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-white border-t border-[#E5E3DA] flex items-center justify-between text-xs text-[#66758A] shrink-0">
          <span>Non-Custodial Multi-Agent Fiduciary Architecture &bull; SEBI RIA Compliant</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-[#E5E3DA] hover:bg-[#F7F6F1] font-semibold text-[#142A3B] transition-colors cursor-pointer"
          >
            Close Research Report
          </button>
        </div>
      </div>
    </div>
  );
}

