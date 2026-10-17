/**
 * API client library for the Intelligent Portfolio Creation Backend.
 * Supports authentication tokens, diagnosis/rebalancing, comparisons, and backtesting benchmarks.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (typeof window !== "undefined") {
    if (token) localStorage.setItem("samruddhi_jwt", token);
    else localStorage.removeItem("samruddhi_jwt");
  }
}

export function getAuthToken(): string | null {
  if (authToken) return authToken;
  if (typeof window !== "undefined") {
    authToken = localStorage.getItem("samruddhi_jwt");
  }
  return authToken;
}

function getHeaders(contentType: boolean = true): HeadersInit {
  const headers: Record<string, string> = {};
  if (contentType) headers["Content-Type"] = "application/json";
  const token = getAuthToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function loginDemoUser(email?: string): Promise<{ access_token: string; user_id: string; email: string }> {
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email || "investor@example.invalid", demo_user: !email }),
  });
  if (!res.ok) throw new Error("Failed to obtain authentication token");
  const data = await res.json();
  setAuthToken(data.access_token);
  return data;
}

export interface UserProfile {
  user_id: string;
  display_name: string;
  country_code: string;
  preferred_currency: string;
  investment_experience: string;
  investment_knowledge_level: string;
}

export interface FinancialGoal {
  goal_id: string;
  goal_name: string;
  goal_type: string;
  target_amount: number;
  amount_already_saved: number;
  priority: number;
  goal_status: string;
}

export interface RiskOption {
  option_id: string;
  option_code: string;
  option_label: string;
  score: number;
  display_order: number;
}

export interface RiskQuestion {
  question_id: string;
  question_code: string;
  question_text: string;
  answer_type: string;
  options: RiskOption[];
}

export type CanonicalRiskCategory =
  | 'very_conservative'
  | 'conservative'
  | 'moderate'
  | 'growth'
  | 'aggressive';

export interface RiskAssessment {
  risk_assessment_id: string;
  risk_tolerance_score: number;
  risk_capacity_score: number;
  risk_category: CanonicalRiskCategory;
  assessment_status: string;
  completed_at: string;
}

export interface HoldingItem {
  security_id: string;
  symbol: string;
  security_name: string;
  sector_name: string;
  target_weight_pct: number;
  target_amount: number;
  shares_quantity: number;
  latest_price: number;
  decision_reason: string;
}

export interface ValidationItem {
  rule_code: string;
  result_status: string;
  severity: string;
  result_message: string;
  actual_value?: number;
  threshold_value?: number;
}

export interface ExplanationItem {
  explanation_id: string;
  explanation_type: string;
  title: string;
  explanation_text: string;
  display_order: number;
  evidence?: any[];
}

export interface PortfolioVersion {
  portfolio_version_id: string;
  portfolio_id: string;
  version_number: number;
  version_status: string;
  investment_amount: number;
  currency_code: string;
  risk_category: string;
  expected_return_pct: number;
  expected_volatility_pct: number;
  diversification_score: number;
  generated_at: string;
  holdings: HoldingItem[];
  validation_status: string;
  validation_results: ValidationItem[];
  explanations: ExplanationItem[];
}

export interface ScenarioResult {
  scenario_code: string;
  scenario_name: string;
  scenario_type: string;
  baseline_value: number;
  stressed_value: number;
  loss_amount: number;
  loss_pct: number;
  impact_summary: string;
}

export interface RebalanceSuggestion {
  security_id: string;
  symbol: string;
  action: "buy" | "sell" | "hold";
  current_quantity: number;
  target_quantity: number;
  quantity_change: number;
  current_value: number;
  target_value: number;
  change_value: number;
  explanation: string;
}

export interface DiagnosisResult {
  portfolio_diagnosis_id: string;
  existing_portfolio_id: string;
  portfolio_name: string;
  total_market_value: number;
  warnings: string[];
  current_metrics: Record<string, any>;
  target_metrics: Record<string, any>;
  rebalance_turnover_pct: number;
  unallocated_cash: number;
  suggestions: RebalanceSuggestion[];
  created_at: string;
}

export interface BenchmarkComparison {
  evaluation_date: string;
  risk_category: string;
  investment_capital: number;
  strategies: Record<string, any>;
  key_findings: string[];
  methodology_notes: string;
}

// User Profile & Goals
export async function fetchProfile(): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/profile`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch investor profile");
  return res.json();
}

export async function updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/profile`, {
    method: "PATCH",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update profile");
  return res.json();
}

export async function fetchRiskQuestions(): Promise<RiskQuestion[]> {
  const res = await fetch(`${API_BASE}/risk-questions`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to load risk questions");
  return res.json();
}

export async function submitRiskAssessment(answers: Array<{ question_id: string; selected_option_id: string }>): Promise<RiskAssessment> {
  const res = await fetch(`${API_BASE}/risk-assessments`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) throw new Error("Failed to submit risk assessment");
  return res.json();
}

export async function fetchLatestAssessment(): Promise<RiskAssessment | null> {
  const res = await fetch(`${API_BASE}/risk-assessments/latest`, { headers: getHeaders() });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to load latest assessment");
  return res.json();
}

export async function fetchGoals(): Promise<FinancialGoal[]> {
  const res = await fetch(`${API_BASE}/goals`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch goals");
  return res.json();
}

export async function createGoal(data: { goal_name: string; goal_type: string; target_amount: number }): Promise<FinancialGoal> {
  const res = await fetch(`${API_BASE}/goals`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create goal");
  return res.json();
}

// Portfolio Generation & Versions
export async function generatePortfolio(payload: {
  portfolio_name?: string;
  investment_amount: number;
  investment_horizon_months: number;
  preferences?: {
    excluded_sectors?: string[];
    excluded_instruments?: string[];
    max_single_stock_weight_pct?: number;
    max_sector_weight_pct?: number;
  };
  user_prompt?: string;
}): Promise<PortfolioVersion> {
  const res = await fetch(`${API_BASE}/portfolio-generation-requests`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Portfolio generation failed");
  }
  return res.json();
}

export async function fetchPortfolios(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/portfolios`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch portfolios");
  return res.json();
}

export async function fetchExplanations(portfolioId: string, versionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/versions/${versionId}/explanations`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch explanations");
  return res.json();
}

export async function comparePortfolioVersions(
  portfolioId: string,
  versionAId: string,
  versionBId: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/compare`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ version_a_id: versionAId, version_b_id: versionBId }),
  });
  if (!res.ok) throw new Error("Failed to compare versions");
  return res.json();
}

export async function runScenarioStressTest(
  portfolioId: string,
  payload: { scenario_type: string; scenario_name: string; drop_pct: number; affected_sector?: string }
): Promise<ScenarioResult> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/scenarios`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to run scenario");
  return res.json();
}

// Diagnosis & Rebalancing
export async function createExistingPortfolio(payload: {
  portfolio_name: string;
  holdings: Array<{ symbol: string; quantity: number; average_purchase_price?: number }>;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/diagnosis/portfolios`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to register existing portfolio");
  return res.json();
}

export async function listExistingPortfolios(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/diagnosis/portfolios`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to list existing portfolios");
  return res.json();
}

export async function analyzeExistingPortfolio(
  existingPortfolioId: string,
  riskCategory: string = "moderate"
): Promise<DiagnosisResult> {
  const res = await fetch(`${API_BASE}/diagnosis/analyze/${existingPortfolioId}?risk_category=${riskCategory}`, {
    method: "POST",
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Diagnosis failed");
  }
  return res.json();
}

// Benchmark Evaluation
export async function fetchBenchmarkEvaluation(
  riskCategory: string = "moderate",
  amount: number = 100000
): Promise<BenchmarkComparison> {
  const res = await fetch(`${API_BASE}/portfolios/benchmark-evaluation?risk_category=${riskCategory}&amount=${amount}`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load benchmark evaluation");
  return res.json();
}
