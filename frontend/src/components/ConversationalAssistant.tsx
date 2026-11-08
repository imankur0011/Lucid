"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  PortfolioVersion,
  chatWithPortfolioAssistant,
  chatWithGeneralAssistant,
  ScenarioSimulationDetail,
  ChatHistoryMessage,
} from "../lib/api";
import {
  IconBolt,
  IconLightbulb,
  IconCheck,
  IconRefresh,
  IconX,
  IconArrowUpRight,
  IconSparkles,
} from "./icons";

interface MessageItem {
  id: string;
  sender: "user" | "assistant";
  text: string;
  simulation?: ScenarioSimulationDetail | null;
  followups?: string[];
  timestamp: string;
}

interface ConversationalAssistantProps {
  portfolio: PortfolioVersion | null;
  initialQuery?: string | null;
  existingPortfolioId?: string | null;
}

/**
 * Parses markdown-like text (bold, tables, subheaders, lists, ratios) into rich accessible UI elements.
 */
function FormattedAssistantMessage({ text }: { text: string }) {
  const paragraphs = text.split("\n\n").filter((p) => p.trim().length > 0);

  return (
    <div className="space-y-3 text-sm leading-relaxed text-[#142A3B]">
      {paragraphs.map((para, pIdx) => {
        const trimmedPara = para.trim();

        // Check if paragraph is a subheader (### Heading or ## Heading)
        if (trimmedPara.startsWith("### ")) {
          return (
            <h3 key={pIdx} className="text-sm font-bold text-[#142A3B] pt-2 pb-1 border-b border-[#E5E3DA]/80 flex items-center gap-1.5">
              {renderFormattedInline(trimmedPara.replace(/^###\s+/, ""))}
            </h3>
          );
        }
        if (trimmedPara.startsWith("## ")) {
          return (
            <h2 key={pIdx} className="text-base font-extrabold text-[#142A3B] pt-3 pb-1.5 border-b border-[#E5E3DA] flex items-center gap-1.5">
              {renderFormattedInline(trimmedPara.replace(/^##\s+/, ""))}
            </h2>
          );
        }

        const lines = para.split("\n").filter((l) => l.trim().length > 0);

        // Check if paragraph is a markdown table
        const tableLines = lines.filter((l) => l.trim().startsWith("|") && l.trim().endsWith("|"));
        if (tableLines.length >= 2) {
          const headerLine = tableLines[0];
          const headerCells = headerLine
            .split("|")
            .slice(1, -1)
            .map((c) => c.trim());
          const bodyLines = tableLines.slice(1).filter((l) => !/^[\|\s:\-]+$/.test(l.trim()));
          const bodyRows = bodyLines.map((l) =>
            l
              .split("|")
              .slice(1, -1)
              .map((c) => c.trim())
          );

          return (
            <div key={pIdx} className="overflow-x-auto my-3 rounded-xl border border-[#E5E3DA] shadow-2xs">
              <table className="w-full text-left text-xs bg-white">
                <thead className="bg-[#F7F6F1] text-[#66758A] uppercase text-[10px] font-bold border-b border-[#E5E3DA]">
                  <tr>
                    {headerCells.map((cell, cIdx) => (
                      <th key={cIdx} className="py-2.5 px-3 whitespace-nowrap font-bold text-[#142A3B]">
                        {renderFormattedInline(cell)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E3DA] text-[#142A3B]">
                  {bodyRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-[#F7F6F1]/60 transition-colors">
                      {row.map((cell, cIdx) => (
                        <td key={cIdx} className="py-2.5 px-3 text-xs">
                          {renderFormattedInline(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        // Check if paragraph is a numbered list (e.g. 1. Strategic Role...)
        const isNumberedList = lines.every((l) => /^\d+\.\s+/.test(l.trim()));
        if (isNumberedList) {
          return (
            <div key={pIdx} className="space-y-2 pt-1">
              {lines.map((line, lIdx) => {
                const match = line.match(/^(\d+)\.\s+(.*)$/);
                const num = match ? match[1] : `${lIdx + 1}`;
                const content = match ? match[2] : line;
                return (
                  <div
                    key={lIdx}
                    className="flex items-start gap-2.5 p-2.5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA]/80"
                  >
                    <span className="w-5 h-5 rounded-full bg-[#285C4D] text-white flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                      {num}
                    </span>
                    <div className="text-xs sm:text-sm text-[#142A3B] leading-relaxed">
                      {renderFormattedInline(content)}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        }

        // Check if paragraph is bullet points
        const isBulletList = lines.every((l) => /^([•\-\*])\s+/.test(l.trim()));
        if (isBulletList) {
          return (
            <ul key={pIdx} className="space-y-1.5 pl-1 pt-1">
              {lines.map((line, lIdx) => {
                const content = line.replace(/^([•\-\*])\s+/, "");
                return (
                  <li key={lIdx} className="flex items-start gap-2 text-xs sm:text-sm text-[#142A3B]">
                    <span className="text-[#285C4D] font-bold text-base leading-none select-none">•</span>
                    <span className="leading-relaxed">{renderFormattedInline(content)}</span>
                  </li>
                );
              })}
            </ul>
          );
        }

        // Standard paragraph
        return (
          <p key={pIdx} className="text-xs sm:text-sm text-[#142A3B] leading-relaxed">
            {renderFormattedInline(para)}
          </p>
        );
      })}
    </div>
  );
}

/**
 * Formats inline bold (**text**) and code (`ticker`).
 */
function renderFormattedInline(raw: string) {
  const parts = raw.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      const inner = part.slice(2, -2);
      return (
        <strong key={idx} className="font-bold text-[#142A3B]">
          {inner}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      const inner = part.slice(1, -1);
      return (
        <code key={idx} className="px-1.5 py-0.5 rounded bg-[#EFECE4] text-[#142A3B] font-mono text-[11px] font-semibold border border-[#E5E3DA]">
          {inner}
        </code>
      );
    }
    return <span key={idx}>{part}</span>;
  });
}

export function ConversationalAssistant({ portfolio, initialQuery, existingPortfolioId }: ConversationalAssistantProps) {
  const stock1 = portfolio?.holdings?.[0]?.symbol || "Reliance";
  const stock2 = portfolio?.holdings?.[1]?.symbol || "TCS";
  const stock3 = portfolio?.holdings?.[2]?.symbol || "HDFC Bank";

  const [sessionId, setSessionId] = useState<string>("sess_init");

  useEffect(() => {
    setSessionId(`sess_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`);
  }, []);

  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: "initial-msg",
      sender: "assistant",
      text:
        "Welcome to Lucid! I am your AI Fiduciary Copilot.\n\n" +
        "You can ask me anything about your stock allocations, explore how direct stocks compare to mutual funds, " +
        "learn about diversification, or simulate what-if macro stress tests (e.g. 'What happens in a 30% COVID crash?').",
      timestamp: "Just now",
      followups: [
        `Why did you recommend ${stock1}?`,
        "What is the difference between a stock and a mutual fund?",
        "What happens if the market crashes 30% like in March 2020?",
        "Explain how diversification protects my capital.",
      ],
    },
  ]);

  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const lastInitialQueryRef = useRef<string | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Smooth auto-scroll that handles both internal scroll container and page view
  const scrollToBottom = useCallback((smooth = true) => {
    const behavior = smooth ? "smooth" : "auto";
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: behavior as ScrollBehavior,
      });
    }
    // Also scroll message end gently into view so outer window follows
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: behavior as ScrollBehavior,
        block: "nearest",
      });
    }
  }, []);

  // Trigger auto-scroll when messages change or loading state toggles
  useEffect(() => {
    const timer1 = setTimeout(() => scrollToBottom(true), 50);
    const timer2 = setTimeout(() => scrollToBottom(true), 250);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, [messages, loading, scrollToBottom]);

  // Track scroll position to show floating 'Jump to bottom' pill if user scrolls up
  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 120;
    setShowScrollBottom(!isNearBottom);
  };

  const handleSend = useCallback(
    async (queryToSend?: string) => {
      const q = (queryToSend || inputQuery).trim();
      if (!q || loading) return;

      const userMsg: MessageItem = {
        id: `user-${Date.now()}`,
        sender: "user",
        text: q,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInputQuery("");
      setLoading(true);

      // Scroll immediately when user sends
      setTimeout(() => scrollToBottom(true), 30);

      // Extract conversation history for multi-turn context
      const history: ChatHistoryMessage[] = messages
        .filter((m) => m.id !== "initial-msg" && !m.id.startsWith("init-"))
        .map((m) => ({ role: m.sender, content: m.text }));

      try {
        let res: { reply: string; scenario_simulation?: ScenarioSimulationDetail | null; suggested_followups: string[] };
        if (portfolio?.portfolio_id) {
          try {
            res = await chatWithPortfolioAssistant(
              portfolio.portfolio_id,
              q,
              history,
              sessionId
            );
          } catch {
            // Gracefully fall back to universal assistant endpoint
            res = await chatWithGeneralAssistant(
              q,
              history,
              sessionId,
              portfolio.portfolio_id,
              existingPortfolioId || undefined
            );
          }
        } else {
          res = await chatWithGeneralAssistant(
            q,
            history,
            sessionId,
            undefined,
            existingPortfolioId || undefined
          );
        }
        const assistantMsg: MessageItem = {
          id: `assistant-${Date.now()}-${Math.random()}`,
          sender: "assistant",
          text: res.reply,
          simulation: res.scenario_simulation,
          followups: res.suggested_followups,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : "Failed to communicate with assistant";
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: "assistant",
            text: `I encountered an issue analyzing that request: ${errMsg}. Please verify your portfolio connection and try asking again.`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
      } finally {
        setLoading(false);
        setTimeout(() => scrollToBottom(true), 60);
      }
    },
    [inputQuery, portfolio, loading, scrollToBottom, messages, sessionId]
  );

  // Handle external stock-click triggers
  useEffect(() => {
    if (initialQuery && initialQuery.trim() && initialQuery !== lastInitialQueryRef.current) {
      lastInitialQueryRef.current = initialQuery;
      handleSend(initialQuery);
    }
  }, [initialQuery, handleSend]);

  const handleCopyText = (id: string, text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const handleResetChat = () => {
    const newSess = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    setSessionId(newSess);
    setMessages([
      {
        id: `init-${Date.now()}`,
        sender: "assistant",
        text:
          "Conversation restarted. Ask any question about your stock allocation, sector caps, or downside stress testing.",
        timestamp: "Just now",
        followups: [
          `Why did you recommend ${stock1}?`,
          "What is the difference between a stock and a mutual fund?",
          "What happens if the market crashes 30%?",
          "Explain how diversification protects my capital.",
        ],
      },
    ]);
    setInputQuery("");
  };

  if (!portfolio) {
    return (
      <div className="p-8 text-center rounded-2xl bg-white border border-[#E5E3DA] text-xs text-[#66758A]">
        Please generate a portfolio first to enable the interactive conversational assistant.
      </div>
    );
  }

  // Curated quick chips for 1-tap questions
  const quickPills = [
    { label: `Why ${stock1}?`, query: `Why did you recommend ${stock1}?` },
    { label: "Stock vs Mutual Fund", query: "What is the difference between a stock and a mutual fund?" },
    { label: "COVID Crash (-30%)", query: "What happens if the market crashes 30% like in March 2020?" },
    { label: "Crude Oil $100", query: "What if crude oil spikes to $100/barrel?" },
    { label: "RBI Rate Hike", query: "What happens if RBI hikes interest rates by 100 bps?" },
    { label: "Explain Diversification", query: "Explain what diversification means and how Lucid caps risk." },
    { label: "Sector Caps Rule", query: "Explain Lucid's 40% sector cap risk policy and how it protects me." },
  ];

  return (
    <div className="rounded-2xl bg-white border border-[#E5E3DA] shadow-xs overflow-hidden flex flex-col h-[680px] sm:h-[720px] transition-all relative">
      {/* Header Bar */}
      <div className="px-5 py-4 border-b border-[#E5E3DA] bg-[#F7F6F1] flex justify-between items-center flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#142A3B] text-white flex items-center justify-center font-bold text-sm shadow-xs border border-[#285C4D]">
            <IconSparkles className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wider">
                Lucid AI Copilot
              </span>
              <span className="text-[#D6D3C8]">&bull;</span>
              <span className="text-xs font-semibold text-[#4A5568]">Fiduciary Equities Advisor</span>
            </div>
            <h2 className="text-base sm:text-lg font-bold text-[#142A3B] font-editorial">
              Ask Lucid &bull; Conversational Stress Testing
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-lg bg-[#ECF3F0] text-[#285C4D] border border-[#C6D8D1] font-bold">
            v#{portfolio.version_number} Portfolio
          </span>
          <button
            onClick={handleResetChat}
            type="button"
            title="Reset conversation"
            className="p-1.5 rounded-lg border border-[#D6D3C8] bg-white text-[#66758A] hover:text-[#142A3B] hover:border-[#142A3B] transition-all cursor-pointer"
          >
            <IconRefresh className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Message Stream */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-[#F7F6F1]/50 scroll-smooth"
      >
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-2xl p-4 sm:p-5 rounded-2xl text-sm leading-relaxed ${
                m.sender === "user"
                  ? "bg-[#142A3B] text-white rounded-br-xs shadow-xs"
                  : "bg-white border border-[#E5E3DA] text-[#142A3B] rounded-bl-xs shadow-xs space-y-3"
              }`}
            >
              {/* Message Header for Assistant */}
              {m.sender === "assistant" && (
                <div className="flex items-center justify-between pb-2 border-b border-[#EFECE4]">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-md bg-[#285C4D] text-white flex items-center justify-center text-xs font-bold">
                      <IconSparkles className="w-3 h-3 text-white" />
                    </span>
                    <span className="text-xs font-bold text-[#285C4D] uppercase tracking-wide">
                      Lucid Fiduciary Analysis
                    </span>
                  </div>
                  <button
                    onClick={() => handleCopyText(m.id, m.text)}
                    type="button"
                    className="text-xs text-[#66758A] hover:text-[#142A3B] flex items-center gap-1 cursor-pointer transition-colors"
                  >
                    {copiedId === m.id ? (
                      <>
                        <IconCheck className="w-3.5 h-3.5 text-[#285C4D]" />
                        <span className="text-[#285C4D] font-bold">Copied</span>
                      </>
                    ) : (
                      <span>Copy Thesis</span>
                    )}
                  </button>
                </div>
              )}

              {/* Message Body */}
              {m.sender === "assistant" ? (
                <FormattedAssistantMessage text={m.text} />
              ) : (
                <div className="whitespace-pre-line font-medium text-white">{m.text}</div>
              )}

              {/* Dynamic Scenario Simulation Result Card */}
              {m.simulation &&
                m.simulation.baseline_value != null &&
                m.simulation.stressed_value != null && (
                <div className="mt-3 p-4 sm:p-5 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] space-y-3.5 text-sm text-[#142A3B]">
                  <div className="flex justify-between items-center pb-2.5 border-b border-[#E5E3DA]">
                    <div className="font-bold flex items-center gap-2 text-[#B91C1C] text-sm sm:text-base">
                      <IconBolt className="w-5 h-5" />
                      <span>{m.simulation.scenario_title || "Market Stress Simulation"}</span>
                    </div>
                    <span className="text-xs sm:text-sm font-bold px-2.5 py-1 rounded bg-[#FEF2F2] text-[#B91C1C] border border-[#FECACA] tabular-nums">
                      -{Math.abs(Number(m.simulation.loss_pct) || 0)}% Net Drawdown
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs sm:text-sm">
                    <div className="p-2.5 rounded-lg bg-white border border-[#E5E3DA]">
                      <span className="text-[#66758A] block text-xs">Baseline Portfolio:</span>
                      <strong className="text-sm font-bold tabular-nums text-[#142A3B]">
                        ₹{Number(m.simulation.baseline_value || 0).toLocaleString("en-IN")}
                      </strong>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white border border-[#E5E3DA]">
                      <span className="text-[#66758A] block text-xs">Stressed Valuation:</span>
                      <strong className="text-sm font-bold tabular-nums text-[#B91C1C]">
                        ₹{Number(m.simulation.stressed_value || 0).toLocaleString("en-IN")}
                      </strong>
                    </div>
                  </div>

                  {m.simulation.cushion_effect && (
                    <div className="p-3 rounded-lg bg-[#ECF3F0] border border-[#C6D8D1] text-xs sm:text-sm text-[#285C4D]">
                      <strong>Diversification Cushion:</strong> {m.simulation.cushion_effect}
                    </div>
                  )}

                  {/* Holding Impacts Table */}
                  {m.simulation.holding_impacts && m.simulation.holding_impacts.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <div className="text-xs uppercase font-bold text-[#66758A] tracking-wider">
                        Per-Holding Simulated Impact:
                      </div>
                      <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                        {m.simulation.holding_impacts.map((hi) => (
                          <div
                            key={hi.symbol}
                            className="flex justify-between items-center p-2.5 rounded-lg bg-white border border-[#E5E3DA] text-xs sm:text-sm"
                          >
                            <div>
                              <span className="font-bold text-[#142A3B]">{hi.symbol}</span>{" "}
                              <span className="text-[#66758A] text-xs">({hi.weight_pct}%)</span>
                              <div className="text-xs text-[#66758A] mt-0.5">{hi.role_description}</div>
                            </div>
                            <div className="text-right flex-shrink-0 ml-2">
                              <span
                                className={`font-bold tabular-nums px-2 py-0.5 rounded text-xs sm:text-sm ${
                                  hi.simulated_change_pct >= 0
                                    ? "bg-[#ECF3F0] text-[#285C4D]"
                                    : "bg-[#FEF2F2] text-[#B91C1C]"
                                }`}
                              >
                                {hi.simulated_change_pct >= 0
                                  ? `+${hi.simulated_change_pct}%`
                                  : `${hi.simulated_change_pct}%`}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {m.simulation.historical_recovery_context && (
                    <div className="text-xs text-[#66758A] italic pt-1 flex items-center gap-1.5">
                      <IconLightbulb className="w-3.5 h-3.5 shrink-0 text-[#285C4D]" />
                      <span><strong>Historical Context:</strong> {m.simulation.historical_recovery_context}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Follow-up Prompts */}
              {m.followups && m.followups.length > 0 && (
                <div className="pt-2 flex flex-wrap gap-2 border-t border-[#EFECE4]">
                  <span className="text-xs font-semibold text-[#66758A] w-full mb-0.5">
                    Suggested Follow-up Questions:
                  </span>
                  {m.followups.map((f, fIdx) => (
                    <button
                      key={fIdx}
                      onClick={() => handleSend(f)}
                      disabled={loading}
                      type="button"
                      className="text-xs px-3 py-1.5 rounded-lg bg-[#F7F6F1] hover:bg-[#EFECE4] border border-[#E5E3DA] text-[#285C4D] font-medium transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span>{f}</span>
                      <IconArrowUpRight className="w-3 h-3 text-[#285C4D]" />
                    </button>
                  ))}
                </div>
              )}
            </div>
            <span className="text-xs text-[#94A3B8] mt-1 px-1">{m.timestamp}</span>
          </div>
        ))}

        {/* Live Loading Indicator */}
        {loading && (
          <div className="flex items-center gap-3 text-sm text-[#285C4D] p-3.5 rounded-2xl bg-white border border-[#E5E3DA] w-fit shadow-xs animate-pulse">
            <span className="w-4 h-4 rounded-full border-2 border-[#285C4D] border-t-transparent animate-spin"></span>
            <span className="text-xs sm:text-sm font-semibold">
              Analyzing audited metrics, market betas, and portfolio correlations...
            </span>
          </div>
        )}

        {/* Anchor element for smooth auto-scrolling */}
        <div ref={messagesEndRef} className="h-1" />
      </div>

      {/* Floating 'Jump to Bottom' Button */}
      {showScrollBottom && (
        <button
          onClick={() => scrollToBottom(true)}
          type="button"
          className="absolute bottom-24 right-6 px-3.5 py-1.5 rounded-full bg-[#142A3B] text-white text-xs font-bold shadow-lg hover:bg-[#0E1E2B] transition-all cursor-pointer flex items-center gap-1.5 border border-white/20 animate-bounce"
        >
          <span>↓ Jump to latest message</span>
        </button>
      )}

      {/* Bottom Control Deck: Quick Suggestion Chips + Input Bar */}
      <div className="border-t border-[#E5E3DA] bg-white p-3 sm:p-4 space-y-2.5">
        {/* Horizontal Quick-Action Prompt Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar text-xs">
          <span className="text-xs font-bold text-[#66758A] flex-shrink-0 flex items-center gap-1">
            <IconSparkles className="w-3.5 h-3.5 text-[#285C4D]" />
            <span>Try:</span>
          </span>
          {quickPills.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(p.query)}
              disabled={loading}
              className="px-2.5 py-1 rounded-lg bg-[#F7F6F1] hover:bg-[#ECF3F0] hover:text-[#285C4D] border border-[#E5E3DA] text-[#4A5568] whitespace-nowrap transition-colors cursor-pointer text-xs flex-shrink-0"
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask about a stock (e.g. 'Why TCS?'), compare holdings, or ask anything (e.g. 'What does Lucid do?')..."
              disabled={loading}
              className="w-full pl-4 pr-9 py-3 rounded-xl bg-[#F7F6F1] border border-[#E5E3DA] text-xs sm:text-sm text-[#142A3B] focus:bg-white focus:outline-none focus:border-[#285C4D] focus:ring-1 focus:ring-[#285C4D] transition-all"
            />
            {inputQuery && (
              <button
                type="button"
                onClick={() => setInputQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-[#142A3B] cursor-pointer"
              >
                <IconX className="w-4 h-4" />
              </button>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="px-5 sm:px-6 py-3 rounded-xl bg-[#285C4D] hover:bg-[#1E463A] text-white font-bold text-xs sm:text-sm transition-all disabled:opacity-50 cursor-pointer shadow-xs whitespace-nowrap flex items-center gap-1.5"
          >
            <span>Ask AI</span>
            <span>&rarr;</span>
          </button>
        </form>
      </div>
    </div>
  );
}
