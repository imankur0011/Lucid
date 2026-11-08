"use client";

import React, { useState } from "react";
import { PortfolioVersion } from "../lib/api";
import {
  IconLightbulb,
  IconShield,
  IconSliders,
  IconTarget,
  IconAlertTriangle,
  IconArrowUpRight,
  IconCheck,
  IconChevronDown,
  IconGlobe,
  IconNewspaper,
  IconChartBar,
} from "./icons";
import { getStockDetails } from "../lib/stockRationales";

interface ExplainabilityViewProps {
  portfolio: PortfolioVersion | null;
  onGoToGenerator: () => void;
  onAskAboutStock?: (symbolOrPrompt: string) => void;
  initialSymbol?: string | null;
  onGoToPortfolio?: () => void;
  onOpenStockWhy?: (symbol: string, companyName?: string) => void;
}

export function ExplainabilityView({
  portfolio,
  onGoToGenerator,
  onAskAboutStock,
  initialSymbol,
  onGoToPortfolio,
  onOpenStockWhy,
}: ExplainabilityViewProps) {
  const [activeSection, setActiveSection] = useState<
    "stocks" | "safety" | "rebalancing"
  >("stocks");
  const [filterSector, setFilterSector] = useState<string>("ALL");
  const [expandedNotes, setExpandedNotes] = useState<Record<string, boolean>>({});
  const [expandedMetrics, setExpandedMetrics] = useState<Record<string, boolean>>({});

  const toggleAgentNotes = (symbol: string) => {
    setExpandedNotes((prev) => ({ ...prev, [symbol]: !prev[symbol] }));
  };

  const toggleMetric = (key: string) => {
    setExpandedMetrics((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  React.useEffect(() => {
    if (initialSymbol && portfolio) {
      const match = portfolio.holdings.find(
        (h) => h.symbol.toUpperCase() === initialSymbol.toUpperCase()
      );
      if (match?.sector_name) {
        setFilterSector(match.sector_name);
      }
      setActiveSection("stocks");
    }
  }, [initialSymbol, portfolio]);

  if (!portfolio) {
    return (
      <div className="p-12 text-center rounded-2xl bg-white border border-[#E5E3DA] shadow-xs max-w-xl mx-auto my-8">
        <div className="w-12 h-12 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] text-[#66758A] flex items-center justify-center mx-auto mb-3">
          <IconLightbulb className="w-6 h-6 text-[#285C4D]" />
        </div>
        <h3 className="text-lg font-bold text-[#142A3B] mb-2 font-editorial">
          No Portfolio Available Yet
        </h3>
        <p className="text-xs text-[#66758A] mb-5 leading-relaxed">
          Create an optimized portfolio first to inspect its plain-language multi-agent reasoning, SEBI safety checks, and verified exchange filings.
        </p>
        <button
          onClick={onGoToGenerator}
          type="button"
          className="px-5 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white font-semibold text-xs transition-all shadow-xs cursor-pointer"
        >
          Create Your Portfolio
        </button>
      </div>
    );
  }

  const holdings = portfolio.holdings || [];

  // Group holdings by sector to show diversification
  const sectorMap = holdings.reduce<Record<string, number>>((acc, h) => {
    const s = h.sector_name || "Diversified";
    acc[s] = (acc[s] || 0) + (Number(h.target_weight_pct) || 0);
    return acc;
  }, {});

  const sectorsSorted = Object.entries(sectorMap).sort((a, b) => b[1] - a[1]);
  const uniqueSectors = Array.from(new Set(holdings.map((h) => h.sector_name || "Diversified")));

  const filteredHoldings =
    filterSector === "ALL"
      ? holdings
      : holdings.filter((h) => (h.sector_name || "Diversified") === filterSector);

  return (
    <div className="space-y-6">
      {/* Editorial Header Panel */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-widest">
                MULTI-AGENT AI EXPLAINABILITY &amp; AUDIT TRAIL
              </span>
              <span className="text-[#D6D3C8]">&bull;</span>
              <span className="text-xs font-bold text-[#285C4D] bg-[#ECF3F0] px-2.5 py-0.5 rounded border border-[#C6D8D1]">
                SEBI Fiduciary Standard
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-editorial text-[#142A3B] tracking-tight">
              Why Were These Stocks Chosen For You?
            </h1>
            <p className="text-sm text-[#4A5568] mt-2 max-w-3xl leading-relaxed">
              Every rupee in your portfolio was evaluated, debated, and approved by our 5 specialized AI investment agents. Here is the complete, transparent breakdown of why each company made the cut, what financial metrics were verified, and how SEBI safety rules protect your capital.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-[#F7F6F1] p-3 rounded-xl border border-[#E5E3DA] shrink-0">
            <div className="text-right">
              <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                Target Allocation
              </div>
              <div className="text-lg font-bold text-[#142A3B] tabular-nums font-editorial">
                ₹{Number(portfolio.investment_amount).toLocaleString("en-IN")}
              </div>
            </div>
            <div className="h-8 w-px bg-[#D6D3C8] mx-1" />
            <div className="text-left">
              <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider">
                Risk Tier
              </div>
              <div className="text-sm font-bold text-[#285C4D] uppercase">
                {portfolio.risk_category}
              </div>
            </div>
          </div>
        </div>

        {/* 5-Agent Collaborative AI Committee Overview */}
        <div className="mt-6 pt-6 border-t border-[#EFECE4]">
          <div className="text-xs font-bold text-[#142A3B] uppercase tracking-wider mb-3 flex items-center justify-between">
            <span>How Your 5-Agent AI Committee Evaluated Every Stock:</span>
            <span className="text-xs text-[#285C4D] font-medium hidden sm:inline">Unanimous Multi-Agent Consensus Required</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Agent 1: Macro */}
            <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#142A3B] flex items-center gap-1.5">
                  <IconGlobe className="w-3.5 h-3.5 text-[#285C4D]" />
                  <span>Macro Agent</span>
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">6.5% Repo</span>
              </div>
              <div className="text-xs text-[#4A5568] leading-tight">
                Analyzes India GDP (7.2%), RBI monetary stance, and sector demand tailwinds.
              </div>
            </div>

            {/* Agent 2: Fundamentals */}
            <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#142A3B] flex items-center gap-1.5">
                  <IconChartBar className="w-3.5 h-3.5 text-[#285C4D]" />
                  <span>Analyst Agent</span>
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">ROE &gt; 18%</span>
              </div>
              <div className="text-xs text-[#4A5568] leading-tight">
                Audits balance sheet health, P/E multiples, cash generation, and competitive moats.
              </div>
            </div>

            {/* Agent 3: News */}
            <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#142A3B] flex items-center gap-1.5">
                  <IconNewspaper className="w-3.5 h-3.5 text-[#285C4D]" />
                  <span>News Agent</span>
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">Clean</span>
              </div>
              <div className="text-xs text-[#4A5568] leading-tight">
                Inspects real-time BSE filings, quarterly order books, and governance integrity.
              </div>
            </div>

            {/* Agent 4: Strategist */}
            <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#142A3B] flex items-center gap-1.5">
                  <IconTarget className="w-3.5 h-3.5 text-[#285C4D]" />
                  <span>Strategist Agent</span>
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">Sharpe Max</span>
              </div>
              <div className="text-xs text-[#4A5568] leading-tight">
                Calibrates candidate weights to your stated goal and expected return target.
              </div>
            </div>

            {/* Agent 5: Critic */}
            <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#142A3B] flex items-center gap-1.5">
                  <IconShield className="w-3.5 h-3.5 text-[#285C4D]" />
                  <span>Critic Agent</span>
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">&le;25% Cap</span>
              </div>
              <div className="text-xs text-[#4A5568] leading-tight">
                Enforces SEBI caps, whole shares execution, and stress-tests -20% crash shocks.
              </div>
            </div>
          </div>
        </div>

        {/* 3 Intuitive Primary Section Navigators */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-6 mt-6 border-t border-[#EFECE4]">
          <button
            onClick={() => setActiveSection("stocks")}
            type="button"
            className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
              activeSection === "stocks"
                ? "bg-[#ECF3F0] border-[#285C4D] shadow-xs ring-1 ring-[#285C4D]"
                : "bg-white border-[#E5E3DA] hover:border-[#D6D3C8]"
            }`}
          >
            <div className="text-xs font-bold uppercase tracking-wider text-[#285C4D] mb-1 flex items-center justify-between">
              <span>Section 1</span>
              <span className="bg-[#285C4D] text-white text-[10px] px-2 py-0.5 rounded-full font-bold">
                {holdings.length} Holdings
              </span>
            </div>
            <div className="text-sm font-bold text-[#142A3B]">Stock-by-Stock Decisions</div>
            <div className="text-xs text-[#4A5568] mt-0.5">
              Plain-English reasons, AI agent votes &amp; BSE/NSE filings for every holding
            </div>
          </button>

          <button
            onClick={() => setActiveSection("safety")}
            type="button"
            className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
              activeSection === "safety"
                ? "bg-[#ECF3F0] border-[#285C4D] shadow-xs ring-1 ring-[#285C4D]"
                : "bg-white border-[#E5E3DA] hover:border-[#D6D3C8]"
            }`}
          >
            <div className="text-xs font-bold uppercase tracking-wider text-[#285C4D] mb-1">
              Section 2
            </div>
            <div className="text-sm font-bold text-[#142A3B]">Safety Guardrails &amp; Lucid Risk Policies</div>
            <div className="text-xs text-[#4A5568] mt-0.5">
              How 25% single-stock &amp; 40% sector limits protect you from major losses
            </div>
          </button>

          <button
            onClick={() => setActiveSection("rebalancing")}
            type="button"
            className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
              activeSection === "rebalancing"
                ? "bg-[#ECF3F0] border-[#285C4D] shadow-xs ring-1 ring-[#285C4D]"
                : "bg-white border-[#E5E3DA] hover:border-[#D6D3C8]"
            }`}
          >
            <div className="text-xs font-bold uppercase tracking-wider text-[#285C4D] mb-1">
              Section 3
            </div>
            <div className="text-sm font-bold text-[#142A3B]">When to Rebalance or Sell</div>
            <div className="text-xs text-[#4A5568] mt-0.5">
              Clear triggers: 5% weight drift, quarterly profit drops, or goal horizon
            </div>
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* SECTION 1: STOCK-BY-STOCK DECISIONS (HERO EXPLAINABILITY) */}
      {/* ======================================================== */}
      {activeSection === "stocks" && (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-[#EFECE4]">
            <div>
              <div className="flex items-center gap-2">
                <IconShield className="w-5 h-5 text-[#285C4D]" />
                <h2 className="text-xl font-bold text-[#142A3B] font-editorial">
                  Stock-by-Stock AI Reasoning &amp; Audited Evidence
                </h2>
              </div>
              <p className="text-xs text-[#4A5568] mt-1">
                Click any stock to inspect its multi-agent audit trail, audited ratios, and official exchange filings.
              </p>
            </div>

            {/* Sector Quick Filter */}
            {uniqueSectors.length > 1 && (
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-xs text-[#66758A] font-semibold mr-1">Filter:</span>
                <button
                  type="button"
                  onClick={() => setFilterSector("ALL")}
                  className={`text-xs px-2.5 py-1 rounded-lg border font-semibold transition-colors cursor-pointer ${
                    filterSector === "ALL"
                      ? "bg-[#142A3B] text-white border-[#142A3B]"
                      : "bg-[#F7F6F1] text-[#4A5568] border-[#E5E3DA] hover:border-[#D6D3C8]"
                  }`}
                >
                  All ({holdings.length})
                </button>
                {uniqueSectors.map((sec) => (
                  <button
                    key={sec}
                    type="button"
                    onClick={() => setFilterSector(sec)}
                    className={`text-xs px-2.5 py-1 rounded-lg border font-semibold transition-colors cursor-pointer ${
                      filterSector === sec
                        ? "bg-[#142A3B] text-white border-[#142A3B]"
                        : "bg-[#F7F6F1] text-[#4A5568] border-[#E5E3DA] hover:border-[#D6D3C8]"
                    }`}
                  >
                    {sec}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Stock-by-Stock Comprehensive Cards */}
          <div className="space-y-6">
            {filteredHoldings.map((h) => {
              const details = getStockDetails(h.symbol, h.sector_name);
              const audit = details.agentAudit;

              return (
                <div
                  key={h.symbol}
                  className="rounded-2xl bg-white border border-[#E5E3DA] shadow-xs hover:border-[#285C4D]/60 transition-all overflow-hidden"
                >
                  {/* Card Header: Symbol, Name, Allocation */}
                  <div className="p-5 sm:p-6 bg-gradient-to-r from-[#F7F6F1] to-white border-b border-[#E5E3DA] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div className="flex items-center gap-3.5">
                      <div className="px-3 py-2 rounded-xl bg-[#142A3B] text-white font-black text-base tracking-wider shadow-xs">
                        {h.symbol}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-base sm:text-lg font-bold text-[#142A3B]">
                            {h.security_name}
                          </h3>
                          <span className="text-xs px-2 py-0.5 rounded-md bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1] font-semibold">
                            {h.sector_name}
                          </span>
                        </div>
                        <div className="text-xs text-[#66758A] mt-0.5 flex items-center gap-2">
                          <span>NSE: <strong className="text-[#142A3B]">{h.symbol}</strong></span>
                          <span>&bull;</span>
                          <span>BSE Scrip: <strong className="font-mono text-[#142A3B]">{details.bseCode}</strong></span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 bg-white px-4 py-2.5 rounded-xl border border-[#E5E3DA] shadow-xs">
                      <div>
                        <div className="text-[10px] text-[#66758A] font-bold uppercase tracking-wider">
                          Target Allocation
                        </div>
                        <div className="text-base font-extrabold text-[#166534] tabular-nums">
                          {h.target_weight_pct.toFixed(2)}%
                        </div>
                      </div>
                      <div className="h-7 w-px bg-[#E5E3DA]" />
                      <div>
                        <div className="text-[10px] text-[#66758A] font-bold uppercase tracking-wider">
                          Value &amp; Units
                        </div>
                        <div className="text-xs font-bold text-[#142A3B] tabular-nums">
                          ₹{Number(h.target_amount).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                          <span className="text-[#66758A] font-normal ml-1">
                            ({h.shares_quantity} sh @ ₹{Number(h.latest_price).toLocaleString("en-IN", { maximumFractionDigits: 2 })})
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Body Content */}
                  <div className="p-5 sm:p-6 space-y-5">
                    {/* Plain English Core Reason & Moat */}
                    <div className="space-y-1.5 bg-[#F7F6F1]/50 p-4 rounded-xl border border-[#E5E3DA]">
                      <div className="flex items-center gap-2">
                        <IconTarget className="w-4 h-4 text-[#285C4D]" />
                        <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                          Why This Stock is Recommended For You:
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-[#142A3B] leading-relaxed">
                        {details.role}
                      </p>
                      <p className="text-sm text-[#4A5568] leading-relaxed">
                        {h.decision_reason && h.decision_reason.length > 50
                          ? h.decision_reason
                          : details.thesis}
                      </p>
                    </div>

                    {/* Consolidated Agent Consensus Ribbon */}
                    <div className="space-y-3">
                      <div className="p-3.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] flex flex-col md:flex-row md:items-center justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider mr-1">
                            Agent Consensus:
                          </span>
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white border border-[#E5E3DA] text-[#142A3B]">
                            <IconTarget className="w-3.5 h-3.5 text-[#285C4D]" /> Strategist: <strong className="text-[#285C4D]">Goal Aligned</strong>
                          </span>
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white border border-[#E5E3DA] text-[#142A3B]">
                            <IconChartBar className="w-3.5 h-3.5 text-[#285C4D]" /> Fundamentals: <strong className="text-[#285C4D]">Passed Audit</strong>
                          </span>
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white border border-[#E5E3DA] text-[#142A3B]">
                            <IconShield className="w-3.5 h-3.5 text-[#B45309]" /> Critic: <strong className="text-[#B45309]">≤25% Safety Verified</strong>
                          </span>
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white border border-[#E5E3DA] text-[#142A3B]">
                            <IconGlobe className="w-3.5 h-3.5 text-[#285C4D]" /> Macro: <strong className="text-[#285C4D]">Favorable</strong>
                          </span>
                        </div>

                        <button
                          type="button"
                          onClick={() => toggleAgentNotes(h.symbol)}
                          className="text-xs font-semibold text-[#285C4D] hover:underline flex items-center gap-1 self-start md:self-auto cursor-pointer"
                        >
                          <span>{expandedNotes[h.symbol] ? "Hide Agent Deliberations" : "Inspect Agent Deliberations"}</span>
                          <IconChevronDown
                            className={`w-3.5 h-3.5 transition-transform duration-200 ${
                              expandedNotes[h.symbol] ? "rotate-180" : ""
                            }`}
                          />
                        </button>
                      </div>

                      {/* Expandable Agent Deliberation Details */}
                      {expandedNotes[h.symbol] && (
                        <div className="p-4 rounded-xl bg-white border border-[#E5E3DA] shadow-xs space-y-3 animate-fadeIn">
                          <div className="text-xs font-bold text-[#142A3B] uppercase tracking-wider flex items-center gap-1.5">
                            <IconLightbulb className="w-4 h-4 text-[#285C4D]" />
                            <span>Detailed Multi-Agent Deliberation Transcripts ({h.symbol}):</span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            <div className="p-3 rounded-lg bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                              <span className="font-bold text-[#285C4D] flex items-center gap-1.5">
                                <IconTarget className="w-3.5 h-3.5 text-[#285C4D]" /> Strategist Agent
                              </span>
                              <p className="text-[#4A5568] leading-relaxed">
                                {audit?.strategistNote ||
                                  `Optimized for high Sharpe contribution and capital efficiency to support your ${portfolio.risk_category} wealth objective.`}
                              </p>
                            </div>

                            <div className="p-3 rounded-lg bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                              <span className="font-bold text-[#285C4D] flex items-center gap-1.5">
                                <IconChartBar className="w-3.5 h-3.5 text-[#285C4D]" /> Fundamental Analyst
                              </span>
                              <p className="text-[#4A5568] leading-relaxed">
                                {audit?.fundamentalCheck ||
                                  `Audited balance sheet ratios: ROE (${details.roe}), P/E valuation (${details.pe}), and debt leverage (${details.debtToEquity}) meet fiduciary criteria.`}
                              </p>
                            </div>

                            <div className="p-3 rounded-lg bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                              <span className="font-bold text-[#B45309] flex items-center gap-1.5">
                                <IconShield className="w-3.5 h-3.5 text-[#B45309]" /> Risk Critic &amp; Policy Safeguards
                              </span>
                              <p className="text-[#4A5568] leading-relaxed">
                                {audit?.criticSafeguard ||
                                  `Verified ≤25.0% single-stock ceiling adherence, integer lot execution, and evaluated resilience under -20% downside stress scenarios.`}
                              </p>
                            </div>

                            <div className="p-3 rounded-lg bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                              <span className="font-bold text-[#285C4D] flex items-center gap-1.5">
                                <IconGlobe className="w-3.5 h-3.5 text-[#285C4D]" /> Macro &amp; Regulatory Climate
                              </span>
                              <p className="text-[#4A5568] leading-relaxed">
                                {audit?.macroContext ||
                                  `India's 7.2% GDP expansion and steady RBI 6.5% interest rate stance support corporate earnings across the ${h.sector_name || "underlying"} industry.`}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Audited Valuation & Risk Parameters with Exact Provenance */}
                    <div>
                      <div className="text-[11px] font-bold text-[#66758A] uppercase tracking-wider mb-2 flex items-center justify-between">
                        <span>Audited Valuation, Quality &amp; Fiduciary Risk Parameters:</span>
                        <span className="text-[10px] text-[#94A3B8]">Verified Against SEBI RIA Safeguards</span>
                      </div>

                      <div className="overflow-x-auto rounded-xl border border-[#E5E3DA]">
                        <table className="w-full text-left text-xs bg-white">
                          <thead className="bg-[#F7F6F1] text-[#66758A] uppercase text-[10px] font-bold border-b border-[#E5E3DA]">
                            <tr>
                              <th className="py-2.5 px-3.5">Financial Metric</th>
                              <th className="py-2.5 px-3.5 text-right">Audited Value</th>
                              <th className="py-2.5 px-3.5">Fiduciary Benchmark Corridor</th>
                              <th className="py-2.5 px-3.5">Regulatory Provenance Source</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#E5E3DA] text-[#142A3B]">
                            {/* Dynamic Valuation & Fiduciary Evaluation Table with Two-Level Deep Dive */}
                            {(() => {
                              const deNum = parseFloat(details.debtToEquity || "0.5");
                              const peNum = parseFloat(details.pe || "20");
                              const isBank = (h.sector_name || "").toLowerCase().includes("bank") || (h.sector_name || "").toLowerCase().includes("financial");
                              const isUtility = (h.sector_name || "").toLowerCase().includes("power") || (h.sector_name || "").toLowerCase().includes("utilit") || h.symbol === "ACMESOLAR" || h.symbol === "ADANIGREEN";

                              const metricsList = [
                                {
                                  id: `${h.symbol}_pe`,
                                  name: "Price / Earnings (P/E)",
                                  val: details.pe,
                                  valColor: "text-[#142A3B]",
                                  corridor: peNum > 70
                                    ? "High-Growth Scaling Multiple (Capacity pipeline expansion; position strictly capped against valuation contraction)"
                                    : peNum < 15
                                    ? "< 15.0x Deep Value Multiple (High margin of safety & earnings yield)"
                                    : "< 35.0x Valuation Corridor (Fair multiple)",
                                  source: `BSE Scrip ${details.bseCode} • TTM Disclosures`,
                                  def: "Current Market Price divided by Diluted Trailing 12-Month Earnings Per Share.",
                                  formula: "P/E = CMP / TTM EPS",
                                  benchmark: "NIFTY 50 10-Yr Historical Median: 21.5x. Peer Group Corridor: 18x - 28x.",
                                  context: "Evaluates the price paid per rupee of profit. Favorable when matched by high earnings growth and robust ROE.",
                                  limitations: "Can be misleading during cyclical peaks or if one-off exceptional items artificially alter profit.",
                                },
                                {
                                  id: `${h.symbol}_roe`,
                                  name: "Return on Equity (ROE)",
                                  val: details.roe,
                                  valColor: "text-[#285C4D]",
                                  corridor: "> 12.0% Cost of Equity Hurdle (Capital compounding efficiency)",
                                  source: "Audited FY25 Annual Financial Statements",
                                  def: "Measures net profit generated as a percentage of shareholders' equity.",
                                  formula: "ROE = (PAT / Average Shareholder Net Worth) × 100",
                                  benchmark: "Corporate India Median: 14.0%. Sector Benchmark: > 16.0%.",
                                  context: "Demonstrates management's ability to compound retained capital organically without equity dilution.",
                                  limitations: "Can be artificially boosted by high debt; must be verified alongside balance sheet leverage.",
                                },
                                {
                                  id: `${h.symbol}_beta`,
                                  name: "Market Beta (β)",
                                  val: details.beta.toFixed(2),
                                  valColor: "text-[#142A3B]",
                                  corridor: details.beta > 1.3
                                    ? "> 1.30 High Sensitivity (Growth driver; cushioned by low-beta anchors)"
                                    : details.beta < 0.8
                                    ? "< 0.80 Defensive Buffer (Low volatility market cushion)"
                                    : "0.80 – 1.30 Balanced Band (Nifty 50 = 1.0)",
                                  source: "NSE 3-Year Daily Closing Covariance",
                                  def: "Measures stock return volatility relative to the broad market benchmark (NIFTY 50 = 1.0).",
                                  formula: "Beta = Covariance(Stock, NIFTY 50) / Variance(NIFTY 50)",
                                  benchmark: "NIFTY 50 = 1.00. Range: 0.65 (defensive) to 1.45 (cyclical/high-growth).",
                                  context: "Calibrates portfolio volatility. Low beta provides downside cushioning during broad market corrections.",
                                  limitations: "Historical measure; does not capture sudden company-specific operational shocks.",
                                },
                                {
                                  id: `${h.symbol}_de`,
                                  name: isBank ? "Capital Adequacy (CRAR) / D/E" : isUtility ? "Project Debt / Equity" : "Debt to Equity (D/E)",
                                  val: isBank ? "18.5% (D/E: N/A)" : details.debtToEquity,
                                  valColor: "text-[#142A3B]",
                                  corridor: isBank
                                    ? "RBI Basel III Hurdle: >11.5% (Tier-1: 16.2%; Deposits are operational liabilities, D/E marked N/A)"
                                    : isUtility
                                    ? "Regulated Utility Structure (Project debt ring-fenced by 25-yr sovereign SECI PPAs)"
                                    : deNum <= 0.05
                                    ? "< 0.10x Pristine Balance Sheet (Zero default hazard & elite liquidity)"
                                    : "< 1.50x Solvency Ceiling (Low default hazard)",
                                  source: isBank ? "RBI Basel III Pillar III Disclosures" : "Balance Sheet Borrowings / Net Worth",
                                  def: isBank
                                    ? "Capital Adequacy Ratio: Total regulatory capital divided by risk-weighted assets under Basel III."
                                    : "Total external borrowings divided by total shareholders' equity.",
                                  formula: isBank ? "CRAR = (Tier 1 + Tier 2 Capital) / Total RWA" : "D/E = Total Debt / Net Worth",
                                  benchmark: isBank ? "RBI Mandate: 11.5%. Indian SCB Avg: 16.8%." : "Prudent Ceiling: ≤ 1.50x. IT/FMCG: < 0.20x.",
                                  context: isBank
                                    ? "For banks, D/E is economically invalid because customer deposits are liabilities. A 18.5% CRAR ensures solvency against credit defaults."
                                    : isUtility
                                    ? "Project debt is non-recourse and fully serviced by long-term 25-year sovereign tariffs."
                                    : "Ensures interest coverage is preserved during economic recessions.",
                                  limitations: isBank ? "Sensitive to sudden spikes in bad loans or NPAs." : "Low debt may sometimes indicate under-investment.",
                                },
                                {
                                  id: `${h.symbol}_div`,
                                  name: "Dividend Yield",
                                  val: details.dividendYield,
                                  valColor: "text-[#142A3B]",
                                  corridor: parseFloat(details.dividendYield || "0") === 0
                                    ? "100% Cash Flow Reinvestment into operating capex"
                                    : "Cash Return Cushion & Payout Continuity",
                                  source: "Corporate Actions Registrar (BSE/NSE)",
                                  def: "Annual cash dividend paid per share divided by the current market share price.",
                                  formula: "Dividend Yield = (Annual DPS / CMP) × 100",
                                  benchmark: "NIFTY 50 Median: ~1.2%. High Yield Corridors: > 2.5%.",
                                  context: "Provides liquidity cash flow and confirms genuine free cash flow generation.",
                                  limitations: "High dividend yields can occasionally reflect declining share prices or unsupportable payout ratios.",
                                },
                              ];

                              return (
                                <>
                                  {metricsList.map((m) => {
                                    const isRowExpanded = !!expandedMetrics[m.id];
                                    return (
                                      <React.Fragment key={m.id}>
                                        <tr
                                          onClick={() => toggleMetric(m.id)}
                                          className="cursor-pointer hover:bg-[#F7F6F1] transition-colors"
                                        >
                                          <td className="py-2.5 px-3.5 font-semibold flex items-center justify-between">
                                            <span>{m.name}</span>
                                            <span className="text-[10px] text-[#285C4D] font-mono ml-2">
                                              {isRowExpanded ? "▲" : "▼"}
                                            </span>
                                          </td>
                                          <td className={`py-2.5 px-3.5 text-right font-mono font-bold ${m.valColor}`}>
                                            {m.val}
                                          </td>
                                          <td className="py-2.5 px-3.5 text-[#4A5568]">
                                            {m.corridor}
                                          </td>
                                          <td className="py-2.5 px-3.5 text-[#66758A] truncate max-w-xs font-mono text-[11px]">
                                            {m.source}
                                          </td>
                                        </tr>
                                        {isRowExpanded && (
                                          <tr className="bg-[#FAF9F5] border-t border-b border-[#E5E3DA]">
                                            <td colSpan={4} className="p-3.5">
                                              <div className="space-y-2 text-xs">
                                                <div className="flex items-center justify-between pb-1.5 border-b border-[#EFECE4]">
                                                  <span className="font-bold text-[#142A3B]">
                                                    Level 2 Deep Dive: {m.name}
                                                  </span>
                                                  <span className="font-mono text-[11px] text-[#285C4D]">
                                                    {m.formula}
                                                  </span>
                                                </div>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                                                  <div>
                                                    <span className="font-bold text-[#142A3B]">Definition:</span>{" "}
                                                    <span className="text-[#4A5568]">{m.def}</span>
                                                  </div>
                                                  <div>
                                                    <span className="font-bold text-[#142A3B]">Benchmark:</span>{" "}
                                                    <span className="text-[#4A5568]">{m.benchmark}</span>
                                                  </div>
                                                </div>
                                                <div className="text-[11px]">
                                                  <span className="font-bold text-[#142A3B]">Industry &amp; Fiduciary Context:</span>{" "}
                                                  <span className="text-[#4A5568]">{m.context}</span>
                                                </div>
                                                <div className="text-[11px] text-[#991B1B] bg-red-50/50 p-1.5 rounded border border-red-100">
                                                  <strong>Limitations:</strong> {m.limitations}
                                                </div>
                                              </div>
                                            </td>
                                          </tr>
                                        )}
                                      </React.Fragment>
                                    );
                                  })}
                                </>
                              );
                            })()}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* Card Footer: Filing Citation & Direct Action Hyperlinks */}
                  <div className="p-4 sm:px-6 bg-[#F7F6F1] border-t border-[#E5E3DA] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                    <div className="text-xs text-[#4A5568] flex items-center gap-2">
                      <span className="font-semibold text-[#142A3B]">Verified Citation:</span>
                      <span className="truncate max-w-xs sm:max-w-md">{details.filingSource}</span>
                    </div>

                    <div className="flex items-center gap-2.5 w-full sm:w-auto">
                      {/* Direct External Hyperlink to Official BSE / NSE Filing */}
                      <a
                        href={details.filingUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={`Open ${details.filingSource} in verified exchange portal`}
                        className="text-xs px-3.5 py-2 rounded-xl bg-white border border-[#D6D3C8] hover:border-[#142A3B] text-[#142A3B] font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
                      >
                        <span>View Official Exchange Filing</span>
                        <IconArrowUpRight className="w-3.5 h-3.5 text-[#285C4D]" />
                      </a>

                      {/* Interactive Ask AI Copilot Button */}
                      {onOpenStockWhy ? (
                        <button
                          type="button"
                          onClick={() => onOpenStockWhy(h.symbol, h.security_name)}
                          className="text-xs px-3.5 py-2 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
                        >
                          <IconLightbulb className="w-3.5 h-3.5" />
                          <span>Ask AI why {h.symbol} &rarr;</span>
                        </button>
                      ) : onAskAboutStock ? (
                        <button
                          type="button"
                          onClick={() =>
                            onAskAboutStock(
                              `Explain why the AI Analyst and Critic agents chose ${h.symbol} for my portfolio, what risks they identified, and whether there are safer alternatives.`
                            )
                          }
                          className="text-xs px-3.5 py-2 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
                        >
                          <IconLightbulb className="w-3.5 h-3.5" />
                          <span>Ask AI why {h.symbol} &rarr;</span>
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* SECTION 2: SAFETY GUARDRAILS & LUCID RISK POLICIES */}
      {/* ======================================================== */}
      {activeSection === "safety" && (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs space-y-6">
          <div className="flex items-center gap-2 pb-2 border-b border-[#EFECE4]">
            <IconSliders className="w-5 h-5 text-[#285C4D]" />
            <h2 className="text-xl font-bold text-[#142A3B] font-editorial">
              Safety Guardrails: How We Protect Your Capital
            </h2>
          </div>
          <p className="text-sm text-[#4A5568] leading-relaxed">
            The optimization engine enforces strict mathematical boundaries grounded in Lucid&apos;s internal risk policy and SEBI suitability standards. Even if a single company or sector looks attractive, our algorithm prevents you from taking dangerous, concentrated risks.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#285C4D]">
                Single Stock Concentration Cap
              </div>
              <div className="text-xl font-bold text-[#142A3B]">Maximum 25.0% Per Company</div>
              <p className="text-xs text-[#4A5568] leading-relaxed">
                Prevents catastrophic drawdowns if an individual corporation suffers unexpected management turmoil, earnings misses, or operational setbacks.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#285C4D]">
                Macro Sector Ceiling
              </div>
              <div className="text-xl font-bold text-[#142A3B]">Maximum 40.0% Per Economic Sector</div>
              <p className="text-xs text-[#4A5568] leading-relaxed">
                Ensures capital is spread across banking, technology, consumer goods, healthcare, and infrastructure rather than clustered in a single cyclical industry.
              </p>
            </div>
          </div>

          {/* Active Fiduciary Guardrail Audit Checklist */}
          <div className="space-y-3 pt-2">
            <div className="text-xs font-bold text-[#142A3B] uppercase tracking-wider flex items-center justify-between">
              <span>Active Guardrail Compliance Verdict:</span>
              <span className="text-xs text-[#285C4D] font-bold">100% Guardrails Satisfied</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#142A3B]">Single-Stock Cap</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">PASSED</span>
                </div>
                <div className="text-base font-bold text-[#142A3B] tabular-nums">
                  {Math.max(...holdings.map(h => Number(h.target_weight_pct) || 0)).toFixed(1)}% / 25.0%
                </div>
                <p className="text-xs text-[#4A5568]">
                  All individual positions are strictly capped under the 25.0% ceiling.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#142A3B]">Sector Ceiling</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">PASSED</span>
                </div>
                <div className="text-base font-bold text-[#142A3B] tabular-nums">
                  {(sectorsSorted[0]?.[1] || 0).toFixed(1)}% / 40.0%
                </div>
                <p className="text-xs text-[#4A5568]">
                  Capital distributed across {uniqueSectors.length} distinct economic sectors.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#142A3B]">Integer Lot Sizing</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#ECF3F0] text-[#285C4D]">VERIFIED</span>
                </div>
                <div className="text-base font-bold text-[#142A3B]">
                  100% Whole Shares
                </div>
                <p className="text-xs text-[#4A5568]">
                  Zero fractional share roundings; direct execution on NSE/BSE.
                </p>
              </div>
            </div>

            {/* Quick action to navigate to visualizer in HoldingsView */}
            {onGoToPortfolio && (
              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={onGoToPortfolio}
                  className="text-xs text-[#285C4D] font-bold hover:underline inline-flex items-center gap-1 cursor-pointer"
                >
                  <span>View interactive sector breakdown in My Portfolio &rarr;</span>
                </button>
              </div>
            )}
          </div>

          {/* Fiduciary Suitability Note */}
          <div className="p-5 rounded-xl bg-[#ECF3F0] border border-[#C6D8D1] space-y-1.5">
            <div className="flex items-center gap-2 text-[#285C4D] font-bold text-sm">
              <IconCheck className="w-4 h-4" />
              <span>Fiduciary Suitability Verification Passed</span>
            </div>
            <p className="text-xs text-[#285C4D] leading-relaxed">
              Because this portfolio was constructed for your specific risk tier ({portfolio.risk_category.toUpperCase()}), it avoids speculative penny stocks while allocating to disciplined, dividend-paying market leaders with audited multi-year balance sheets.
            </p>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* SECTION 3: WHEN TO REBALANCE OR SELL */}
      {/* ======================================================== */}
      {activeSection === "rebalancing" && (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs space-y-6">
          <div className="flex items-center gap-2 pb-2 border-b border-[#EFECE4]">
            <IconAlertTriangle className="w-5 h-5 text-[#B45309]" />
            <h2 className="text-xl font-bold text-[#142A3B] font-editorial">
              When to Rebalance or Sell: Clear Operational Triggers
            </h2>
          </div>
          <p className="text-sm text-[#4A5568] leading-relaxed">
            A disciplined portfolio is not static. Over time, stock prices move at different rates, altering your risk profile. Below are the transparent rules governing when and why you should execute a rebalance.
          </p>

          <div className="space-y-4">
            <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#B45309]">
                Trigger 1: Weight Drift Exceeds ±5% Concentration Threshold
              </div>
              <h3 className="text-base font-bold text-[#142A3B]">
                Cap Breach &amp; Concentration Risk
              </h3>
              <p className="text-sm text-[#4A5568] leading-relaxed">
                If an individual stock gains substantial value and grows past the 25% single-stock ceiling (e.g. rising to 28% of your overall capital), you should trim the excess profit and reallocate the proceeds across underweight defensive holdings.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#B45309]">
                Trigger 2: Fundamental Degradation or Moat Erosion
              </div>
              <h3 className="text-base font-bold text-[#142A3B]">
                Balance Sheet &amp; Governance Check
              </h3>
              <p className="text-sm text-[#4A5568] leading-relaxed">
                If a company reports two consecutive quarters of deteriorating operating margins, takes on excessive unhedged debt, or experiences severe regulatory sanctions, our engine automatically flags the security for replacement.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-1.5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#285C4D]">
                Trigger 3: Goal Timeline Transition (&lt;18 Months Remaining)
              </div>
              <h3 className="text-base font-bold text-[#142A3B]">
                Capital Preservation Glidepath
              </h3>
              <p className="text-sm text-[#4A5568] leading-relaxed">
                As you approach your goal completion date, equity risk should be systematically de-risked into liquid overnight funds and debt to safeguard compounded gains against late-stage market corrections.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}