"use client";

import React from "react";
import { RiskQuestion } from "../lib/api";
import { IconTarget, IconCheck } from "./icons";

interface RiskQuestionnaireViewProps {
  questions: RiskQuestion[];
  selectedAnswers: Record<string, string>;
  setSelectedAnswers: (answers: Record<string, string>) => void;
  loading: boolean;
  onSubmit: () => void;
}

export function RiskQuestionnaireView({
  questions,
  selectedAnswers,
  setSelectedAnswers,
  loading,
  onSubmit,
}: RiskQuestionnaireViewProps) {
  const answeredCount = Object.keys(selectedAnswers).length;
  const totalCount = questions.length;
  const progressPct = totalCount > 0 ? (answeredCount / totalCount) * 100 : 0;
  const isComplete = answeredCount === totalCount && totalCount > 0;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header Panel */}
      <div className="p-6 sm:p-7 rounded-2xl bg-white border border-[#E5E5DF] shadow-sm space-y-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-[#4338CA] uppercase tracking-wider">
            Suitability &amp; Risk Profiling
          </span>
          <span className="text-[#94A3B8]">&bull;</span>
          <span className="text-xs text-[#64748B]">Canonical 5-Tier Taxonomy</span>
        </div>
        <h2 className="text-xl font-bold text-[#0C192C] flex items-center gap-2">
          <IconTarget className="w-5 h-5 text-[#0C192C]" />
          <span>Investor Risk Assessment Questionnaire</span>
        </h2>
        <p className="text-xs sm:text-sm text-[#64748B] leading-relaxed">
          Evaluates your investment horizon, financial loss capacity, and psychological risk tolerance to compute a deterministic risk envelope: Very Conservative, Conservative, Moderate, Growth, or Aggressive.
        </p>

        {/* Progress Bar */}
        <div className="pt-2">
          <div className="flex justify-between items-center text-xs mb-1.5">
            <span className="font-semibold text-[#0C192C]">
              Progress: {answeredCount} of {totalCount} Questions Answered
            </span>
            <span className="font-bold text-[#4338CA] tabular-nums">
              {progressPct.toFixed(0)}%
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-[#FAF9F5] border border-[#E5E5DF] overflow-hidden">
            <div
              className="h-full bg-[#0C192C] rounded-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-6">
        {questions.map((q, idx) => {
          const isAnswered = Boolean(selectedAnswers[q.question_id]);
          return (
            <div
              key={q.question_id}
              className={`p-6 rounded-2xl bg-white border transition-all space-y-3.5 ${
                isAnswered
                  ? "border-[#E5E5DF] shadow-sm"
                  : "border-[#CBD5E1] shadow-xs"
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-[#4338CA] uppercase tracking-wider">
                  Question {idx + 1} of {questions.length}
                </span>
                {isAnswered && (
                  <span className="text-xs font-bold text-[#166534] bg-[#F0FDF4] px-2.5 py-0.5 rounded border border-[#BBF7D0] flex items-center gap-1">
                    <IconCheck className="w-3 h-3 text-[#166534]" />
                    <span>Answered</span>
                  </span>
                )}
              </div>

              <h3 className="text-base font-semibold text-[#0C192C] leading-snug">
                {q.question_text}
              </h3>

              <div className="space-y-2 pt-1">
                {q.options.map((opt) => {
                  const isSelected = selectedAnswers[q.question_id] === opt.option_id;
                  return (
                    <button
                      key={opt.option_id}
                      type="button"
                      onClick={() =>
                        setSelectedAnswers({
                          ...selectedAnswers,
                          [q.question_id]: opt.option_id,
                        })
                      }
                      className={`w-full text-left p-4 rounded-xl border transition-all text-sm flex items-center justify-between cursor-pointer ${
                        isSelected
                          ? "bg-[#FAF9F5] border-[#0C192C] text-[#0C192C] font-semibold ring-1 ring-[#0C192C] shadow-xs"
                          : "bg-white border-[#E5E5DF] text-[#475569] hover:border-[#CBD5E1] hover:bg-[#FAF9F5]"
                      }`}
                    >
                      <span>{opt.option_label}</span>
                      {isSelected ? (
                        <span className="w-5 h-5 rounded-full bg-[#0C192C] text-white flex items-center justify-center flex-shrink-0">
                          <IconCheck className="w-3 h-3 text-white" />
                        </span>
                      ) : (
                        <span className="w-5 h-5 rounded-full border border-[#CBD5E1] flex-shrink-0"></span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Submit Action */}
        <div className="space-y-3">
          <button
            onClick={onSubmit}
            disabled={loading || !isComplete}
            type="button"
            className="w-full py-4 rounded-xl font-bold text-base bg-[#0C192C] hover:bg-[#1E293B] text-white shadow-md transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-3"
          >
            {loading ? (
              <>
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Calculating Deterministic Suitability Score...</span>
              </>
            ) : (
              <>
                <IconTarget className="w-5 h-5 text-emerald-400" />
                <span>Submit Risk Assessment &amp; Calculate Profile</span>
              </>
            )}
          </button>

          {!isComplete && (
            <p className="text-center text-xs text-[#B45309] font-medium">
              Please answer all {totalCount} questions before submitting ({totalCount - answeredCount} remaining).
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
