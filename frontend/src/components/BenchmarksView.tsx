"use client";

import React from "react";
import { BenchmarkComparison } from "../lib/api";
import { IconTrendingUp, IconShield, IconCheck } from "./icons";

interface BenchmarksViewProps {
  benchmarkData: BenchmarkComparison | null;
}

export function BenchmarksView({ benchmarkData }: BenchmarksViewProps) {
  if (!benchmarkData) {
    return (
      <div className="p-12 text-center rounded-2xl bg-white border border-[#E5E3DA] shadow-sm max-w-xl mx-auto my-8">
        <div className="w-12 h-12 rounded-2xl bg-[#F7F6F1] border border-[#E5E3DA] text-[#66758A] flex items-center justify-center mx-auto mb-3">
          <IconTrendingUp className="w-6 h-6 text-[#142A3B]" />
        </div>
        <h3 className="text-lg font-bold text-[#142A3B] mb-2">Loading Benchmark Data...</h3>
        <p className="text-xs text-[#66758A]">
          Fetching 252-day empirical backtest results comparing SLSQP Mean-Variance Optimizer against 1/N and NIFTY 50 baselines.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-[#4338CA] uppercase tracking-wider">
            Quantitative Performance Evaluation
          </span>
          <span className="text-[#94A3B8]">&bull;</span>
          <span className="text-xs text-[#66758A]">252-Day Horizon Empirical Comparison</span>
        </div>
        <h2 className="text-xl font-bold text-[#142A3B] flex items-center gap-2">
          <IconTrendingUp className="w-5 h-5 text-[#142A3B]" />
          <span>Backtesting &amp; Benchmark Comparative Evaluation</span>
        </h2>
        <p className="text-xs sm:text-sm text-[#66758A] mt-1 leading-relaxed">
          Rigorous empirical comparison evaluating the AI Disciplined Quadratic Programming Engine against Equal-Weight (1/N)
          and Market Proxy (NIFTY 50 Proxy) baselines over a 252-day trading horizon.
        </p>
      </div>

      {/* 3 Strategy Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.entries(benchmarkData.strategies).map(([key, strat]) => {
          const isOptimized = key === "optimized";
          return (
            <div
              key={key}
              className={`p-6 rounded-2xl border transition-all flex flex-col justify-between ${
                isOptimized
                  ? "bg-white border-[#142A3B] shadow-md ring-1 ring-[#142A3B]"
                  : "bg-white border-[#E5E3DA] shadow-sm hover:border-[#D6D3C8]"
              }`}
            >
              <div>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-[#142A3B] text-base">{strat.strategy_name}</h3>
                    <span className="text-xs text-[#66758A]">
                      {isOptimized ? "Disciplined Mean-Variance" : "Comparative Benchmark"}
                    </span>
                  </div>
                  {isOptimized && (
                    <span className="text-xs uppercase font-bold px-2.5 py-0.5 rounded-full bg-[#F0FDF4] text-[#166534] border border-[#BBF7D0]">
                      SLSQP Optimizer
                    </span>
                  )}
                </div>

                <div className="space-y-3 pt-2">
                  <div className="flex justify-between items-center text-xs pb-2 border-b border-[#EFECE4]">
                    <span className="text-[#66758A]">Annualized Return:</span>
                    <span className="font-extrabold text-[#166534] tabular-nums text-sm">
                      {strat.annualized_return_pct.toFixed(2)}%
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-xs pb-2 border-b border-[#EFECE4]">
                    <span className="text-[#66758A]">Annualized Volatility:</span>
                    <span className="font-bold text-[#B45309] tabular-nums text-sm">
                      {strat.annualized_volatility_pct.toFixed(2)}%
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-xs pb-2 border-b border-[#EFECE4]">
                    <span className="text-[#66758A]">Sharpe Ratio (7% Rf):</span>
                    <span className="font-extrabold text-[#142A3B] tabular-nums text-sm">
                      {strat.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-xs pb-2 border-b border-[#EFECE4]">
                    <span className="text-[#66758A]">Max Drawdown:</span>
                    <span className="font-bold text-[#B91C1C] tabular-nums text-sm">
                      -{strat.max_drawdown_pct.toFixed(2)}%
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#66758A]">Diversification Score:</span>
                    <span className="font-bold text-[#4338CA] tabular-nums text-sm">
                      {strat.diversification_score}/100
                    </span>
                  </div>
                </div>
              </div>

              {isOptimized && (
                <div className="mt-5 pt-3 border-t border-[#EFECE4] text-xs text-[#166534] font-semibold flex items-center gap-1.5">
                  <IconShield className="w-3.5 h-3.5" />
                  <span>Enforces &le;25% stock &amp; &le;40% sector caps</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Academic Evaluation Findings */}
      <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E3DA] shadow-sm space-y-3">
        <h3 className="font-bold text-[#142A3B] text-base flex items-center gap-2">
          <IconShield className="w-4 h-4 text-[#166534]" />
          <span>Academic Evaluation Findings &amp; Insights:</span>
        </h3>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-[#4A5568] pt-1">
          {benchmarkData.key_findings.map((f, i) => (
            <li key={i} className="flex items-start gap-2.5 p-3 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]">
              <span className="w-4 h-4 rounded-full bg-[#F0FDF4] text-[#166534] flex items-center justify-center flex-shrink-0 mt-0.5">
                <IconCheck className="w-2.5 h-2.5 text-[#166534]" />
              </span>
              <span className="leading-relaxed">{f}</span>
            </li>
          ))}
        </ul>

        {/* Methodology Notes */}
        <div className="pt-3 border-t border-[#E5E3DA] text-xs text-[#4A5568] space-y-1">
          <p>
            <strong className="text-[#142A3B]">Methodology &amp; Assumptions:</strong> {benchmarkData.methodology_notes}
          </p>
          <p className="text-xs text-[#66758A]">
            Historical performance is simulated using adjusted daily closing prices and does not guarantee future investment returns.
          </p>
        </div>
      </div>
    </div>
  );
}
