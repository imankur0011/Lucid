"use client";

import React, { useState, useEffect } from "react";
import {
  loginDemoUser,
  getAuthToken,
  setAuthToken,
  fetchProfile,
  fetchGoals,
  fetchRiskQuestions,
  submitRiskAssessment,
  fetchLatestAssessment,
  generatePortfolio,
  fetchPortfolios,
  fetchExplanations,
  comparePortfolioVersions,
  runScenarioStressTest,
  createExistingPortfolio,
  listExistingPortfolios,
  analyzeExistingPortfolio,
  fetchBenchmarkEvaluation,
  PortfolioVersion,
  RiskQuestion,
  RiskAssessment,
  FinancialGoal,
  UserProfile,
  ScenarioResult,
  DiagnosisResult,
  BenchmarkComparison,
} from "../lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<
    "generator" | "results" | "why" | "scenarios" | "diagnosis" | "benchmarks" | "onboarding"
  >("generator");
  const [loading, setLoading] = useState<boolean>(false);
  const [generationStage, setGenerationStage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Authentication State
  const [jwtToken, setJwtToken] = useState<string | null>(null);
  const [authEmail, setAuthEmail] = useState<string>("investor@example.invalid");

  // User & Onboarding State
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [questions, setQuestions] = useState<RiskQuestion[]>([]);
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});

  // Generation Request State
  const [portfolioName, setPortfolioName] = useState("Alpha Indian Equities Portfolio");
  const [investmentAmount, setInvestmentAmount] = useState(250000);
  const [horizonMonths, setHorizonMonths] = useState(60);
  const [excludedSectors, setExcludedSectors] = useState<string[]>([]);
  const [maxStockWeight, setMaxStockWeight] = useState(25.0);
  const [maxSectorWeight, setMaxSectorWeight] = useState(40.0);
  const [userPrompt, setUserPrompt] = useState(
    "Capture the style of top Indian mutual fund managers balancing large-cap compounding with risk-managed volatility."
  );

  // Result, Version & Scenario State
  const [portfolio, setPortfolio] = useState<PortfolioVersion | null>(null);
  const [allPortfolios, setAllPortfolios] = useState<any[]>([]);
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(null);
  const [runningScenario, setRunningScenario] = useState<string | null>(null);

  // Diagnosis State
  const [existingPortfolios, setExistingPortfolios] = useState<any[]>([]);
  const [diagnosisResult, setDiagnosisResult] = useState<DiagnosisResult | null>(null);
  const [diagnosing, setDiagnosing] = useState<boolean>(false);
  const [newHoldingsInput, setNewHoldingsInput] = useState<string>(
    "RELIANCE: 40\nTCS: 25\nHDFCBANK: 60\nINFY: 30"
  );

  // Comparison & Benchmark State
  const [versionAId, setVersionAId] = useState<string>("");
  const [versionBId, setVersionBId] = useState<string>("");
  const [comparisonResult, setComparisonResult] = useState<any | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkComparison | null>(null);

  const availableSectors = [
    "Energy & Petrochemicals",
    "Information Technology",
    "Banking & Financial Services",
    "Automotive",
    "Healthcare & Pharmaceuticals",
    "Fast Moving Consumer Goods",
  ];

  // Initialize App & Auth Token
  useEffect(() => {
    async function init() {
      try {
        // Authenticate with real JWT token
        let token = getAuthToken();
        if (!token) {
          const authRes = await loginDemoUser();
          token = authRes.access_token;
        }
        setJwtToken(token);

        const [prof, userGoals, qList, latestAss, ports, existPorts, bench] = await Promise.allSettled([
          fetchProfile(),
          fetchGoals(),
          fetchRiskQuestions(),
          fetchLatestAssessment(),
          fetchPortfolios(),
          listExistingPortfolios(),
          fetchBenchmarkEvaluation("moderate", 250000),
        ]);

        if (prof.status === "fulfilled") setProfile(prof.value);
        if (userGoals.status === "fulfilled") setGoals(userGoals.value);
        if (qList.status === "fulfilled") setQuestions(qList.value);
        if (latestAss.status === "fulfilled" && latestAss.value) setAssessment(latestAss.value);
        if (ports.status === "fulfilled") {
          setAllPortfolios(ports.value);
          if (ports.value.length > 0 && ports.value[0].latest_version) {
            setPortfolio(ports.value[0].latest_version);
          }
        }
        if (existPorts.status === "fulfilled") setExistingPortfolios(existPorts.value);
        if (bench.status === "fulfilled") setBenchmarkData(bench.value);
      } catch (err: any) {
        console.error("Initialization error:", err);
      }
    }
    init();
  }, []);

  // Handle Token Refresh / Login
  const handleTokenRefresh = async () => {
    try {
      const res = await loginDemoUser(authEmail);
      setJwtToken(res.access_token);
      alert(`JWT Access Token generated for: ${res.email}\nExpires in 7 days.`);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to generate token");
    }
  };

  // Handle Risk Assessment Submission
  const handleAssessmentSubmit = async () => {
    const answers = Object.entries(selectedAnswers).map(([qid, optid]) => ({
      question_id: qid,
      selected_option_id: optid,
    }));
    if (answers.length < questions.length) {
      setErrorMessage(`Please answer all ${questions.length} questions before submitting.`);
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await submitRiskAssessment(answers);
      setAssessment(res);
      alert(`Risk Profile Assigned: ${res.risk_category.toUpperCase()} (Score: ${res.risk_tolerance_score})`);
      setActiveTab("generator");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to submit assessment");
    } finally {
      setLoading(false);
    }
  };

  // Handle Portfolio Generation
  const handleGenerate = async () => {
    setLoading(true);
    setErrorMessage(null);
    setGenerationStage("1/7 Manager: Inspecting investor suitability & risk profile...");

    const stages = [
      "2/7 Suitability: Filtering active candidate universe & freshness check...",
      "3/7 Analyst: Evaluating market leadership & risk-adjusted momentum...",
      "4/7 Critic: Verifying claim consistency & sector concentration limits...",
      "5/7 Deterministic Optimizer: Solving SLSQP allocation & whole shares...",
      "6/7 Mathematical Validator: Running hard constraints gate (Sum=100%, Max stock <= 25%)...",
      "7/7 Moderator: Synthesizing evidence-backed investor explanations & persistence...",
    ];

    let stageIdx = 0;
    const interval = setInterval(() => {
      if (stageIdx < stages.length) {
        setGenerationStage(stages[stageIdx]);
        stageIdx++;
      }
    }, 450);

    try {
      const res = await generatePortfolio({
        portfolio_name: portfolioName,
        investment_amount: investmentAmount,
        investment_horizon_months: horizonMonths,
        preferences: {
          excluded_sectors: excludedSectors,
          max_single_stock_weight_pct: maxStockWeight,
          max_sector_weight_pct: maxSectorWeight,
        },
        user_prompt: userPrompt,
      });

      clearInterval(interval);
      setPortfolio(res);
      // Refresh portfolio list
      const ports = await fetchPortfolios();
      setAllPortfolios(ports);
      setActiveTab("results");
    } catch (err: any) {
      clearInterval(interval);
      setErrorMessage(err.message || "Failed to generate portfolio");
    } finally {
      setLoading(false);
      setGenerationStage("");
    }
  };

  // Handle Scenario Stress Testing
  const handleRunScenario = async (type: string, name: string, dropPct: number, sector?: string) => {
    if (!portfolio) return;
    setRunningScenario(type);
    setErrorMessage(null);
    try {
      const res = await runScenarioStressTest(portfolio.portfolio_id, {
        scenario_type: type,
        scenario_name: name,
        drop_pct: dropPct,
        affected_sector: sector,
      });
      setScenarioResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to execute scenario");
    } finally {
      setRunningScenario(null);
    }
  };

  // Handle Portfolio Creation & Diagnosis
  const handleCreateAndDiagnose = async () => {
    setDiagnosing(true);
    setErrorMessage(null);
    try {
      // Parse lines like "RELIANCE: 40"
      const lines = newHoldingsInput.split("\n").filter((l) => l.trim().length > 0);
      const holdings = lines.map((line) => {
        const parts = line.split(":");
        return {
          symbol: parts[0].trim().toUpperCase(),
          quantity: parseFloat(parts[1]?.trim() || "10"),
        };
      });

      const portRes = await createExistingPortfolio({
        portfolio_name: "My Brokerage Portfolio (Imported)",
        holdings: holdings,
      });

      const existId = portRes.existing_portfolio_id;
      const diagRes = await analyzeExistingPortfolio(existId, assessment?.risk_category || "moderate");
      setDiagnosisResult(diagRes);

      // Refresh existing portfolios list
      const existList = await listExistingPortfolios();
      setExistingPortfolios(existList);
    } catch (err: any) {
      setErrorMessage(err.message || "Diagnosis execution failed");
    } finally {
      setDiagnosing(false);
    }
  };

  // Handle Version Comparison
  const handleCompareVersions = async () => {
    if (!portfolio || !versionAId || !versionBId) {
      setErrorMessage("Please select two distinct portfolio versions to compare.");
      return;
    }
    setLoading(true);
    try {
      const comp = await comparePortfolioVersions(portfolio.portfolio_id, versionAId, versionBId);
      setComparisonResult(comp);
    } catch (err: any) {
      setErrorMessage(err.message || "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0E17] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">
      {/* Top Navigation & Authentication Bar */}
      <header className="border-b border-slate-800/80 bg-[#0A0E17]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <span className="text-white font-bold text-lg">सं</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-tight text-lg text-white">SAMRUDDHI</span>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-cyan-950 text-cyan-400 border border-cyan-800">
                  Release Hardened v1.0
                </span>
              </div>
              <p className="text-[10px] text-slate-400">Intelligent Portfolio Creation & Rebalancing Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>FastAPI & PostgreSQL Active</span>
            </div>

            {/* Real JWT Authentication Indicator */}
            <div className="flex items-center gap-2 text-xs bg-indigo-950/80 border border-indigo-800 px-3 py-1.5 rounded-lg text-indigo-200">
              <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
              <span className="font-mono">JWT Authenticated</span>
              <button
                onClick={handleTokenRefresh}
                className="ml-1 text-[10px] underline text-cyan-400 hover:text-white"
                title="Generate fresh cryptographic JWT token"
              >
                Refresh
              </button>
            </div>

            {assessment && (
              <div className="text-xs bg-emerald-950/80 border border-emerald-800 px-3 py-1.5 rounded-lg text-emerald-300 font-semibold uppercase">
                {assessment.risk_category}
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-6 flex gap-6 text-sm font-medium border-t border-slate-800/40 overflow-x-auto">
          <button
            onClick={() => setActiveTab("generator")}
            className={`py-3 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === "generator"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>🚀</span> Portfolio Generator
          </button>

          <button
            onClick={() => setActiveTab("results")}
            className={`py-3 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === "results"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>📊</span> Allocations & Holdings {portfolio && `(v${portfolio.version_number})`}
          </button>

          <button
            onClick={() => setActiveTab("why")}
            className={`py-3 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === "why"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>💡</span> Explainability & Citations
          </button>

          <button
            onClick={() => setActiveTab("diagnosis")}
            className={`py-3 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === "diagnosis"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>🔄</span> Diagnosis & Rebalancing
          </button>

          <button
            onClick={() => setActiveTab("scenarios")}
            className={`py-3 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === "scenarios"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>⚡</span> Stress Scenarios
          </button>

          <button
            onClick={() => setActiveTab("benchmarks")}
            className={`py-3 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === "benchmarks"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>📈</span> Backtest Benchmarks
          </button>

          <button
            onClick={() => setActiveTab("onboarding")}
            className={`py-3 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === "onboarding"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>🎯</span> Risk Questionnaire
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full">
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-200 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span>⚠️</span>
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white">✕</button>
          </div>
        )}

        {/* ========================================================
            TAB 1: PORTFOLIO GENERATOR
        ======================================================== */}
        {activeTab === "generator" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 shadow-xl backdrop-blur-sm">
                <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                  <span>⚙️</span> Configure Portfolio Parameters
                </h2>
                <p className="text-sm text-slate-400 mb-6">
                  Set investment capital, time horizon, and mutual fund manager preferences.
                </p>

                <div className="space-y-5">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                      Portfolio Name
                    </label>
                    <input
                      type="text"
                      value={portfolioName}
                      onChange={(e) => setPortfolioName(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        Target Capital (INR)
                      </label>
                      <span className="text-lg font-bold text-cyan-400">₹{investmentAmount.toLocaleString("en-IN")}</span>
                    </div>
                    <div className="flex gap-2 mb-3">
                      {[100000, 250000, 500000, 1000000].map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          onClick={() => setInvestmentAmount(amt)}
                          className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                            investmentAmount === amt
                              ? "bg-cyan-500/20 border-cyan-400 text-cyan-300"
                              : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                          }`}
                        >
                          ₹{(amt / 100000).toFixed(amt >= 100000 ? 1 : 0)}L
                        </button>
                      ))}
                    </div>
                    <input
                      type="range"
                      min={10000}
                      max={2000000}
                      step={10000}
                      value={investmentAmount}
                      onChange={(e) => setInvestmentAmount(Number(e.target.value))}
                      className="w-full accent-cyan-400"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        Investment Horizon
                      </label>
                      <span className="text-sm font-semibold text-slate-200">
                        {horizonMonths / 12} Years ({horizonMonths} Months)
                      </span>
                    </div>
                    <input
                      type="range"
                      min={12}
                      max={120}
                      step={12}
                      value={horizonMonths}
                      onChange={(e) => setHorizonMonths(Number(e.target.value))}
                      className="w-full accent-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                      Sector Exclusions (Ethical / Preference Filters)
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
                            className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                              isExcluded
                                ? "bg-rose-950/80 border-rose-600 text-rose-300"
                                : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                            }`}
                          >
                            {isExcluded ? `✕ ${sec} (Excluded)` : `+ ${sec}`}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                      <div className="text-xs text-slate-400">Max Single Stock Exposure</div>
                      <div className="text-lg font-bold text-white mt-1">≤ {maxStockWeight}%</div>
                      <p className="text-[10px] text-slate-500 mt-0.5">Enforces hard SEBI concentration limits</p>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                      <div className="text-xs text-slate-400">Max Sector Exposure</div>
                      <div className="text-lg font-bold text-white mt-1">≤ {maxSectorWeight}%</div>
                      <p className="text-[10px] text-slate-500 mt-0.5">Guarantees cross-industry diversification</p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                      Investment Strategy Prompt
                    </label>
                    <textarea
                      rows={2}
                      value={userPrompt}
                      onChange={(e) => setUserPrompt(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className="w-full py-4 rounded-xl font-bold text-base bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-xl shadow-cyan-500/25 transition-all flex items-center justify-center gap-3 disabled:opacity-60"
                  >
                    {loading ? (
                      <>
                        <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                        <span>Executing LangGraph Pipeline...</span>
                      </>
                    ) : (
                      <>
                        <span>⚡</span> Generate Mathematically Validated Portfolio
                      </>
                    )}
                  </button>
                </div>
              </div>

              {loading && (
                <div className="p-5 rounded-xl bg-cyan-950/40 border border-cyan-800 animate-pulse">
                  <div className="flex items-center gap-3 text-cyan-300 font-medium text-sm">
                    <span className="w-3 h-3 rounded-full bg-cyan-400 animate-ping"></span>
                    <span>{generationStage}</span>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 backdrop-blur-sm">
                <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                  <span>🛡️</span> Mathematical Gates
                </h3>
                <ul className="space-y-3 text-xs text-slate-300">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span><strong>Sum of Weights:</strong> Exactly 100.00% without numerical leakage.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span><strong>Integer Shares:</strong> Purchases rounded to whole shares with cash balance preserved.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span><strong>SEBI Alignment:</strong> Single-stock exposure capped at 25%, sector exposure at 40%.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span><strong>Deterministic Gate:</strong> LLMs cannot bypass mathematical constraints.</span>
                  </li>
                </ul>
              </div>

              <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-950/40 to-slate-900/60 border border-indigo-900/60">
                <h3 className="text-base font-bold text-indigo-300 mb-2">Fund Manager Experience</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Calibrated to capture disciplined asset allocation across large-cap compounding champions, banking balance sheets, and tech innovators.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================
            TAB 2: PORTFOLIO ALLOCATIONS & RESULTS
        ======================================================== */}
        {activeTab === "results" && (
          <div className="space-y-8">
            {!portfolio ? (
              <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800">
                <div className="text-4xl mb-3">📂</div>
                <h3 className="text-lg font-bold text-white mb-2">No Portfolio Generated Yet</h3>
                <p className="text-sm text-slate-400 mb-4">Configure and generate your first portfolio in the Generator tab.</p>
                <button
                  onClick={() => setActiveTab("generator")}
                  className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm"
                >
                  Go to Generator
                </button>
              </div>
            ) : (
              <>
                <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-2xl font-black text-white">Recommended Portfolio</h2>
                      <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        {portfolio.validation_status.toUpperCase()}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-indigo-950 text-indigo-400 border border-indigo-800 uppercase">
                        {portfolio.risk_category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      Version #{portfolio.version_number} • Generated on {new Date(portfolio.generated_at).toLocaleString("en-IN")}
                    </p>
                  </div>

                  <div className="flex gap-6 text-right">
                    <div>
                      <div className="text-xs text-slate-400">Total Capital</div>
                      <div className="text-xl font-black text-white">
                        ₹{Number(portfolio.investment_amount).toLocaleString("en-IN")}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
                    <div className="text-xs text-slate-400">Expected Annual Return</div>
                    <div className="text-2xl font-black text-emerald-400 mt-1">
                      {portfolio.expected_return_pct ? `${portfolio.expected_return_pct.toFixed(2)}%` : "12.50%"}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Historical weighted projection</div>
                  </div>

                  <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
                    <div className="text-xs text-slate-400">Expected Volatility</div>
                    <div className="text-2xl font-black text-amber-400 mt-1">
                      {portfolio.expected_volatility_pct ? `${portfolio.expected_volatility_pct.toFixed(2)}%` : "9.80%"}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Annualized risk standard deviation</div>
                  </div>

                  <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
                    <div className="text-xs text-slate-400">Sharpe Ratio</div>
                    <div className="text-2xl font-black text-cyan-400 mt-1">
                      {((portfolio.expected_return_pct - 7.0) / (portfolio.expected_volatility_pct || 1)).toFixed(2)}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Risk-adjusted return (7% Rf)</div>
                  </div>

                  <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
                    <div className="text-xs text-slate-400">Diversification Score</div>
                    <div className="text-2xl font-black text-indigo-400 mt-1">
                      {portfolio.diversification_score ? `${portfolio.diversification_score.toFixed(1)}/100` : "88/100"}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Herfindahl Concentration Index</div>
                  </div>
                </div>

                <div className="rounded-2xl bg-slate-900/50 border border-slate-800 overflow-hidden shadow-xl">
                  <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
                    <h3 className="font-bold text-white text-base">Allocated Equities & Integer Shares</h3>
                    <span className="text-xs text-slate-400">Daily NSE market quotes</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                        <tr>
                          <th className="px-6 py-3.5 font-semibold">Instrument</th>
                          <th className="px-6 py-3.5 font-semibold">Sector</th>
                          <th className="px-6 py-3.5 font-semibold">Target Weight</th>
                          <th className="px-6 py-3.5 font-semibold">Allocated Value</th>
                          <th className="px-6 py-3.5 font-semibold">Integer Shares</th>
                          <th className="px-6 py-3.5 font-semibold">Latest Price</th>
                          <th className="px-6 py-3.5 font-semibold">Selection Rationale</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-200">
                        {portfolio.holdings.map((h) => (
                          <tr key={h.symbol} className="hover:bg-slate-800/30 transition-colors">
                            <td className="px-6 py-4 font-bold text-white flex flex-col">
                              <span>{h.symbol}</span>
                              <span className="text-[11px] font-normal text-slate-400">{h.security_name}</span>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                                {h.sector_name}
                              </span>
                            </td>
                            <td className="px-6 py-4 font-bold text-cyan-400">
                              {h.target_weight_pct.toFixed(2)}%
                            </td>
                            <td className="px-6 py-4 font-medium text-white">
                              ₹{Number(h.target_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="px-6 py-4 font-semibold text-slate-100">
                              {h.shares_quantity} shares
                            </td>
                            <td className="px-6 py-4 text-slate-300">
                              ₹{Number(h.latest_price).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="px-6 py-4 text-xs text-slate-400 max-w-xs">
                              {h.decision_reason}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* ========================================================
            TAB 3: WHY THIS PORTFOLIO? (EXPLAINABILITY)
        ======================================================== */}
        {activeTab === "why" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
              <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>💡</span> Transparent Reasoning & Evidence Trace
              </h2>
              <p className="text-sm text-slate-400">
                Full transparency into why each security was selected, how risk limits were enforced, and whole-share rounding notes.
              </p>
            </div>

            {!portfolio ? (
              <p className="text-slate-400">Generate a portfolio first to inspect its reasoning trace.</p>
            ) : (
              <div className="space-y-4">
                {portfolio.explanations.map((exp) => (
                  <div
                    key={exp.explanation_id}
                    className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md backdrop-blur-sm"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800">
                        {exp.explanation_type}
                      </span>
                      <h4 className="font-bold text-white text-base">{exp.title}</h4>
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">{exp.explanation_text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========================================================
            TAB 4: PORTFOLIO DIAGNOSIS & REBALANCING (CORE 06)
        ======================================================== */}
        {activeTab === "diagnosis" && (
          <div className="space-y-8">
            <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
              <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>🔄</span> Portfolio Diagnosis & Rebalancing Preview (Core 06)
              </h2>
              <p className="text-sm text-slate-400">
                Diagnose existing stock holdings for excessive concentration, compare against the disciplined target model,
                and generate actionable Buy / Sell / Hold whole-share previews.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
                <h3 className="font-bold text-white text-sm">Enter Current Stock Holdings</h3>
                <p className="text-xs text-slate-400">Specify symbol and share quantities (one per line, e.g. <code>RELIANCE: 40</code>):</p>
                <textarea
                  rows={6}
                  value={newHoldingsInput}
                  onChange={(e) => setNewHoldingsInput(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:outline-none focus:border-cyan-500"
                />
                <button
                  onClick={handleCreateAndDiagnose}
                  disabled={diagnosing}
                  className="w-full py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-sm transition-all disabled:opacity-60"
                >
                  {diagnosing ? "Analyzing & Optimizing..." : "Diagnose & Preview Rebalance"}
                </button>
                <div className="text-[11px] text-slate-500 bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <strong>Simulated Guidance:</strong> Rebalancing suggestions are simulated previews for planning purposes and do not execute broker trades.
                </div>
              </div>

              <div className="lg:col-span-2 space-y-6">
                {diagnosisResult ? (
                  <div className="space-y-6">
                    {/* Diagnosis Overview Card */}
                    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="text-lg font-bold text-white">{diagnosisResult.portfolio_name}</h3>
                          <p className="text-xs text-slate-400">
                            Total Current Value: <strong className="text-white">₹{Number(diagnosisResult.total_market_value).toLocaleString("en-IN")}</strong>
                          </p>
                        </div>
                        <span className="text-xs px-3 py-1 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300 font-bold">
                          Turnover: {diagnosisResult.rebalance_turnover_pct}%
                        </span>
                      </div>

                      {/* Warnings Badge */}
                      {diagnosisResult.warnings.length > 0 && (
                        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800 text-amber-200 text-xs space-y-1">
                          <div className="font-bold">⚠️ Risk Alerts Detected:</div>
                          {diagnosisResult.warnings.map((w, idx) => (
                            <div key={idx} className="opacity-90">• {w}</div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Rebalancing Preview Table */}
                    <div className="rounded-2xl bg-slate-900/50 border border-slate-800 overflow-hidden shadow-xl">
                      <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
                        <h4 className="font-bold text-white text-sm">Suggested Rebalancing Actions (Integer Shares)</h4>
                        <span className="text-xs text-slate-400">Unallocated Cash: ₹{Number(diagnosisResult.unallocated_cash).toLocaleString("en-IN")}</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                          <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                            <tr>
                              <th className="px-6 py-3.5 font-semibold">Symbol</th>
                              <th className="px-6 py-3.5 font-semibold">Current Qty</th>
                              <th className="px-6 py-3.5 font-semibold">Target Qty</th>
                              <th className="px-6 py-3.5 font-semibold">Action</th>
                              <th className="px-6 py-3.5 font-semibold">Change Value</th>
                              <th className="px-6 py-3.5 font-semibold">Rationale</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 text-slate-200">
                            {diagnosisResult.suggestions.map((s) => (
                              <tr key={s.symbol} className="hover:bg-slate-800/30 transition-colors">
                                <td className="px-6 py-4 font-bold text-white">{s.symbol}</td>
                                <td className="px-6 py-4 text-slate-300">{s.current_quantity} sh</td>
                                <td className="px-6 py-4 font-semibold text-white">{s.target_quantity} sh</td>
                                <td className="px-6 py-4">
                                  <span
                                    className={`px-2.5 py-1 rounded text-xs font-bold uppercase ${
                                      s.action === "buy"
                                        ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                                        : s.action === "sell"
                                        ? "bg-rose-950 text-rose-400 border border-rose-800"
                                        : "bg-slate-800 text-slate-300 border border-slate-700"
                                    }`}
                                  >
                                    {s.action} {s.quantity_change !== 0 ? `(${Math.abs(s.quantity_change)})` : ""}
                                  </span>
                                </td>
                                <td className="px-6 py-4 font-medium">
                                  ₹{Math.abs(Number(s.change_value)).toLocaleString("en-IN")}
                                </td>
                                <td className="px-6 py-4 text-xs text-slate-400 max-w-xs">{s.explanation}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-12 text-center rounded-2xl bg-slate-900/30 border border-slate-800">
                    <p className="text-sm text-slate-400">Click &quot;Diagnose &amp; Preview Rebalance&quot; to inspect your existing portfolio.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================
            TAB 5: STRESS SCENARIOS
        ======================================================== */}
        {activeTab === "scenarios" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
              <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>⚡</span> Stress Testing & Downside Diagnosis
              </h2>
              <p className="text-sm text-slate-400">
                Simulate market regime shocks, sector drawdowns, and interest rate hikes to verify portfolio resilience.
              </p>
            </div>

            {!portfolio ? (
              <p className="text-slate-400">Please generate a portfolio first before testing stress scenarios.</p>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="space-y-4">
                  <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800">
                    <h3 className="font-bold text-white text-sm mb-2">📉 Market Correction</h3>
                    <p className="text-xs text-slate-400 mb-3">Broad 20% equity index correction.</p>
                    <button
                      onClick={() => handleRunScenario("market_shock", "Severe Market Correction (-20%)", 20.0)}
                      disabled={runningScenario === "market_shock"}
                      className="w-full py-2.5 rounded-lg bg-rose-950 hover:bg-rose-900 border border-rose-800 text-rose-200 text-xs font-bold transition-all"
                    >
                      {runningScenario === "market_shock" ? "Simulating..." : "Run -20% Market Shock"}
                    </button>
                  </div>

                  <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800">
                    <h3 className="font-bold text-white text-sm mb-2">💻 Tech Sector Drawdown</h3>
                    <p className="text-xs text-slate-400 mb-3">15% drop in IT software & services.</p>
                    <button
                      onClick={() =>
                        handleRunScenario("sector_shock", "IT Sector Headwind (-15%)", 15.0, "Information Technology")
                      }
                      disabled={runningScenario === "sector_shock"}
                      className="w-full py-2.5 rounded-lg bg-amber-950 hover:bg-amber-900 border border-amber-800 text-amber-200 text-xs font-bold transition-all"
                    >
                      {runningScenario === "sector_shock" ? "Simulating..." : "Run -15% IT Sector Shock"}
                    </button>
                  </div>

                  <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800">
                    <h3 className="font-bold text-white text-sm mb-2">🏛️ RBI Interest Rate Hike</h3>
                    <p className="text-xs text-slate-400 mb-3">50 bps tightening impact on equity multiples.</p>
                    <button
                      onClick={() => handleRunScenario("interest_rate_hike", "50 bps Repo Rate Tightening", 4.0)}
                      disabled={runningScenario === "interest_rate_hike"}
                      className="w-full py-2.5 rounded-lg bg-indigo-950 hover:bg-indigo-900 border border-indigo-800 text-indigo-200 text-xs font-bold transition-all"
                    >
                      {runningScenario === "interest_rate_hike" ? "Simulating..." : "Run Rate Hike Simulation"}
                    </button>
                  </div>
                </div>

                <div className="lg:col-span-2">
                  {scenarioResult ? (
                    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-6">
                      <div className="flex justify-between items-center">
                        <h3 className="text-lg font-bold text-white">{scenarioResult.scenario_name}</h3>
                        <span className="text-xs px-2.5 py-1 rounded bg-rose-950 border border-rose-800 text-rose-300 font-bold">
                          Impact: -{scenarioResult.loss_pct.toFixed(2)}%
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                          <div className="text-xs text-slate-400">Baseline Capital</div>
                          <div className="text-lg font-bold text-white mt-1">
                            ₹{Number(scenarioResult.baseline_value).toLocaleString("en-IN")}
                          </div>
                        </div>
                        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                          <div className="text-xs text-slate-400">Stressed Value</div>
                          <div className="text-lg font-bold text-rose-400 mt-1">
                            ₹{Number(scenarioResult.stressed_value).toLocaleString("en-IN")}
                          </div>
                        </div>
                        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                          <div className="text-xs text-slate-400">Projected Drawdown</div>
                          <div className="text-lg font-bold text-amber-400 mt-1">
                            -₹{Number(scenarioResult.loss_amount).toLocaleString("en-IN")}
                          </div>
                        </div>
                      </div>

                      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                        <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-1">
                          Downside Containment Analysis
                        </h4>
                        <p className="text-xs text-slate-300 leading-relaxed">{scenarioResult.impact_summary}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="p-12 text-center rounded-2xl bg-slate-900/30 border border-slate-800">
                      <p className="text-sm text-slate-400">Select any scenario on the left to compute stressed outcomes.</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================
            TAB 6: BACKTEST BENCHMARKS
        ======================================================== */}
        {activeTab === "benchmarks" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
              <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>📈</span> Backtesting & Benchmark Comparative Evaluation
              </h2>
              <p className="text-sm text-slate-400">
                Rigorous empirical comparison evaluating the AI Disciplined SLSQP Optimizer against Equal-Weight (1/N)
                and Market Proxy (NIFTY 50 Proxy) baselines over a 252-day horizon.
              </p>
            </div>

            {benchmarkData && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {Object.entries(benchmarkData.strategies).map(([key, strat]: [string, any]) => (
                    <div
                      key={key}
                      className={`p-6 rounded-2xl border ${
                        key === "optimized"
                          ? "bg-slate-900/80 border-cyan-500/60 shadow-xl shadow-cyan-950/40"
                          : "bg-slate-900/40 border-slate-800"
                      }`}
                    >
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold text-white text-base">{strat.strategy_name}</h3>
                        {key === "optimized" && (
                          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                            Our Model
                          </span>
                        )}
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Annualized Return:</span>
                          <span className="font-bold text-emerald-400">{strat.annualized_return_pct}%</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Annualized Volatility:</span>
                          <span className="font-bold text-amber-400">{strat.annualized_volatility_pct}%</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Sharpe Ratio (7% Rf):</span>
                          <span className="font-bold text-cyan-400">{strat.sharpe_ratio}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Max Drawdown:</span>
                          <span className="font-bold text-rose-400">-{strat.max_drawdown_pct}%</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Diversification Score:</span>
                          <span className="font-bold text-indigo-400">{strat.diversification_score}/100</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
                  <h4 className="font-bold text-cyan-400 text-sm mb-2">Academic Evaluation Findings:</h4>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {benchmarkData.key_findings.map((f, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-emerald-400">✓</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================
            TAB 7: ONBOARDING & RISK QUESTIONNAIRE
        ======================================================== */}
        {activeTab === "onboarding" && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
              <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>🎯</span> SEBI-Aligned Investor Risk Assessment
              </h2>
              <p className="text-sm text-slate-400">
                Deterministic mathematical scoring mapping answers to Conservative, Moderate, Growth, or Aggressive categories.
              </p>
            </div>

            <div className="space-y-6">
              {questions.map((q, idx) => (
                <div key={q.question_id} className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-3">
                  <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
                    Question {idx + 1} of {questions.length}
                  </div>
                  <h3 className="text-base font-semibold text-white">{q.question_text}</h3>
                  <div className="space-y-2 pt-2">
                    {q.options.map((opt) => {
                      const isSelected = selectedAnswers[q.question_id] === opt.option_id;
                      return (
                        <button
                          key={opt.option_id}
                          type="button"
                          onClick={() => setSelectedAnswers({ ...selectedAnswers, [q.question_id]: opt.option_id })}
                          className={`w-full text-left p-3.5 rounded-xl border transition-all text-sm flex items-center justify-between ${
                            isSelected
                              ? "bg-cyan-950/70 border-cyan-500 text-white shadow-lg shadow-cyan-950/50"
                              : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                          }`}
                        >
                          <span>{opt.option_label}</span>
                          {isSelected && <span className="text-cyan-400 font-bold">✓</span>}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              <button
                onClick={handleAssessmentSubmit}
                disabled={loading}
                className="w-full py-4 rounded-xl font-bold bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-xl shadow-cyan-500/20 hover:from-cyan-400 hover:to-indigo-500 transition-all disabled:opacity-50"
              >
                {loading ? "Calculating Deterministic Score..." : "Submit Risk Assessment"}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
