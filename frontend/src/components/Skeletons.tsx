"use client";

import React from "react";

export function MetricCardSkeleton() {
  return (
    <div className="p-5 rounded-2xl bg-white border border-[#E5E5DF] shadow-xs space-y-3 animate-pulse">
      <div className="h-3 w-28 bg-[#F5F4EE] rounded"></div>
      <div className="h-8 w-24 bg-[#ECEAE2] rounded"></div>
      <div className="h-3 w-36 bg-[#F5F4EE] rounded"></div>
    </div>
  );
}

export function HoldingsTableSkeleton() {
  return (
    <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E5DF] shadow-xs space-y-4 animate-pulse">
      <div className="flex justify-between items-center pb-3 border-b border-[#F5F4EE]">
        <div className="h-5 w-48 bg-[#ECEAE2] rounded"></div>
        <div className="h-4 w-24 bg-[#F5F4EE] rounded"></div>
      </div>
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex justify-between items-center py-2.5 border-b border-[#FAF9F5]">
            <div className="space-y-1">
              <div className="h-4 w-32 bg-[#ECEAE2] rounded"></div>
              <div className="h-3 w-20 bg-[#F5F4EE] rounded"></div>
            </div>
            <div className="flex gap-6">
              <div className="h-4 w-12 bg-[#F5F4EE] rounded"></div>
              <div className="h-4 w-16 bg-[#F5F4EE] rounded"></div>
              <div className="h-4 w-20 bg-[#ECEAE2] rounded"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ExplainabilitySkeleton() {
  return (
    <div className="p-6 sm:p-8 rounded-2xl bg-white border border-[#E5E5DF] shadow-xs space-y-6 animate-pulse">
      <div className="space-y-2">
        <div className="h-3 w-32 bg-[#F5F4EE] rounded"></div>
        <div className="h-7 w-64 bg-[#ECEAE2] rounded"></div>
        <div className="h-4 w-96 bg-[#F5F4EE] rounded"></div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 pt-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-3 rounded-xl border border-[#E5E5DF] bg-[#FAF9F5] h-16"></div>
        ))}
      </div>
      <div className="p-5 rounded-xl bg-[#FAF9F5] border border-[#E5E5DF] space-y-3">
        <div className="h-4 w-40 bg-[#ECEAE2] rounded"></div>
        <div className="h-3 w-full bg-[#F5F4EE] rounded"></div>
        <div className="h-3 w-4/5 bg-[#F5F4EE] rounded"></div>
      </div>
    </div>
  );
}
