"use client";

import React, { useState, useEffect } from "react";
import { PortfolioVersion, ScenarioResult } from "../lib/api";
import { IconBolt, IconAlertTriangle, IconLightbulb } from "./icons";
import { ConversationalAssistant } from "./ConversationalAssistant";

interface StressScenariosViewProps {
  portfolio: PortfolioVersion | null;
  scenarioResult: ScenarioResult | null;
  runningScenario: string | null;
  onRunScenario: (type: string, name: string, dropPct: number, sector?: string) => void;
  onGoToGenerator: () => void;
  initialQuery?: string | null;
  existingPortfolioId?: string | null;
}

export function StressScenariosView({
  portfolio,
  scenarioResult,
  runningScenario,
  onRunScenario,
  onGoToGenerator,
  initialQuery,
  existingPortfolioId,
}: StressScenariosViewProps) {

  if (!portfolio && !existingPortfolioId) {
    return (
      <div className="p-12 text-center rounded-2xl bg-white border border-[#E5E3DA] shadow-xs max-w-xl mx-auto my-8">
        <div className="w-12 h-12 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] text-[#66758A] flex items-center justify-center mx-auto mb-3">
          <IconBolt className="w-6 h-6 text-[#142A3B]" />
        </div>
        <h3 className="text-lg font-bold text-[#142A3B] mb-2 font-editorial">
          No Portfolio Available for Stress Testing
        </h3>
        <p className="text-xs text-[#66758A] mb-5 leading-relaxed">
          Please generate an optimized portfolio first before running market shock and conversational stress simulations.
        </p>
        <button
          onClick={onGoToGenerator}
          type="button"
          className="px-5 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white font-semibold text-xs transition-all shadow-xs cursor-pointer"
        >
          Go to Portfolio Generator
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-[#B91C1C] uppercase tracking-wider">
                Tail-Risk &amp; Macro Simulation
              </span>
              <span className="text-[#D6D3C8]">&bull;</span>
              <span className="text-xs font-bold text-[#285C4D] bg-[#ECF3F0] px-2.5 py-0.5 rounded border border-[#C6D8D1]">
                Live Fiduciary Copilot
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-editorial text-[#142A3B] tracking-tight flex items-center gap-2">
              <IconBolt className="w-6 h-6 text-[#142A3B]" />
              <span>Stress Testing &amp; Downside Risk Containment</span>
            </h1>
            <p className="text-sm text-[#4A5568] mt-1.5 max-w-3xl leading-relaxed">
              Ask natural-language questions about your holdings, explore why specific companies were chosen, or simulate macroeconomic stress scenarios and interest rate shocks.
            </p>
          </div>
        </div>
      </div>

      {/* Part 1: Full-width Interactive Conversational Assistant */}
      <div className="space-y-4">
        <ConversationalAssistant
          portfolio={portfolio}
          initialQuery={initialQuery}
          existingPortfolioId={existingPortfolioId}
        />
      </div>

      {/* Part 2: 1-Click Standard Preset Scenarios */}
      <div className="space-y-4 pt-4 border-t border-[#EFECE4]">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#66758A]">
            One-Click Preset Macro Shocks
          </span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Interactive Scenario Cards */}
            <div className="space-y-4">
              {/* Scenario 1: Market Correction */}
              <div className="p-5 sm:p-6 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs hover:border-[#D6D3C8] transition-all space-y-3">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-[#142A3B] text-base">Severe Market Correction</h3>
                  <span className="text-xs font-bold text-[#B91C1C] bg-[#FEF2F2] px-2.5 py-0.5 rounded border border-[#FECACA]">
                    -20% Index
                  </span>
                </div>
                <p className="text-sm text-[#4A5568] leading-relaxed">
                  Simulates a systemic 20% drawdown across broad Indian equity indices (NIFTY 50 / SENSEX) triggered by global macro headwinds.
                </p>
                <button
                  onClick={() =>
                    onRunScenario("market_shock", "Severe Market Correction (-20%)", 20.0)
                  }
                  disabled={runningScenario !== null}
                  type="button"
                  className="w-full py-2.5 rounded-xl bg-[#FEF2F2] hover:bg-[#FEE2E2] border border-[#FECACA] text-[#B91C1C] text-sm font-bold transition-all disabled:opacity-60 cursor-pointer shadow-xs"
                >
                  {runningScenario === "market_shock" ? "Simulating Regime Shock..." : "Run -20% Market Shock"}
                </button>
              </div>

              {/* Scenario 2: Tech Sector Headwind */}
              <div className="p-5 sm:p-6 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs hover:border-[#D6D3C8] transition-all space-y-3">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-[#142A3B] text-base">Tech Sector Headwind</h3>
                  <span className="text-xs font-bold text-[#B45309] bg-[#FFFBEB] px-2.5 py-0.5 rounded border border-[#FDE68A]">
                    -15% IT Sector
                  </span>
                </div>
                <p className="text-sm text-[#4A5568] leading-relaxed">
                  Evaluates idiosyncratic downside impact if Indian IT consulting and software export leaders face client discretionary budget freezes.
                </p>
                <button
                  onClick={() =>
                    onRunScenario("sector_shock", "IT Sector Headwind (-15%)", 15.0, "Information Technology")
                  }
                  disabled={runningScenario !== null}
                  type="button"
                  className="w-full py-2.5 rounded-xl bg-[#FFFBEB] hover:bg-[#FEF3C7] border border-[#FDE68A] text-[#B45309] text-sm font-bold transition-all disabled:opacity-60 cursor-pointer shadow-xs"
                >
                  {runningScenario === "sector_shock" ? "Simulating Sector Shock..." : "Run -15% IT Sector Shock"}
                </button>
              </div>

              {/* Scenario 3: Interest Rate Hike */}
              <div className="p-5 sm:p-6 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs hover:border-[#D6D3C8] transition-all space-y-3">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-[#142A3B] text-base">RBI Monetary Tightening</h3>
                  <span className="text-xs font-bold text-[#4338CA] bg-[#EEF2FF] px-2.5 py-0.5 rounded border border-[#C7D2FE]">
                    +50 bps Repo
                  </span>
                </div>
                <p className="text-sm text-[#4A5568] leading-relaxed">
                  Simulates a 50 bps surprise policy repo rate hike by the RBI to contain headline inflation, compressing equity valuation multiples.
                </p>
                <button
                  onClick={() =>
                    onRunScenario("interest_rate_hike", "50 bps Repo Rate Tightening", 4.0)
                  }
                  disabled={runningScenario !== null}
                  type="button"
                  className="w-full py-2.5 rounded-xl bg-[#EEF2FF] hover:bg-[#E0E7FF] border border-[#C7D2FE] text-[#4338CA] text-sm font-bold transition-all disabled:opacity-60 cursor-pointer shadow-xs"
                >
                  {runningScenario === "interest_rate_hike" ? "Simulating Rate Hike..." : "Run +50 bps Rate Simulation"}
                </button>
              </div>
            </div>

            {/* Right 2 Columns: Stressed Outcomes */}
            <div className="lg:col-span-2">
              {scenarioResult ? (
                <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-xs space-y-6">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                      <h3 className="text-lg font-bold text-[#142A3B]">{scenarioResult.scenario_name}</h3>
                      <span className="text-sm text-[#4A5568]">Simulated Stressed Valuation</span>
                    </div>
                    <span className="text-xs px-3 py-1 rounded-full bg-[#FEF2F2] border border-[#FECACA] text-[#B91C1C] font-extrabold tabular-nums">
                      Portfolio Impact: -{scenarioResult.loss_pct.toFixed(2)}%
                    </span>
                  </div>

                  {/* 3 Metric Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                      <div className="text-sm text-[#4A5568] font-medium">Baseline Capital</div>
                      <div className="text-xl font-bold text-[#142A3B] mt-1 tabular-nums">
                        ₹{Number(scenarioResult.baseline_value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </div>
                      <div className="text-xs text-[#66758A] mt-0.5">Pre-shock capital</div>
                    </div>

                    <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                      <div className="text-sm text-[#4A5568] font-medium">Stressed Value</div>
                      <div className="text-xl font-bold text-[#B91C1C] mt-1 tabular-nums">
                        ₹{Number(scenarioResult.stressed_value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </div>
                      <div className="text-xs text-[#B91C1C] mt-0.5">Post-shock residual</div>
                    </div>

                    <div className="p-4 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
                      <div className="text-sm text-[#4A5568] font-medium">Projected Drawdown</div>
                      <div className="text-xl font-bold text-[#B45309] mt-1 tabular-nums">
                        -₹{Number(scenarioResult.loss_amount).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </div>
                      <div className="text-xs text-[#B45309] mt-0.5">Estimated downside</div>
                    </div>
                  </div>

                  {/* Downside Analysis Panel */}
                  <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2">
                    <h4 className="text-sm font-bold text-[#142A3B] uppercase tracking-wider flex items-center gap-1.5">
                      <IconAlertTriangle className="w-4 h-4 text-[#B45309]" />
                      <span>Downside Containment &amp; Diversification Analysis</span>
                    </h4>
                    <p className="text-sm text-[#4A5568] leading-relaxed">
                      {scenarioResult.impact_summary}
                    </p>
                  </div>

                  {/* Stress Testing Notice */}
                  <div className="text-xs sm:text-sm text-[#4A5568] bg-[#F7F6F1] p-4 rounded-xl border border-[#E5E3DA] leading-relaxed">
                    <strong className="text-[#142A3B]">Hypothetical Simulation Disclaimer:</strong> Stress scenario outcomes reflect factor beta sensitivities and mathematical drawdown approximations under SEBI advisory risk modeling standards.
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center rounded-2xl bg-white border border-[#E5E3DA] shadow-xs">
                  <div className="w-12 h-12 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] text-[#66758A] flex items-center justify-center mx-auto mb-3">
                    <IconBolt className="w-6 h-6 text-[#142A3B]" />
                  </div>
                  <h3 className="text-base font-bold text-[#142A3B] mb-1">Select a Stress Scenario</h3>
                  <p className="text-xs text-[#66758A] max-w-md mx-auto">
                    Choose any macroeconomic or sector shock scenario on the left to compute projected asset drawdowns and verify downside protection.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
  );
}
