"use client";

import React, { useState } from "react";
import { HoldingAllocation } from "../lib/api";

interface AllocationVisualizerProps {
  holdings: HoldingAllocation[];
  totalCapital: number;
}

const PALETTE = [
  "#142A3B", // Deep Navy
  "#166534", // Muted Sage / Emerald
  "#4338CA", // Quantitative Indigo
  "#D97706", // Amber
  "#0D9488", // Teal
  "#B91C1C", // Crimson
  "#4F46E5", // Electric Indigo
  "#0284C7", // Cerulean
  "#7C3AED", // Violet
  "#66758A", // Slate
];

export function AllocationVisualizer({ holdings, totalCapital }: AllocationVisualizerProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!holdings || holdings.length === 0) {
    return null;
  }

  // Group by sector for the sector allocation bar
  const sectorMap: Record<string, number> = {};
  holdings.forEach((h) => {
    const s = h.sector_name || "Diversified";
    sectorMap[s] = (sectorMap[s] || 0) + (h.target_weight_pct || 0);
  });
  const sectors = Object.entries(sectorMap).sort((a, b) => b[1] - a[1]);

  // Compute SVG Donut segments with pure offsets
  const radius = 68;
  const cx = 90;
  const cy = 90;
  const strokeWidth = 24;
  const circumference = 2 * Math.PI * radius;

  // Pre-calculate cumulative angles purely
  const cumulativeAngles: number[] = [];
  let runningAngle = 0;
  for (const h of holdings) {
    cumulativeAngles.push(runningAngle);
    runningAngle += (h.target_weight_pct || 0) / 100;
  }

  const donutSegments = holdings.map((h, i) => {
    const fraction = (h.target_weight_pct || 0) / 100;
    const strokeDasharray = `${fraction * circumference} ${circumference}`;
    const strokeDashoffset = -(cumulativeAngles[i] || 0) * circumference;
    const color = PALETTE[i % PALETTE.length];

    return {
      symbol: h.symbol,
      weight: h.target_weight_pct,
      amount: h.target_amount,
      sector: h.sector_name,
      shares: h.shares_quantity,
      color,
      strokeDasharray,
      strokeDashoffset,
    };
  });

  const activeItem = hoveredIdx !== null ? donutSegments[hoveredIdx] : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 bg-white border border-[#E5E3DA] rounded-2xl p-6 shadow-sm">
      {/* SVG Donut Chart Section */}
      <div className="lg:col-span-5 flex flex-col items-center justify-center p-2">
        <div className="relative w-[180px] h-[180px]">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 180 180">
            <circle
              cx={cx}
              cy={cy}
              r={radius}
              fill="transparent"
              stroke="#EFECE4"
              strokeWidth={strokeWidth}
            />
            {donutSegments.map((seg, idx) => (
              <circle
                key={seg.symbol}
                cx={cx}
                cy={cy}
                r={radius}
                fill="transparent"
                stroke={seg.color}
                strokeWidth={hoveredIdx === idx ? strokeWidth + 4 : strokeWidth}
                strokeDasharray={seg.strokeDasharray}
                strokeDashoffset={seg.strokeDashoffset}
                className="transition-all duration-200 cursor-pointer"
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
              />
            ))}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
            {activeItem ? (
              <>
                <span className="text-xs font-bold text-[#142A3B]">{activeItem.symbol}</span>
                <span className="text-base font-extrabold text-[#166534] tabular-nums">
                  {activeItem.weight.toFixed(1)}%
                </span>
                <span className="text-xs text-[#4A5568]">
                  ₹{Number(activeItem.amount).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </span>
              </>
            ) : (
              <>
                <span className="text-xs font-semibold text-[#66758A] uppercase tracking-wider">
                  Holdings
                </span>
                <span className="text-xl font-extrabold text-[#142A3B] tabular-nums">
                  {holdings.length}
                </span>
                <span className="text-xs text-[#4A5568] font-medium tabular-nums">
                  ₹{Number(totalCapital).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </span>
              </>
            )}
          </div>
        </div>
        <p className="text-xs sm:text-sm text-[#4A5568] mt-3 text-center">
          Hover over donut segments to inspect per-stock target weight
        </p>
      </div>

      {/* Sector Breakdown & Legend Section */}
      <div className="lg:col-span-7 flex flex-col justify-between space-y-5">
        <div>
          <div className="flex justify-between items-center mb-2">
            <h4 className="text-sm font-bold text-[#142A3B] uppercase tracking-wider">
              Sector Exposure vs. 40% Risk Cap
            </h4>
            <span className="text-xs text-[#66758A]">Fiduciary Guardrail: Max 40%</span>
          </div>

          <div className="space-y-2.5">
            {sectors.map(([sector, weight]) => {
              const isHigh = weight > 35;
              return (
                <div key={sector}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-[#0E1E2B]">{sector}</span>
                    <span className="font-semibold text-[#142A3B] tabular-nums">
                      {weight.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-[#EFECE4] overflow-hidden flex">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isHigh ? "bg-amber-600" : "bg-[#142A3B]"
                      }`}
                      style={{ width: `${Math.min(weight, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Legend Badges */}
        <div className="pt-3 border-t border-[#E5E3DA]">
          <div className="flex flex-wrap gap-2">
            {donutSegments.map((seg, idx) => (
              <button
                key={seg.symbol}
                type="button"
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className={`text-xs px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition-all cursor-pointer ${
                  hoveredIdx === idx
                    ? "bg-[#142A3B] text-white border-[#142A3B]"
                    : "bg-[#EFECE4] text-[#0E1E2B] border-[#E5E3DA] hover:border-[#D6D3C8]"
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: seg.color }}
                />
                <span className="font-semibold">{seg.symbol}</span>
                <span className="opacity-80 tabular-nums">{seg.weight.toFixed(1)}%</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
