"use client";

import React from "react";
import { BRAND } from "../lib/brand";
import {
  IconShield,
  IconChartBar,
  IconLightbulb,
  IconArrowUpRight,
  IconCheck,
  IconTrendingUp,
  IconTarget,
  IconDownload,
  IconBolt,
} from "./icons";
import { PortfolioVersion } from "../lib/api";

interface LandingPageProps {
  onGetStarted: () => void;
  onLogin: () => void;
  onDemoLogin: () => void;
  existingPortfolio: PortfolioVersion | null;
  onViewExistingPortfolio: () => void;
  isAuthenticated: boolean;
  isLoading?: boolean;
}

export function LandingPage({
  onGetStarted,
  onLogin,
  onDemoLogin,
  existingPortfolio,
  onViewExistingPortfolio,
  isAuthenticated,
  isLoading = false,
}: LandingPageProps) {
  // Sample demonstration data for visual preview
  const sampleHoldings = [
    {
      symbol: "RELIANCE",
      name: "Reliance Industries",
      sector: "Energy & Conglomerate",
      weight: 18.2,
      shares: 16,
      price: 2840,
      amount: 45440,
      reason: "Cash-flow powerhouse with dominant digital and retail growth engines.",
    },
    {
      symbol: "HDFCBANK",
      name: "HDFC Bank",
      sector: "Private Banking",
      weight: 22.0,
      shares: 32,
      price: 1718,
      amount: 54976,
      reason: "Premier Indian private lender with conservative underwriting and retail reach.",
    },
    {
      symbol: "TCS",
      name: "Tata Consultancy Services",
      sector: "Information Tech",
      weight: 16.0,
      shares: 11,
      price: 3636,
      amount: 39996,
      reason: "High return-on-equity exporter generating sustained dollar dividends.",
    },
    {
      symbol: "LT",
      name: "Larsen & Toubro",
      sector: "Capital Goods & Infra",
      weight: 15.0,
      shares: 10,
      price: 3750,
      amount: 37500,
      reason: "National infrastructure proxy with robust domestic and Middle East order books.",
    },
    {
      symbol: "SUNPHARMA",
      name: "Sun Pharmaceutical",
      sector: "Healthcare",
      weight: 16.0,
      shares: 24,
      price: 1666,
      amount: 39984,
      reason: "Defensive healthcare leader providing low correlation to economic downturns.",
    },
  ];

  return (
    <div className="space-y-16 lg:space-y-24 py-2">
      {/* Existing Portfolio Banner ONLY if user is confirmed authenticated and portfolio exists */}
      {isAuthenticated && existingPortfolio && (
        <div className="p-4 sm:p-5 rounded-2xl bg-[#ECF3F0] border border-[#C6D8D1] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#285C4D] text-white flex items-center justify-center font-bold">
              <IconCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                Active Portfolio Ready
              </p>
              <h4 className="text-sm sm:text-base font-bold text-[#142A3B]">
                You have a generated portfolio of ₹{Number(existingPortfolio.investment_amount).toLocaleString("en-IN")} ({existingPortfolio.risk_category.replace("_", " ")}).
              </h4>
            </div>
          </div>
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={onViewExistingPortfolio}
              type="button"
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center gap-1.5"
            >
              <span>View My Portfolio</span>
              <IconArrowUpRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onGetStarted}
              type="button"
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-white hover:bg-[#F7F6F1] border border-[#E5E3DA] text-[#142A3B] text-xs font-bold transition-all cursor-pointer"
            >
              Create New
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SECTION 1: WIDE BALANCED HERO SECTION (2-COLUMN GRID ON DESKTOP)          */}
      {/* ========================================================================= */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center pt-2 sm:pt-6">
        {/* Left Column (Content & CTAs) */}
        <div className="lg:col-span-6 xl:col-span-6 space-y-6 text-left">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EFECE4] border border-[#E5E3DA] text-xs font-medium text-[#4A5568]">
            <span className="w-2 h-2 rounded-full bg-[#285C4D]"></span>
            <span>Engineered for Indian Retail Investors</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-editorial tracking-tight text-[#142A3B] leading-[1.12]">
            Disciplined stock portfolios, <br />
            <span className="italic font-normal">made simple and personal.</span>
          </h1>

          <p className="text-base sm:text-lg text-[#4A5568] leading-relaxed max-w-xl">
            Tell us your goals and comfort with risk — our intelligent engine calculates balanced, whole-share Indian stock portfolios with transparent, plain-English reasons for every rupee allocated.
          </p>

          {/* Primary & Secondary Call to Actions */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5 pt-2">
            <button
              onClick={onGetStarted}
              type="button"
              className="px-7 py-3.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-sm font-bold transition-all shadow-sm hover:shadow-md cursor-pointer flex items-center justify-center gap-2"
            >
              <span>{isAuthenticated ? "Build a Portfolio" : "Get Started Free"}</span>
              <IconArrowUpRight className="w-4 h-4 text-white" />
            </button>

            {!isAuthenticated && (
              <button
                onClick={onDemoLogin}
                disabled={isLoading}
                type="button"
                className="px-6 py-3.5 rounded-xl bg-white hover:bg-[#F7F6F1] border border-[#E5E3DA] text-[#142A3B] text-sm font-bold transition-all shadow-2xs cursor-pointer flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {isLoading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-[#142A3B]/30 border-t-[#142A3B] rounded-full animate-spin"></span>
                    <span>Loading Demo...</span>
                  </>
                ) : (
                  <span className="flex items-center gap-1.5">
                    <IconBolt className="w-4 h-4 text-[#142A3B]" />
                    <span>Try as Demo Investor</span>
                  </span>
                )}
              </button>
            )}

            {!isAuthenticated && (
              <button
                onClick={onLogin}
                type="button"
                className="px-4 py-3.5 rounded-xl text-[#4A5568] hover:text-[#142A3B] text-sm font-semibold transition-colors cursor-pointer text-center"
              >
                Have an account? <span className="underline font-bold text-[#142A3B]">Log In</span>
              </button>
            )}
          </div>

          {/* Trust Badges - 2x2 Grid */}
          <div className="pt-4 grid grid-cols-2 gap-3 max-w-xl">
            <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] flex items-center gap-2.5 shadow-2xs">
              <div className="w-8 h-8 rounded-lg bg-[#ECF3F0] text-[#285C4D] flex items-center justify-center flex-shrink-0">
                <IconShield className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-bold text-[#142A3B]">Non-Custodial</div>
                <div className="text-xs text-[#4A5568]">Your funds stay in your broker</div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] flex items-center gap-2.5 shadow-2xs">
              <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] text-[#1D4ED8] flex items-center justify-center flex-shrink-0">
                <IconCheck className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-bold text-[#142A3B]">100% Whole Shares</div>
                <div className="text-xs text-[#4A5568]">Zero fractional share errors</div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] flex items-center gap-2.5 shadow-2xs">
              <div className="w-8 h-8 rounded-lg bg-[#FDF8ED] text-[#9A6014] flex items-center justify-center flex-shrink-0">
                <IconLightbulb className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-bold text-[#142A3B]">Transparent Investment Thesis</div>
                <div className="text-xs text-[#4A5568]">Fundamental rationale for every holding</div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-[#E5E3DA] flex items-center gap-2.5 shadow-2xs">
              <div className="w-8 h-8 rounded-lg bg-[#FAF5FF] text-[#7E22CE] flex items-center justify-center flex-shrink-0">
                <IconDownload className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-bold text-[#142A3B]">Zerodha / Groww Export</div>
                <div className="text-xs text-[#4A5568]">1-click order basket export</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Visual Showcase Card */}
        <div className="lg:col-span-6 xl:col-span-6">
          <div className="bg-white rounded-2xl border border-[#E5E3DA] shadow-sm overflow-hidden">
            {/* Header metrics */}
            <div className="p-5 sm:p-6 bg-[#F7F6F1] border-b border-[#E5E3DA]">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-[#285C4D] text-white">
                    EXAMPLE
                  </span>
                  <span className="text-sm font-bold text-[#142A3B]">Balanced Compounding Portfolio</span>
                  <span className="text-sm text-[#4A5568]">&bull; Moderate Risk</span>
                </div>
                <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                  REALISTIC ALLOCATION PREVIEW
                </span>
              </div>

              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <div className="text-xs text-[#4A5568] font-medium">Total Capital Allocated</div>
                  <div className="text-2xl sm:text-3xl font-bold text-[#142A3B] tabular-nums font-editorial">
                    ₹2,50,000
                  </div>
                </div>

                <div className="flex items-center gap-5">
                  <div className="text-right">
                    <div className="text-xs text-[#4A5568] font-medium">Expected Return</div>
                    <div className="text-lg sm:text-xl font-bold text-[#285C4D] tabular-nums">
                      14.8% <span className="text-xs text-[#66758A] font-normal">CAGR</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-[#4A5568] font-medium">Expected Volatility</div>
                    <div className="text-lg sm:text-xl font-bold text-[#142A3B] tabular-nums">
                      12.4% <span className="text-xs text-[#66758A] font-normal">ann.</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-[#4A5568] font-medium">Diversification</div>
                    <div className="text-lg sm:text-xl font-bold text-[#142A3B] tabular-nums">
                      88 <span className="text-xs text-[#66758A] font-normal">/ 100</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Holdings List */}
            <div className="divide-y divide-[#EFECE4] max-h-[380px] overflow-y-auto">
              {sampleHoldings.map((h) => (
                <div key={h.symbol} className="p-4 sm:p-4.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#F7F6F1]/70 transition-colors">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-black text-[#142A3B] tracking-wide font-mono">
                        {h.symbol}
                      </span>
                      <span className="text-sm font-semibold text-[#142A3B]">
                        {h.name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-[#EFECE4] text-[#4A5568]">
                        {h.sector}
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-[#4A5568] leading-relaxed flex items-start gap-1.5">
                      <IconLightbulb className="w-3.5 h-3.5 text-[#285C4D] shrink-0 mt-0.5" />
                      <span>{h.reason}</span>
                    </p>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-5 flex-shrink-0 pt-1 sm:pt-0 border-t sm:border-t-0 border-[#EFECE4]">
                    <div className="text-left sm:text-right">
                      <div className="text-sm font-bold text-[#142A3B] tabular-nums">
                        {h.shares} Shares
                      </div>
                      <div className="text-xs text-[#4A5568] tabular-nums font-medium">
                        @ ₹{h.price.toLocaleString("en-IN")}
                      </div>
                    </div>
                    <div className="text-right min-w-[90px]">
                      <div className="text-sm font-bold text-[#142A3B] tabular-nums">
                        ₹{h.amount.toLocaleString("en-IN")}
                      </div>
                      <div className="text-xs text-[#285C4D] font-bold tabular-nums">
                        {h.weight}% weight
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Whole-Share Cash Reserve Card */}
              <div className="p-4 sm:p-4.5 bg-[#ECF3F0]/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#C6D8D1] text-[#285C4D] flex items-center justify-center font-bold text-sm flex-shrink-0 mt-0.5">
                    ₹
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-[#285C4D]">
                        Liquid Cash Reserve: ₹7,904 (3.2%)
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-[#C6D8D1] text-[#285C4D]">
                        NSE/BSE Whole Share Rule
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-[#334155] mt-1 leading-relaxed">
                      Calibrated for whole-share lot sizes — keeping unallocated cash safely uninvested so you never exceed your target budget.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Footer */}
            <div className="p-4 bg-white border-t border-[#E5E3DA] flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
              <span className="text-[#4A5568] font-medium">
                Ready to generate your own personalized equity basket?
              </span>
              <button
                onClick={onGetStarted}
                type="button"
                className="px-4 py-2 rounded-lg bg-[#142A3B] hover:bg-[#0E1E2B] text-white font-bold transition-colors cursor-pointer text-sm"
              >
                Start Your Onboarding →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 2: 3-STEP JOURNEY (EXPANSIVE 3-COLUMN DESKTOP GRID)                */}
      {/* ========================================================================= */}
      <section className="space-y-8 pt-4">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
            A CLEARER WAY TO BUILD YOUR PORTFOLIO
          </span>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-editorial text-[#142A3B]">
            How {BRAND.name} works for you
          </h2>
          <p className="text-sm sm:text-base text-[#4A5568] leading-relaxed">
            From your initial budget to a ready-to-execute stock list in three simple steps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {/* Step 1 */}
          <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-2xs space-y-3.5 relative hover:border-[#D6D3C8] transition-all card-interactive">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-[#142A3B] text-white flex items-center justify-center font-bold text-sm">
                01
              </div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                Share Goals &amp; Risk Comfort
              </span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-[#142A3B]">
              Tell us your goals and risk preferences
            </h3>
            <p className="text-sm text-[#4A5568] leading-relaxed">
              Answer a few clear questions about your timeline, capital, and comfort with market swings. We assess both your financial capacity and psychological risk tolerance.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-2xs space-y-3.5 relative hover:border-[#D6D3C8] transition-all card-interactive">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-[#285C4D] text-white flex items-center justify-center font-bold text-sm">
                02
              </div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                Intelligent Optimization
              </span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-[#142A3B]">
              Build a portfolio around your needs
            </h3>
            <p className="text-sm text-[#4A5568] leading-relaxed">
              Our algorithms analyze balance sheet fundamentals, filter out unwanted sectors, and calculate the exact number of whole shares needed to maximize your risk-adjusted return.
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-2xs space-y-3.5 relative hover:border-[#D6D3C8] transition-all card-interactive">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-[#1E3A5F] text-white flex items-center justify-center font-bold text-sm">
                03
              </div>
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                Execute with Conviction
              </span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-[#142A3B]">
              Review your portfolio recommendation
            </h3>
            <p className="text-sm text-[#4A5568] leading-relaxed">
              Review a clear shopping list with plain-English reasons for every stock. Export the order basket directly into Zerodha, Groww, or your preferred Indian broker with one click.
            </p>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 3: PORTFOLIO RULES & CONSTRAINTS (4-COLUMN RESPONSIVE GRID)       */}
      {/* ========================================================================= */}
      <section className="p-6 sm:p-10 rounded-2xl bg-white border border-[#E5E3DA] shadow-2xs space-y-8">
        <div className="max-w-2xl">
          <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
            PORTFOLIO CONSTRAINTS &amp; SAFETY
          </span>
          <h2 className="text-2xl sm:text-3xl font-editorial text-[#142A3B] mt-1">
            Every recommendation is checked against defined portfolio constraints
          </h2>
          <p className="text-sm text-[#4A5568] mt-1.5 leading-relaxed">
            Institutional-style risk rules help ensure your portfolio remains diversified and disciplined against single-stock shocks.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2 card-interactive">
            <div className="text-sm font-bold text-[#142A3B] flex items-center gap-2">
              <IconShield className="w-4 h-4 text-[#285C4D] shrink-0" />
              <span>Maximum 25% Single Stock Cap</span>
            </div>
            <p className="text-sm text-[#4A5568] leading-relaxed">
              No single company can dominate your portfolio, protecting your capital from individual corporate failures.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2 card-interactive">
            <div className="text-sm font-bold text-[#142A3B] flex items-center gap-2">
              <IconShield className="w-4 h-4 text-[#285C4D] shrink-0" />
              <span>Maximum 40% Sector Concentration Cap</span>
            </div>
            <p className="text-sm text-[#4A5568] leading-relaxed">
              Your money is never overly exposed to a single industry slump (such as an IT slowdown or commodity cycle).
            </p>
          </div>

          <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2 card-interactive">
            <div className="text-sm font-bold text-[#142A3B] flex items-center gap-2">
              <IconCheck className="w-4 h-4 text-[#285C4D] shrink-0" />
              <span>Whole-Share Integer Arithmetic</span>
            </div>
            <p className="text-sm text-[#4A5568] leading-relaxed">
              Unlike theoretical calculators that recommend fractions (e.g. 14.3 shares), our solver only generates integer shares executable on NSE/BSE.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-2 card-interactive">
            <div className="text-sm font-bold text-[#142A3B] flex items-center gap-2">
              <IconTrendingUp className="w-4 h-4 text-[#285C4D] shrink-0" />
              <span>Real-Time Stress Testing</span>
            </div>
            <p className="text-sm text-[#4A5568] leading-relaxed">
              Simulate historical market shocks like the 2020 Covid Crash and Oil Shocks before you invest a single rupee.
            </p>
          </div>
        </div>

        <div className="pt-2 text-center">
          <button
            onClick={onGetStarted}
            type="button"
            className="px-8 py-3.5 rounded-xl bg-[#142A3B] hover:bg-[#0E1E2B] text-white text-sm font-bold transition-all shadow-xs hover:shadow-sm cursor-pointer"
          >
            Get started
          </button>
        </div>
      </section>
    </div>
  );
}
