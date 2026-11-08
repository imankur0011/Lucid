"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  loginDemoUser,
  getAuthToken,
  fetchProfile,
  fetchGoals,
  fetchRiskQuestions,
  fetchLatestAssessment,
  generatePortfolio,
  fetchPortfolios,
  runScenarioStressTest,
  createExistingPortfolio,
  analyzeExistingPortfolio,
  fetchBenchmarkEvaluation,
  logoutUser,
  PortfolioVersion,
  RiskQuestion,
  RiskAssessment,
  FinancialGoal,
  UserProfile,
  ScenarioResult,
  DiagnosisResult,
  BenchmarkComparison,
  PortfolioSummary,
} from "../lib/api";
import { NavigationTab } from "../lib/brand";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { LandingPage } from "../components/LandingPage";
import { AuthView } from "../components/AuthView";
import { OnboardingWizard, OnboardingConfig } from "../components/OnboardingWizard";
import { HoldingsView } from "../components/HoldingsView";
import { ExplainabilityView } from "../components/ExplainabilityView";
import { DiagnosisView } from "../components/DiagnosisView";
import { StressScenariosView } from "../components/StressScenariosView";
import { VersionComparisonModal } from "../components/VersionComparisonModal";
import { ProfileAuthModal } from "../components/ProfileAuthModal";
import { StockWhyModal } from "../components/StockWhyModal";
import { IconAlertTriangle, IconX } from "../components/icons";

export type AppView = "landing" | "auth" | "onboarding" | "dashboard";

export default function Home() {
  // Primary application view state machine
  const [appView, setAppView] = useState<AppView>("landing");
  const [activeTab, setActiveTab] = useState<NavigationTab>("results");

  // Loading & Generation Stepper State
  const [loading, setLoading] = useState<boolean>(false);
  const [generationStage, setGenerationStage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modals
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState<boolean>(false);
  const [isStockWhyModalOpen, setIsStockWhyModalOpen] = useState<boolean>(false);
  const [stockWhySymbol, setStockWhySymbol] = useState<string | null>(null);
  const [stockWhyCompanyName, setStockWhyCompanyName] = useState<string | undefined>(undefined);

  const handleOpenStockWhy = (symbol: string, companyName?: string) => {
    setStockWhySymbol(symbol);
    setStockWhyCompanyName(companyName);
    setIsStockWhyModalOpen(true);
  };

  // Authentication & Profile State
  const [mounted, setMounted] = useState<boolean>(false);
  const [jwtToken, setJwtToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [questions, setQuestions] = useState<RiskQuestion[]>([]);
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);

  // Generated Portfolios & History
  const [portfolio, setPortfolio] = useState<PortfolioVersion | null>(null);
  const [allPortfolios, setAllPortfolios] = useState<PortfolioSummary[]>([]);

  // Stress Scenarios & AI Assistant
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(null);
  const [runningScenario, setRunningScenario] = useState<string | null>(null);
  const [assistantInitialQuery, setAssistantInitialQuery] = useState<string | null>(null);
  const [explainabilityInitialSymbol, setExplainabilityInitialSymbol] = useState<string | null>(null);

  // Demat Diagnosis State
  const [diagnosisResult, setDiagnosisResult] = useState<DiagnosisResult | null>(null);
  const [diagnosing, setDiagnosing] = useState<boolean>(false);
  const [newHoldingsInput, setNewHoldingsInput] = useState<string>(
    "RELIANCE: 40\nTCS: 25\nHDFCBANK: 60\nINFY: 30"
  );

  // Benchmark State
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkComparison | null>(null);

  // Helper to load all authenticated user data
  const loadUserData = useCallback(async () => {
    try {
      const [prof, userGoals, qList, latestAss, ports, bench] = await Promise.allSettled([
        fetchProfile(),
        fetchGoals(),
        fetchRiskQuestions(),
        fetchLatestAssessment(),
        fetchPortfolios(),
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
      if (bench.status === "fulfilled") setBenchmarkData(bench.value);
    } catch (err: unknown) {
      console.error("Error loading user data:", err);
    }
  }, []);

  // Check initial authentication token on load
  useEffect(() => {
    setMounted(true);
    const existingToken = getAuthToken();
    if (existingToken) {
      setJwtToken(existingToken);
      loadUserData();
    }
  }, [loadUserData]);

  // Derived client-safe auth flags to prevent SSR/client hydration mismatches
  const isUserAuthenticated = mounted && Boolean(jwtToken);
  const userHasPortfolio = isUserAuthenticated && Boolean(portfolio);

  // Quick Demo Login Action
  const handleDemoLogin = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await loginDemoUser();
      setJwtToken(res.access_token);
      await loadUserData();
      setAppView("onboarding");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load demo account";
      setErrorMessage(message);
    } finally {
      setLoading(false);
    }
  };

  // Logout Handler
  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch (e) {
      console.warn("Logout error:", e);
    }
    setJwtToken(null);
    setProfile(null);
    setPortfolio(null);
    setAllPortfolios([]);
    setAssessment(null);
    setDiagnosisResult(null);
    setAppView("landing");
  };

  // Portfolio Deletion Handler
  const handlePortfolioDeleted = async () => {
    try {
      const ports = await fetchPortfolios().catch(() => []);
      setAllPortfolios(ports);
      if (ports.length > 0 && ports[0].latest_version) {
        setPortfolio(ports[0].latest_version);
      } else {
        setPortfolio(null);
        setAppView("landing");
      }
    } catch {
      setPortfolio(null);
      setAppView("landing");
    }
  };

  // Portfolio Rebalancing / Update Handler
  const handlePortfolioUpdated = async (newVersion: PortfolioVersion) => {
    setPortfolio(newVersion);
    try {
      const ports = await fetchPortfolios().catch(() => []);
      setAllPortfolios(ports);
    } catch (e) {
      console.warn("Failed to refresh portfolios after update:", e);
    }
  };

  // Full Portfolio Generation Pipeline triggered from Onboarding Wizard
  const handleGeneratePortfolio = async (config: OnboardingConfig) => {
    setLoading(true);
    setErrorMessage(null);
    setGenerationStage("Reviewing your goals, time horizon, and risk capacity...");

    const stages = [
      "Filtering candidate securities against your ethical exclusions...",
      "Evaluating verified fundamental stability and balance sheet quality...",
      "Balancing asset weights using SLSQP Sharpe ratio optimization...",
      "Calculating whole shares and verifying NSE/BSE integer lot arithmetic...",
      "Confirming fiduciary diversification and concentration safety caps...",
      "Preparing your personalized portfolio review and supporting notes...",
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
        portfolio_name: config.portfolioName,
        investment_amount: config.investmentAmount,
        investment_horizon_months: config.horizonMonths,
        risk_category: config.riskCategory,
        risk_assessment_id: config.riskAssessmentId,
        preferences: {
          excluded_sectors: config.excludedSectors,
          max_single_stock_weight_pct: config.maxStockWeight,
          max_sector_weight_pct: config.maxSectorWeight,
          ...(config.minStocksCount ? { min_stocks_count: config.minStocksCount } : {}),
        },
        user_prompt: config.userPrompt,
      });

      clearInterval(interval);
      setPortfolio(res);

      // Refresh portfolio list, latest assessment, and user profile
      const [ports, latestAss, updatedProfile] = await Promise.all([
        fetchPortfolios().catch(() => []),
        fetchLatestAssessment().catch(() => null),
        fetchProfile().catch(() => null),
      ]);
      setAllPortfolios(ports);
      if (latestAss) setAssessment(latestAss);
      if (updatedProfile) setProfile(updatedProfile);

      // Transition smoothly into Dashboard with holdings tab
      setAppView("dashboard");
      setActiveTab("results");
    } catch (err: unknown) {
      clearInterval(interval);
      const message = err instanceof Error ? err.message : "Portfolio generation failed";
      setErrorMessage(message);
    } finally {
      setLoading(false);
      setGenerationStage("");
    }
  };

  // Scenario Stress Testing
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to execute scenario";
      setErrorMessage(
        message === "Load failed"
          ? "Unable to complete stress simulation. Please ensure the backend engine is running."
          : message
      );
    } finally {
      setRunningScenario(null);
    }
  };

  // Demat Diagnosis
  const handleCreateAndDiagnose = async (
    customHoldings?: Array<{ symbol: string; quantity: number; average_purchase_price?: number }>
  ) => {
    setDiagnosing(true);
    setErrorMessage(null);
    try {
      let holdings = customHoldings;
      if (!holdings || holdings.length === 0) {
        const lines = newHoldingsInput.split("\n").filter((l) => l.trim().length > 0);
        holdings = lines.map((line) => {
          const parts = line.split(":");
          return {
            symbol: parts[0].trim().toUpperCase(),
            quantity: parseFloat(parts[1]?.trim() || "10"),
          };
        });
      }

      const portRes = await createExistingPortfolio({
        portfolio_name: "My Brokerage Portfolio (Imported)",
        holdings: holdings,
      });

      const existId = portRes.existing_portfolio_id;
      const diagRes = await analyzeExistingPortfolio(existId, assessment?.risk_category || "moderate");
      setDiagnosisResult(diagRes);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Diagnosis execution failed";
      setErrorMessage(message);
    } finally {
      setDiagnosing(false);
    }
  };

  const handleResetDiagnosis = () => {
    setDiagnosisResult(null);
    setNewHoldingsInput("RELIANCE: 40\nTCS: 25\nHDFCBANK: 60\nINFY: 30");
  };

  const handleAskAboutStock = (queryOrSymbol: string) => {
    if (
      queryOrSymbol.toLowerCase().startsWith("why") ||
      queryOrSymbol.toLowerCase().startsWith("what") ||
      queryOrSymbol.toLowerCase().startsWith("how") ||
      queryOrSymbol.toLowerCase().startsWith("simulate") ||
      queryOrSymbol.includes("?") ||
      queryOrSymbol.length > 25
    ) {
      setAssistantInitialQuery(queryOrSymbol);
    } else {
      setAssistantInitialQuery(`Why did you recommend ${queryOrSymbol} for my portfolio?`);
    }
    setActiveTab("scenarios");
    if (typeof window !== "undefined") {
      setTimeout(() => {
        window.scrollTo({ top: 160, behavior: "smooth" });
      }, 120);
    }
  };

  const handleViewReasoningInExplainability = (symbol?: string) => {
    if (symbol) {
      setExplainabilityInitialSymbol(symbol);
    }
    setActiveTab("why");
    if (typeof window !== "undefined") {
      setTimeout(() => {
        window.scrollTo({ top: 160, behavior: "smooth" });
      }, 100);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F6F1] text-[#142A3B] flex flex-col font-sans selection:bg-[#EFECE4]">
      {/* Context-aware Navigation Bar */}
      <Navbar
        appView={appView}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        assessment={assessment}
        onOpenAuthModal={async () => {
          setIsAuthModalOpen(true);
          try {
            const freshProfile = await fetchProfile();
            if (freshProfile) setProfile(freshProfile);
          } catch {
            // Non-blocking
          }
        }}
        onStartOnboarding={() => {
          if (!isUserAuthenticated && !getAuthToken()) setAppView("auth");
          else setAppView("onboarding");
        }}
        onGoToLanding={() => setAppView("landing")}
        onGoToDashboard={() => setAppView("dashboard")}
        onLogout={handleLogout}
        isAuthenticated={isUserAuthenticated}
        hasPortfolio={userHasPortfolio}
      />

      {/* Main Content Container - Fluid wide layout */}
      <main className="w-full max-w-[1440px] 2xl:max-w-[1536px] mx-auto px-4 sm:px-8 lg:px-12 py-6 sm:py-8 flex-1 space-y-10">
        {/* Global Error Banner */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#B91C1C] text-sm flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2">
              <IconAlertTriangle className="w-5 h-5 text-[#B91C1C] flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              type="button"
              className="text-[#B91C1C] hover:text-black ml-4 cursor-pointer"
              title="Dismiss error"
            >
              <IconX className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ======================================================== */}
        {/* VIEW 1: LANDING PAGE */}
        {/* ======================================================== */}
        {appView === "landing" && (
          <LandingPage
            onGetStarted={() => {
              if (isUserAuthenticated || getAuthToken()) setAppView("onboarding");
              else setAppView("auth");
            }}
            onLogin={() => setAppView("auth")}
            onDemoLogin={handleDemoLogin}
            existingPortfolio={userHasPortfolio ? portfolio : null}
            onViewExistingPortfolio={() => {
              setAppView("dashboard");
              setActiveTab("results");
            }}
            isAuthenticated={isUserAuthenticated}
            isLoading={loading}
          />
        )}

        {/* ======================================================== */}
        {/* VIEW 2: AUTH VIEW (REGISTER / LOGIN) */}
        {/* ======================================================== */}
        {appView === "auth" && (
          <AuthView
            onSuccess={async () => {
              const tok = getAuthToken();
              setJwtToken(tok);
              await loadUserData();
              setAppView("onboarding");
            }}
            onCancel={() => setAppView("landing")}
            onProfileUpdated={(updated) => setProfile(updated)}
          />
        )}

        {/* ======================================================== */}
        {/* VIEW 3: GUIDED 6-STAGE INVESTOR ONBOARDING WIZARD */}
        {/* ======================================================== */}
        {appView === "onboarding" && (
          <OnboardingWizard
            questions={questions}
            existingAssessment={assessment}
            profile={profile}
            onComplete={handleGeneratePortfolio}
            onCancel={() => {
              if (portfolio) setAppView("dashboard");
              else setAppView("landing");
            }}
            loading={loading}
            generationStage={generationStage}
          />
        )}

        {/* ======================================================== */}
        {/* VIEW 4: STREAMLINED 4-TAB DASHBOARD */}
        {/* ======================================================== */}
        {appView === "dashboard" && (
          <div className="space-y-8">
            {/* Tab 1: My Portfolio (Holdings & Allocation) */}
            {activeTab === "results" && (
              <div key="results" className="view-transition">
                <HoldingsView
                  portfolio={portfolio}
                  allPortfolios={allPortfolios}
                  onSelectVersion={(v) => setPortfolio(v)}
                  onOpenCompareModal={() => setIsCompareModalOpen(true)}
                  onGoToGenerator={() => setAppView("onboarding")}
                  onAskAboutStock={handleAskAboutStock}
                  onViewReasoning={handleViewReasoningInExplainability}
                  onPortfolioDeleted={handlePortfolioDeleted}
                  onOpenStockWhy={handleOpenStockWhy}
                  onPortfolioUpdated={handlePortfolioUpdated}
                />
              </div>
            )}

            {/* Tab 2: Why This Portfolio? (Explainability & Citations) */}
            {activeTab === "why" && (
              <div key="why" className="view-transition">
                <ExplainabilityView
                  portfolio={portfolio}
                  onGoToGenerator={() => setAppView("onboarding")}
                  onAskAboutStock={handleAskAboutStock}
                  initialSymbol={explainabilityInitialSymbol}
                  onGoToPortfolio={() => setActiveTab("results")}
                  onOpenStockWhy={handleOpenStockWhy}
                />
              </div>
            )}

            {/* Tab 3: Stress Tests & AI Assistant */}
            {activeTab === "scenarios" && (
              <div key="scenarios" className="view-transition">
                <StressScenariosView
                  portfolio={portfolio}
                  scenarioResult={scenarioResult}
                  runningScenario={runningScenario}
                  onRunScenario={handleRunScenario}
                  onGoToGenerator={() => setAppView("onboarding")}
                  initialQuery={assistantInitialQuery}
                  existingPortfolioId={diagnosisResult?.existing_portfolio_id}
                />
              </div>
            )}

            {/* Tab 4: Demat Diagnosis & Rebalancing */}
            {activeTab === "diagnosis" && (
              <div key="diagnosis" className="view-transition">
                <DiagnosisView
                  holdingsInput={newHoldingsInput}
                  setHoldingsInput={setNewHoldingsInput}
                  diagnosisResult={diagnosisResult}
                  diagnosing={diagnosing}
                  onDiagnose={handleCreateAndDiagnose}
                  onAskAboutRebalance={handleAskAboutStock}
                  onResetDiagnosis={handleResetDiagnosis}
                  riskCategory={assessment?.risk_category || "moderate"}
                />
              </div>
            )}
          </div>
        )}

        {/* Fiduciary Regulatory Footer */}
        <Footer />
      </main>

      {/* Version Comparison Modal */}
      <VersionComparisonModal
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        allPortfolios={allPortfolios}
      />

      {/* Stock-Specific 'Ask AI Why' Equity Research Modal */}
      {portfolio && (
        <StockWhyModal
          isOpen={isStockWhyModalOpen}
          onClose={() => setIsStockWhyModalOpen(false)}
          portfolioId={portfolio.portfolio_id}
          versionId={portfolio.portfolio_version_id}
          symbol={stockWhySymbol}
          companyName={stockWhyCompanyName}
        />
      )}

      {/* Profile & Security Modal */}
      <ProfileAuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        profile={profile}
        goals={goals}
        jwtToken={jwtToken}
        onTokenUpdated={(tok) => {
          setJwtToken(tok);
          loadUserData();
        }}
        assessment={assessment}
        onStartOnboarding={() => {
          setIsAuthModalOpen(false);
          setAppView("onboarding");
        }}
        onLogout={handleLogout}
        activePortfolio={portfolio}
        allPortfolios={allPortfolios}
        onPortfolioDeleted={handlePortfolioDeleted}
      />

      {/* Floating Ask Lucid AI Copilot Launcher */}
      {appView === "dashboard" && activeTab !== "scenarios" && (
        <button
          onClick={() => setActiveTab("scenarios")}
          type="button"
          aria-label="Open AI Copilot"
          className="fixed bottom-6 right-6 z-40 px-5 py-3 rounded-full bg-[#142A3B] hover:bg-[#0E1E2B] text-white font-bold text-sm shadow-xl hover:shadow-2xl flex items-center gap-2.5 transition-all cursor-pointer border border-[#285C4D]"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-[#285C4D] animate-pulse"></span>
          <span>Ask Lucid AI</span>
        </button>
      )}
    </div>
  );
}
