"use client";

import React from "react";
import { IconSliders, IconShield, IconCheck, IconX } from "./icons";

interface PortfolioGeneratorProps {
  portfolioName: string;
  setPortfolioName: (name: string) => void;
  investmentAmount: number;
  setInvestmentAmount: (amt: number) => void;
  horizonMonths: number;
  setHorizonMonths: (months: number) => void;
  excludedSectors: string[];
  setExcludedSectors: (sectors: string[]) => void;
  maxStockWeight: number;
  maxSectorWeight: number;
  userPrompt: string;
  setUserPrompt: (prompt: string) => void;
  loading: boolean;
  generationStage: string;
  onGenerate: () => void;
}

export function PortfolioGenerator({
  portfolioName,
  setPortfolioName,
  investmentAmount,
  setInvestmentAmount,
  horizonMonths,
  setHorizonMonths,
  excludedSectors,
  setExcludedSectors,
  maxStockWeight,
  maxSectorWeight,
  userPrompt,
  setUserPrompt,
  loading,
  generationStage,
  onGenerate,
}: PortfolioGeneratorProps) {
  const availableSectors = [
    "Energy & Petrochemicals",
    "Information Technology",
    "Banking & Financial Services",
    "Automotive",
    "Healthcare & Pharmaceuticals",
    "Fast Moving Consumer Goods",
  ];

  const capitalPresets = [100000, 250000, 500000, 1000000];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Left 2 Columns: Input Controls Form */}
      <div className="lg:col-span-2 space-y-6">
        <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E5DF] shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-xl sm:text-2xl font-bold text-[#0C192C] flex items-center gap-2 font-editorial">
              <IconSliders className="w-5 h-5 text-[#15372C]" />
              <span>Create Your Portfolio</span>
            </h2>
            <span className="text-xs px-2.5 py-1 rounded-md bg-[#F0F7F4] border border-[#C8E3D7] text-[#15372C] font-medium">
              Fiduciary Guardrails Active
            </span>
          </div>
          <p className="text-xs text-[#64748B] mb-6">
            Specify your capital, investment horizon, and preferences. Every allocation is mathematically checked against safety limits.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!loading) onGenerate();
            }}
            className="space-y-6"
          >
            {/* Portfolio Name */}
            <div>
              <label htmlFor="portfolio-name-input" className="block text-xs font-bold text-[#475569] uppercase tracking-wider mb-2">
                Portfolio Name
              </label>
              <input
                id="portfolio-name-input"
                type="text"
                value={portfolioName}
                onChange={(e) => setPortfolioName(e.target.value)}
                placeholder="e.g. Core Wealth Compounding Portfolio"
                className="w-full px-4 py-2.5 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF] text-[#0C192C] font-medium focus:bg-white focus:outline-none focus:border-[#0C192C] focus:ring-1 focus:ring-[#0C192C] transition-all text-sm"
              />
            </div>

            {/* Target Capital */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label htmlFor="investment-amount-input" className="text-xs font-bold text-[#475569] uppercase tracking-wider">
                  Target Capital (INR)
                </label>
                <span className="text-lg font-extrabold text-[#166534] tabular-nums">
                  ₹{investmentAmount.toLocaleString("en-IN")}
                </span>
              </div>

              {/* Capital Presets */}
              <div className="flex flex-wrap gap-2 mb-3">
                {capitalPresets.map((amt) => {
                  const isSelected = investmentAmount === amt;
                  const label = `₹${(amt / 100000).toFixed(amt >= 100000 ? 1 : 0)}L`;
                  return (
                    <button
                      key={amt}
                      type="button"
                      onClick={() => setInvestmentAmount(amt)}
                      className={`text-xs px-3.5 py-1.5 rounded-lg border font-semibold transition-all cursor-pointer ${
                        isSelected
                          ? "bg-[#0C192C] text-white border-[#0C192C] shadow-xs"
                          : "bg-[#FAF9F5] border-[#E5E5DF] text-[#475569] hover:border-[#CBD5E1]"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>

              {/* Slider & Input */}
              <div className="space-y-2">
                <input
                  id="investment-amount-input"
                  type="range"
                  min={10000}
                  max={2000000}
                  step={10000}
                  value={investmentAmount}
                  onChange={(e) => setInvestmentAmount(Number(e.target.value))}
                  className="w-full accent-[#0C192C] cursor-pointer"
                />
                <div className="flex justify-between text-xs text-[#64748B]">
                  <span>Min: ₹10,000</span>
                  <span>Max: ₹20,00,000</span>
                </div>
              </div>
            </div>

            {/* Investment Horizon */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label htmlFor="horizon-months-input" className="text-xs font-bold text-[#475569] uppercase tracking-wider">
                  Investment Horizon
                </label>
                <span className="text-sm font-semibold text-[#0C192C] tabular-nums">
                  {(horizonMonths / 12).toFixed(1)} Years ({horizonMonths} Months)
                </span>
              </div>
              <input
                id="horizon-months-input"
                type="range"
                min={12}
                max={120}
                step={6}
                value={horizonMonths}
                onChange={(e) => setHorizonMonths(Number(e.target.value))}
                className="w-full accent-[#0C192C] cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[#64748B]">
                <span>1 Year</span>
                <span>3 Years</span>
                <span>5 Years</span>
                <span>10 Years</span>
              </div>
            </div>

            {/* Sector Exclusions */}
            <div>
              <label className="block text-xs font-bold text-[#475569] uppercase tracking-wider mb-2">
                Sector Exclusions (Ethical &amp; Concentration Filters)
              </label>
              <div className="flex flex-wrap gap-2">
                {availableSectors.map((sec) => {
                  const isExcluded = excludedSectors.includes(sec);
                  return (
                    <button
                      key={sec}
                      type="button"
                      onClick={() => {
                        if (isExcluded) {
                          setExcludedSectors(excludedSectors.filter((s) => s !== sec));
                        } else {
                          setExcludedSectors([...excludedSectors, sec]);
                        }
                      }}
                      className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all cursor-pointer ${
                        isExcluded
                          ? "bg-[#FEF2F2] border-[#FECACA] text-[#B91C1C]"
                          : "bg-[#FAF9F5] border-[#E5E5DF] text-[#475569] hover:border-[#CBD5E1]"
                      }`}
                    >
                      {isExcluded ? (
                        <span className="flex items-center gap-1">
                          <IconX className="w-3 h-3" />
                          <span>{sec} (Excluded)</span>
                        </span>
                      ) : (
                        `+ ${sec}`
                      )}
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-[#64748B] mt-1.5">
                Selected sectors are strictly excluded from the optimization universe before portfolio construction.
              </p>
            </div>

            {/* Guardrail Indicators */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div className="p-4 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF]">
                <div className="text-xs text-[#64748B] font-medium">Max Single Stock Exposure</div>
                <div className="text-lg font-black text-[#0C192C] mt-0.5 tabular-nums">
                  &le; {maxStockWeight.toFixed(1)}%
                </div>
                <p className="text-xs text-[#64748B] mt-0.5">
                  Application concentration safety cap
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF]">
                <div className="text-xs text-[#64748B] font-medium">Max Sector Exposure</div>
                <div className="text-lg font-black text-[#0C192C] mt-0.5 tabular-nums">
                  &le; {maxSectorWeight.toFixed(1)}%
                </div>
                <p className="text-xs text-[#64748B] mt-0.5">
                  Application sector diversification cap
                </p>
              </div>
            </div>

            {/* Investment Strategy Prompt */}
            <div>
              <label htmlFor="strategy-prompt-input" className="block text-xs font-bold text-[#475569] uppercase tracking-wider mb-2">
                Investment Strategy Prompt &bull; Manager Style Calibration
              </label>
              <textarea
                id="strategy-prompt-input"
                rows={2}
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                placeholder="Describe your qualitative preferences or fund manager style guidelines..."
                className="w-full px-4 py-2.5 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF] text-[#0C192C] text-sm focus:bg-white focus:outline-none focus:border-[#0C192C] focus:ring-1 focus:ring-[#0C192C] transition-all"
              />
            </div>

            {/* Primary Action Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 rounded-xl font-bold text-sm sm:text-base bg-[#0C192C] hover:bg-[#1E293B] text-white shadow-md transition-all flex items-center justify-center gap-3 disabled:opacity-60 cursor-pointer"
            >
              {loading ? (
                <>
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  <span>Solving Mathematical Allocation Pipeline...</span>
                </>
              ) : (
                <>
                  <IconShield className="w-5 h-5 text-emerald-400" />
                  <span>Generate Mathematically Validated Portfolio</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Real-time Multi-Stage Progress Banner */}
        {loading && (
          <div className="p-5 rounded-2xl bg-[#F0F7F4] border border-[#C8E3D7] shadow-xs space-y-2">
            <div className="flex items-center gap-3 text-[#15372C] font-semibold text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-[#15372C] animate-ping"></span>
              <span>{generationStage}</span>
            </div>
            <p className="text-xs text-[#15372C]/80 pl-5">
              Analyzing verified fundamentals, optimizing asset balance, and enforcing safety guardrails.
            </p>
          </div>
        )}
      </div>

      {/* Right Column: Fiduciary Safety & Guardrails */}
      <div className="space-y-6">
        <div className="p-6 rounded-2xl bg-white border border-[#E5E5DF] shadow-xs">
          <h3 className="text-base font-bold text-[#0C192C] mb-4 flex items-center gap-2 font-editorial">
            <IconShield className="w-4 h-4 text-[#15372C]" />
            <span>Fiduciary Safety Guardrails</span>
          </h3>
          <ul className="space-y-3.5 text-sm text-[#475569]">
            <li className="flex items-start gap-2.5">
              <span className="w-4 h-4 rounded-full bg-[#F0F7F4] text-[#15372C] flex items-center justify-center flex-shrink-0 mt-0.5">
                <IconCheck className="w-2.5 h-2.5 text-[#15372C]" />
              </span>
              <span>
                <strong className="text-[#0C192C]">Budget Conservation:</strong> Allocations sum to exactly 100% of your investment without hidden borrowing.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="w-4 h-4 rounded-full bg-[#F0FDF4] text-[#15372C] flex items-center justify-center flex-shrink-0 mt-0.5">
                <IconCheck className="w-2.5 h-2.5 text-[#15372C]" />
              </span>
              <span>
                <strong className="text-[#0C192C]">Whole-Share Feasibility:</strong> Rounds purchases to whole shares; preserves unallocated liquidity safely in cash.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="w-4 h-4 rounded-full bg-[#F0F7F4] text-[#15372C] flex items-center justify-center flex-shrink-0 mt-0.5">
                <IconCheck className="w-2.5 h-2.5 text-[#15372C]" />
              </span>
              <span>
                <strong className="text-[#0C192C]">Concentration Caps:</strong> Single-stock exposure capped at &le;25%, sector exposure at &le;40% (aligned with Indian mutual fund prudential limits).
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="w-4 h-4 rounded-full bg-[#F0F7F4] text-[#15372C] flex items-center justify-center flex-shrink-0 mt-0.5">
                <IconCheck className="w-2.5 h-2.5 text-[#15372C]" />
              </span>
              <span>
                <strong className="text-[#0C192C]">Fiduciary Verification:</strong> Every allocation passes independent mathematical verification to ensure your risk boundaries are strictly respected.
              </span>
            </li>
          </ul>
        </div>

        <div className="p-6 rounded-2xl bg-[#F5F4EE] border border-[#E5E5DF]">
          <h3 className="text-base font-bold text-[#0C192C] mb-1 font-editorial">Investment Style &amp; Discipline</h3>
          <p className="text-sm text-[#475569] leading-relaxed">
            Calibrated to emulate disciplined asset allocation across established market leaders, resilient private banking balance sheets, and technological innovators—avoiding low-liquidity penny stocks and speculative plays.
          </p>
        </div>
      </div>
    </div>
  );
}
