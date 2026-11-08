"use client";

import React from "react";
import { BRAND } from "../lib/brand";
import { IconSliders, IconTarget, IconLightbulb, IconX } from "./icons";

interface WelcomeWalkthroughProps {
  onDismiss: () => void;
  onGoToOnboarding: () => void;
}

export function WelcomeWalkthrough({
  onDismiss,
  onGoToOnboarding,
}: WelcomeWalkthroughProps) {
  return (
    <div className="bg-white border border-[#E5E5DF] rounded-2xl p-6 sm:p-8 shadow-xs relative transition-all">
      <button
        onClick={onDismiss}
        type="button"
        className="absolute top-6 right-6 text-xs text-[#64748B] hover:text-[#0C192C] font-semibold transition-colors cursor-pointer flex items-center gap-1"
        title="Dismiss welcome guide"
      >
        <span>Dismiss</span>
        <IconX className="w-3.5 h-3.5" />
      </button>

      <div className="max-w-3xl space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[#15372C] uppercase tracking-widest">
            WEALTH / {BRAND.name.toUpperCase()}
          </span>
          <span className="text-[#CBD5E1]">&bull;</span>
          <span className="text-sm text-[#64748B]">Invest with clarity</span>
        </div>

        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-editorial text-[#0C192C] tracking-tight leading-tight">
          Invest with clarity.
        </h1>
        <p className="text-sm sm:text-base text-[#475569] leading-relaxed">
          Your goals. Your portfolio. Understand every choice. Designed for thoughtful investors who want institutional-grade rigor without confusing jargon or opaque black boxes.
        </p>

        <div className="pt-2 flex flex-wrap items-center gap-3">
          <button
            onClick={onGoToOnboarding}
            type="button"
            className="px-5 py-2.5 rounded-xl bg-[#15372C] hover:bg-[#0F2820] text-white font-semibold text-sm transition-all shadow-xs flex items-center gap-2 cursor-pointer"
          >
            <IconTarget className="w-4 h-4" />
            <span>Complete Risk Assessment</span>
          </button>
          <span className="text-sm text-[#64748B]">or configure parameters below</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 mt-6 border-t border-[#F5F4EE]">
        <div className="p-4 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF]/70 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#15372C] uppercase tracking-wide mb-1">
              <IconTarget className="w-3.5 h-3.5" />
              <span>1. Your Goals</span>
            </div>
            <h3 className="text-base font-semibold text-[#0C192C]">Suitability &amp; Risk</h3>
            <p className="text-sm text-[#475569] mt-1 leading-relaxed">
              We evaluate investment horizon, loss tolerance, and financial capacity before suggesting any allocation.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF]/70 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#15372C] uppercase tracking-wide mb-1">
              <IconSliders className="w-3.5 h-3.5" />
              <span>2. Mathematical Rigor</span>
            </div>
            <h3 className="text-base font-semibold text-[#0C192C]">Safe Guardrails</h3>
            <p className="text-sm text-[#475569] mt-1 leading-relaxed">
              Mathematical bounds guarantee single-stock safety (&le;25%) and sector diversification (&le;40%).
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF]/70 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#15372C] uppercase tracking-wide mb-1">
              <IconLightbulb className="w-3.5 h-3.5" />
              <span>3. Grounded Evidence</span>
            </div>
            <h3 className="text-base font-semibold text-[#0C192C]">Auditable Explanations</h3>
            <p className="text-sm text-[#475569] mt-1 leading-relaxed">
              Every company is backed by verified regulatory filings with explicit dates, sources, and whole-share quantities.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
