/**
 * API client library for the Intelligent Portfolio Creation Backend.
 * Supports authentication tokens, diagnosis/rebalancing, comparisons, and backtesting benchmarks.
 */

function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") {
    // Both localhost and 127.0.0.1 default to 127.0.0.1:8000
    // This avoids Windows 10/11 Chrome/Edge IPv6 [::1] loopback connection drops when Uvicorn is bound to IPv4 (0.0.0.0)
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://127.0.0.1:8000/api/v1";
    }
    return `http://${window.location.hostname}:8000/api/v1`;
  }
  return "http://127.0.0.1:8000/api/v1";
}

const API_BASE = {
  toString: getApiBase,
  valueOf: getApiBase,
};

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
  const cleanEmail = email ? email.trim().toLowerCase() : undefined;
  const payload = JSON.stringify({ email: cleanEmail, demo_user: !cleanEmail });

  let res = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
  }).catch(() => null);

  if (!res || !res.ok) {
    // Retry via /auth/login alias
    res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
    }).catch(() => null);
  }

  if (!res || !res.ok) {
    const errData = res ? await res.json().catch(() => ({})) : {};
    throw new Error(errData.detail || "Failed to obtain authentication token. Ensure Lucid backend is running.");
  }
  const data = await res.json();
  setAuthToken(data.access_token);
  return data;
}

export async function registerUser(
  email: string,
  password?: string,
  mobileNumber?: string,
): Promise<{ access_token: string; user_id: string; email: string }> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password: password || undefined,
      mobile_number: mobileNumber ? mobileNumber.trim() : undefined,
      demo_user: false,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed. Please check your details.");
  }
  const data = await res.json();
  setAuthToken(data.access_token);
  return data;
}

export async function loginWithCredentials(email: string, password?: string): Promise<{ access_token: string; user_id: string; email: string }> {
  const cleanEmail = email.trim().toLowerCase();
  const payload = JSON.stringify({ email: cleanEmail, password: password || undefined, demo_user: false });

  let res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
  }).catch(() => null);

  if (!res || !res.ok) {
    // Retry via /auth/token
    res = await fetch(`${API_BASE}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
    }).catch(() => null);
  }

  if (!res || !res.ok) {
    const err = res ? await res.json().catch(() => ({})) : {};
    throw new Error(err.detail || "Login failed. Incorrect email or password.");
  }
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
  mobile_number?: string;
  version_number?: number;
  created_at?: string;
  updated_at?: string;
}

export interface AppUser {
  user_id: string;
  identity_provider: string;
  identity_subject: string;
  email: string | null;
  email_verified: boolean;
  mobile_number: string | null;
  mobile_verified: boolean;
  account_status: string;
  profile?: UserProfile | null;
  created_at: string;
  updated_at: string;
}

export async function fetchCurrentUser(): Promise<AppUser | null> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getHeaders(),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function changePassword(newPassword: string, currentPassword?: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/auth/change-password`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ current_password: currentPassword || undefined, new_password: newPassword }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update password");
  }
  return res.json();
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

export interface ExtractedProfileData {
  portfolio_name: string;
  investment_amount: number;
  horizon_months: number;
  risk_category: string;
  experience_level: string;
  knowledge_level: string;
  emergency_fund_status: string;
  loss_capacity_emergency_months?: number;
  goal_type: string;
  goal_name: string;
  target_corpus: number;
  preferred_sectors: string[];
  excluded_sectors: string[];
  user_prompt: string;
}

export interface ProfileNLPExtractResponse {
  extracted_profile: ExtractedProfileData;
  mapped_option_codes: Record<string, string>;
  fiduciary_notes: string[];
  confidence_score: number;
  extraction_method: string;
  resolved_questionnaire_answers?: Array<{
    question_id: string;
    question_code: string;
    question_text: string;
    selected_option_id: string;
    selected_option_code: string;
    selected_option_label: string;
    score: number;
  }>;
}

export async function extractProfileFromText(text: string): Promise<ProfileNLPExtractResponse> {
  const res = await fetch(`${API_BASE}/profile/extract-from-text`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to extract profile from natural language");
  }
  return res.json();
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
  scoring_config?: {
    weight?: number;
    category?: string;
  };
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

export type HoldingAllocation = HoldingItem;

export interface ValidationItem {
  rule_code: string;
  result_status: string;
  severity: string;
  result_message: string;
  actual_value?: number;
  threshold_value?: number;
}

export interface EvidenceItem {
  evidence_id?: string;
  source_type?: string;
  source_name?: string;
  content_snippet?: string;
  relevance_score?: number;
}

export interface ExplanationItem {
  explanation_id: string;
  explanation_type: string;
  title: string;
  explanation_text: string;
  display_order: number;
  evidence?: EvidenceItem[];
  source_url?: string;
  evidence_title?: string;
}

export interface PortfolioVersion {
  portfolio_version_id: string;
  portfolio_id: string;
  portfolio_name?: string;
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
  current_weight_pct?: number;
  target_weight_pct?: number;
  latest_price?: number;
}

export interface CurrentHoldingDetail {
  symbol: string;
  security_name: string;
  sector_name: string;
  quantity: number;
  latest_price: number;
  current_value: number;
  weight_pct: number;
  average_purchase_price?: number | null;
  invested_amount?: number | null;
  unrealized_pnl?: number | null;
  unrealized_pnl_pct?: number | null;
}

export interface ParsedHoldingPreview {
  row_number: number;
  symbol: string;
  security_name: string;
  exchange: string;
  quantity: number;
  average_purchase_price?: number | null;
  latest_market_price: number;
  current_market_value: number;
  unrealized_pnl?: number | null;
  unrealized_pnl_pct?: number | null;
  sector_name: string;
}

export interface InvalidRowError {
  row_number: number;
  raw_symbol?: string | null;
  error: string;
}

export interface PortfolioImportPreviewResponse {
  status: string;
  source_type: string;
  filename?: string | null;
  total_rows: number;
  valid_count: number;
  error_count: number;
  can_commit: boolean;
  total_estimated_value: number;
  valid_holdings: ParsedHoldingPreview[];
  invalid_rows: InvalidRowError[];
}

export interface DiagnosisResult {
  portfolio_diagnosis_id: string;
  existing_portfolio_id: string;
  portfolio_name: string;
  total_market_value: number;
  warnings: string[];
  current_metrics: Record<string, number | string>;
  target_metrics: Record<string, number | string>;
  rebalance_turnover_pct: number;
  unallocated_cash: number;
  suggestions: RebalanceSuggestion[];
  current_holdings?: CurrentHoldingDetail[];
  rebalance_status?: "no_trades_required" | "rebalance_proposed" | string;
  trades_required_count?: number;
  created_at: string;
}

export interface StrategyPerformance {
  strategy_name: string;
  annualized_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  diversification_score: number;
}

export interface BenchmarkComparison {
  evaluation_date: string;
  risk_category: string;
  investment_capital: number;
  strategies: Record<string, StrategyPerformance>;
  key_findings: string[];
  methodology_notes: string;
}

export interface VersionMetricSnapshot {
  portfolio_id?: string;
  portfolio_name?: string;
  version_id: string;
  version_number: number;
  risk_category?: string;
  investment_amount: number;
  expected_return_pct: number;
  expected_volatility_pct: number;
  diversification_score: number;
  holdings_count?: number;
}

export interface HoldingComparisonItem {
  symbol: string;
  security_name: string;
  sector_name: string;
  weight_version_a: number;
  weight_version_b: number;
  weight_delta: number;
  shares_version_a?: number;
  shares_version_b?: number;
  status?: "both" | "added_in_b" | "removed_in_b" | string;
}

export interface PortfolioComparisonResult {
  portfolio_id: string;
  version_a: VersionMetricSnapshot;
  version_b: VersionMetricSnapshot;
  deltas: {
    delta_return_pct: number;
    delta_volatility_pct: number;
    delta_diversification: number;
  };
  holdings_comparison: HoldingComparisonItem[];
}

export interface PortfolioSummary {
  portfolio_id: string;
  portfolio_name: string;
  user_id: string;
  latest_version?: PortfolioVersion;
  versions_count?: number;
  created_at: string;
}

export interface ExistingPortfolioItem {
  existing_portfolio_id: string;
  portfolio_name: string;
  user_id: string;
  created_at: string;
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
  risk_category?: string;
  risk_assessment_id?: string;
  preferences?: {
    excluded_sectors?: string[];
    excluded_instruments?: string[];
    max_single_stock_weight_pct?: number;
    max_sector_weight_pct?: number;
    min_stocks_count?: number;
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

export async function fetchPortfolios(): Promise<PortfolioSummary[]> {
  const res = await fetch(`${API_BASE}/portfolios`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch portfolios");
  return res.json();
}

export async function fetchExplanations(portfolioId: string, versionId: string): Promise<ExplanationItem[]> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/versions/${versionId}/explanations`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch explanations");
  return res.json();
}

export async function fetchPortfolioVersions(portfolioId: string): Promise<PortfolioVersion[]> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/versions`, {
    headers: getHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function comparePortfolioVersions(
  portfolioId: string | null | undefined,
  versionAId: string,
  versionBId: string
): Promise<PortfolioComparisonResult> {
  const endpoint = portfolioId ? `${API_BASE}/portfolios/${portfolioId}/compare` : `${API_BASE}/portfolios/compare`;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ version_a_id: versionAId, version_b_id: versionBId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to compare versions");
  }
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
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to execute scenario stress simulation");
  }
  return res.json();
}

// Diagnosis & Rebalancing
export async function downloadCsvTemplate(): Promise<string> {
  const res = await fetch(`${API_BASE}/diagnosis/csv-template`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to download CSV template");
  return res.text();
}

export async function uploadHoldingsCsv(file: File): Promise<PortfolioImportPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const headers = getHeaders();
  // Let the browser set the multi-part boundary
  delete (headers as Record<string, string>)["Content-Type"];

  const res = await fetch(`${API_BASE}/diagnosis/upload-csv`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to process CSV upload");
  }
  return res.json();
}

export async function parseHoldingsText(
  text: string,
  sourceType: string = "copy_paste"
): Promise<PortfolioImportPreviewResponse> {
  const res = await fetch(`${API_BASE}/diagnosis/parse-text`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ text, source_type: sourceType }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to parse holdings text");
  }
  return res.json();
}

export async function createExistingPortfolio(payload: {
  portfolio_name: string;
  holdings: Array<{ symbol: string; quantity: number; average_purchase_price?: number }>;
}): Promise<{ existing_portfolio_id: string; portfolio_name: string }> {
  const res = await fetch(`${API_BASE}/diagnosis/portfolios`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to register existing portfolio");
  return res.json();
}

export async function listExistingPortfolios(): Promise<ExistingPortfolioItem[]> {
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

// Conversational Fiduciary Assistant & Dynamic Stress Testing (FR-D01 & FR-D08)
export interface HoldingImpact {
  symbol: string;
  security_name: string;
  sector_name: string;
  weight_pct: number;
  simulated_change_pct: number;
  contribution_to_loss_pct: number;
  role_description: string;
}

export interface ScenarioSimulationDetail {
  scenario_title: string;
  scenario_type: string;
  baseline_value: number;
  stressed_value: number;
  loss_amount: number;
  loss_pct: number;
  cushion_effect: string;
  historical_recovery_context: string;
  holding_impacts: HoldingImpact[];
}

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface PortfolioChatResponse {
  reply: string;
  scenario_simulation?: ScenarioSimulationDetail | null;
  suggested_followups: string[];
  intent?: string | null;
  session_id?: string | null;
}

export async function chatWithPortfolioAssistant(
  portfolioId: string,
  message: string,
  history?: ChatHistoryMessage[],
  sessionId?: string
): Promise<PortfolioChatResponse> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/chat`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ message, history, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to communicate with fiduciary assistant");
  }
  return res.json();
}

export async function chatWithGeneralAssistant(
  message: string,
  history?: ChatHistoryMessage[],
  sessionId?: string,
  portfolioId?: string,
  existingPortfolioId?: string
): Promise<PortfolioChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({
      message,
      history,
      session_id: sessionId,
      portfolio_id: portfolioId,
      existing_portfolio_id: existingPortfolioId,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to communicate with assistant");
  }
  return res.json();
}

// ============================================================
// Stock-Specific "Ask AI Why?" API Methods (FR-D01 & Deliberation)
// ============================================================

export interface TwoLevelParameterExplanation {
  parameter_name: string;
  value: string;
  unit: string;
  level_1_summary: {
    what_it_means: string;
    why_it_matters: string;
    how_to_interpret: string;
    why_it_matters_for_portfolio: string;
  };
  level_2_deep_dive: {
    detailed_definition: string;
    purpose: string;
    actual_value: string;
    interpretation: string;
    benchmark_comparison: string;
    calculation_methodology: string;
    why_favorable_or_unfavorable: string;
    investment_implications: string;
    portfolio_implications: string;
    limitations: string;
    evidence_source: string;
    observation_date: string;
    verification_status: string;
  };
}

export interface StockWhyExplanationResponse {
  portfolio_id: string;
  version_id: string;
  symbol: string;
  company_name: string;
  sector: string;
  current_price: number;
  shares_quantity: number;
  target_weight_pct: number;
  target_amount: number;
  actual_allocated_amount: number;
  unallocated_cash: number;
  portfolio_capital: number;
  portfolio_unallocated_cash: number;
  section_1_why_selected: {
    title: string;
    company_name: string;
    symbol: string;
    sector: string;
    portfolio_role: string;
    core_thesis: string;
    alternatives_evaluated: string;
    investor_alignment: string;
  };
  section_2_fundamental_analysis: {
    title: string;
    parameters: TwoLevelParameterExplanation[];
    fiduciary_summary: string;
  };
  section_3_valuation_analysis: {
    title: string;
    trailing_pe: number;
    industry_pe_median: number;
    three_year_cagr_pct: number;
    dividend_yield_pct: number;
    valuation_verdict: string;
    multiple_expansion_potential: string;
    multiple_compression_risk: string;
  };
  section_4_market_and_sector: {
    title: string;
    sector: string;
    sector_headwinds_tailwinds: string;
    relative_performance_vs_nifty: string;
    sector_concentration_check: string;
  };
  section_5_macro_and_news: {
    title: string;
    rbi_monetary_policy_impact: string;
    inflation_and_gdp_context: string;
    primary_filing_url?: string;
    nse_filing_url?: string;
    bse_filing_url?: string;
    ir_portal_url?: string;
    verified_exchange_filings: Array<{
      exchange: string;
      filing_type: string;
      date: string;
      status: string;
      summary: string;
      portal_url?: string;
    }>;
  };
  section_6_risk_analysis: {
    title: string;
    systematic_risk: string;
    idiosyncratic_risks: string[];
    stress_test_simulations: {
      broad_market_shock_minus_20: {
        scenario: string;
        projected_stock_impact_pct: string;
        containment_strategy: string;
      };
      sector_headwind_minus_15: {
        scenario: string;
        projected_portfolio_impact_pct: string;
        containment_strategy: string;
      };
    };
  };
  section_7_why_this_allocation: {
    title: string;
    target_weight_pct: number;
    target_amount: number;
    current_price: number;
    shares_quantity: number;
    actual_allocated_amount: number;
    unallocated_cash_remainder: number;
    math_proof: string;
    why_not_higher: string;
    why_not_lower: string;
    whole_share_enforcement: string;
  };
  section_8_agent_contributions: {
    title: string;
    contributions: Array<{
      agent_name: string;
      role: string;
      finding: string;
    }>;
  };
  section_9_what_could_make_this_wrong: {
    title: string;
    thesis_invalidation_catalysts: string[];
    monitoring_triggers: string;
  };
  section_10_final_conclusion: {
    title: string;
    executive_summary: string;
    suitability_statement: string;
    primary_risk_to_monitor: string;
  };
  suggested_followups: string[];
}

export interface StockWhyChatResponse {
  reply: string;
  symbol: string;
  company_name: string;
  suggested_followups: string[];
}

export async function fetchStockWhyExplanation(
  portfolioId: string,
  versionId: string,
  symbol: string
): Promise<StockWhyExplanationResponse> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/versions/${versionId}/stocks/${encodeURIComponent(symbol)}/why`, {
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch explanation for ${symbol}`);
  }
  return res.json();
}

export async function sendStockWhyChat(
  portfolioId: string,
  versionId: string,
  symbol: string,
  message: string,
  history?: Array<{ role: string; content: string }>
): Promise<StockWhyChatResponse> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/versions/${versionId}/stocks/${encodeURIComponent(symbol)}/chat`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to chat about ${symbol}`);
  }
  return res.json();
}

// ============================================================
// Auth & Verification API Methods (4.3 & 4.4)
// ============================================================

export async function requestVerification(
  recipient: string,
  codeType: "email_verification" | "mobile_verification" = "email_verification"
) {
  const res = await fetch(`${API_BASE}/auth/request-verification`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ recipient, code_type: codeType }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to request verification code");
  }
  return res.json();
}

export async function verifyCode(
  recipient: string,
  code: string,
  codeType: "email_verification" | "mobile_verification" = "email_verification"
) {
  const res = await fetch(`${API_BASE}/auth/verify-code`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ recipient, code, code_type: codeType }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Verification failed");
  }
  return res.json();
}

export async function forgotPassword(email: string) {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to send reset instructions");
  }
  return res.json();
}

export async function resetPassword(email: string, code: string, newPassword: string) {
  const res = await fetch(`${API_BASE}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code, new_password: newPassword }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to reset password");
  }
  return res.json();
}

export async function logoutUser() {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: getHeaders(),
    });
  } catch (e) {
    // Ignore network errors on logout
  }
  setAuthToken(null);
}

// ============================================================
// Profile History & Market Regime Methods (5.7, 6.11, 6.4, 6.5)
// ============================================================

export interface UserProfileVersion {
  profile_version_id: string;
  user_id: string;
  version_number: number;
  display_name: string | null;
  country_code: string;
  preferred_currency: string;
  investment_experience: string | null;
  investment_knowledge_level: string | null;
  change_summary: string | null;
  created_at: string;
}

export async function getProfileVersions(): Promise<UserProfileVersion[]> {
  const res = await fetch(`${API_BASE}/profile/versions`, {
    headers: getHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

export interface MarketRegimeData {
  regime: "CALM" | "MODERATE" | "VOLATILE" | "EXTREME";
  india_vix: number;
  realized_volatility_pct: number;
  risk_multiplier: number;
  cash_buffer_pct: number;
  max_single_stock_tilt: number;
  description: string;
  guidance: string;
  as_of: string;
}

export async function getMarketRegime(vix?: number): Promise<MarketRegimeData> {
  const url = vix ? `${API_BASE}/market-data/regime?vix=${vix}` : `${API_BASE}/market-data/regime`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch market regime");
  return res.json();
}

export async function getMacroIndicators() {
  const res = await fetch(`${API_BASE}/market-data/macro-indicators`);
  if (!res.ok) throw new Error("Failed to fetch macro indicators");
  return res.json();
}

export async function getMarketNews(symbol?: string) {
  const url = symbol ? `${API_BASE}/market-data/news?symbol=${symbol}` : `${API_BASE}/market-data/news`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch market news");
  return res.json();
}

export interface TradeOrder {
  symbol: string;
  security_name: string;
  sector_name: string;
  exchange: string;
  action: "BUY" | "SELL";
  shares_quantity: number;
  limit_price: number;
  order_type: string;
  product: string;
  target_weight_pct: number;
  allocated_amount: number;
}

export interface TradeBasketExport {
  portfolio_id: string;
  version_id: string;
  version_number: number;
  investment_amount: number;
  total_invested: number;
  unallocated_cash: number;
  total_orders: number;
  orders: TradeOrder[];
  generated_at: string;
}

export async function exportPortfolioOrders(
  portfolioId: string,
  versionId: string,
  format: "json" | "csv" | "zerodha_csv" = "json"
): Promise<TradeBasketExport | string> {
  const url = `${API_BASE}/portfolios/${portfolioId}/versions/${versionId}/export-orders?export_format=${format}`;
  const res = await fetch(url, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to export portfolio orders");
  if (format === "csv" || format === "zerodha_csv") {
    return res.text();
  }
  return res.json();
}

/**
 * Permanently deletes an individual investor portfolio and all dependent records.
 */
export async function deletePortfolio(portfolioId: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete portfolio");
  }
  return res.json();
}

/**
 * Permanently deletes multiple selected portfolios in a single batch operation.
 */
export async function deletePortfoliosBatch(
  portfolioIds: string[]
): Promise<{ success: boolean; deleted_count: number; message: string }> {
  const res = await fetch(`${API_BASE}/portfolios/batch-delete`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ portfolio_ids: portfolioIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete selected portfolios");
  }
  return res.json();
}

/**
 * Permanently deletes ALL portfolios belonging to the authenticated user.
 */
export async function deleteAllPortfolios(): Promise<{ success: boolean; deleted_count: number; message: string }> {
  const res = await fetch(`${API_BASE}/portfolios`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete all portfolios");
  }
  return res.json();
}

/**
 * Permanently deletes an imported / diagnosed portfolio and its diagnoses.
 */
export async function deleteImportedPortfolio(portfolioId: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/diagnosis/portfolios/${portfolioId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete imported portfolio");
  }
  return res.json();
}

/**
 * Exports all user data, profiles, preferences, financial goals, risk assessments,
 * and portfolio versions as structured JSON (GDPR & SEBI data portability).
 */
export async function exportUserData(): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE}/profile/export`, {
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to export user data");
  }
  return res.json();
}

/**
 * Permanently deletes the investor account, active tokens, and all associated personal data.
 */
export async function deleteAccount(payload: {
  password?: string;
  confirmationPhrase: string;
}): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/profile/delete-account`, {
    method: "POST",
    headers: getHeaders(true),
    body: JSON.stringify({
      password: payload.password || undefined,
      confirmation_phrase: payload.confirmationPhrase,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete account");
  }
  return res.json();
}

// ============================================================
// Diagnosis AI Copilot Interfaces & API Methods
// ============================================================

export interface DiagnosisProblemItem {
  issue: string;
  policy_origin: string;
  impact: string;
}

export interface DiagnosisTradeExplanation {
  symbol: string;
  company_name: string;
  sector: string;
  action: "BUY" | "SELL" | "HOLD" | string;
  current_quantity: number;
  current_value: number;
  current_weight_pct: number;
  target_quantity: number;
  target_value: number;
  target_weight_pct: number;
  proposed_trade_quantity: number;
  reference_price: number;
  estimated_trade_value: number;
  remaining_quantity: number;
  reason: string;
}

export interface DiagnosisMetricComparison {
  current: string | number;
  proposed: string | number;
}

export interface DiagnosisBeforeAfterComparison {
  total_portfolio_value: DiagnosisMetricComparison;
  holdings_count: DiagnosisMetricComparison;
  largest_stock_weight: DiagnosisMetricComparison;
  it_sector_exposure: DiagnosisMetricComparison;
  diversification_score: DiagnosisMetricComparison;
  cash_remaining: DiagnosisMetricComparison;
  [key: string]: DiagnosisMetricComparison;
}

export interface DiagnosisCopilotExplanation {
  existing_portfolio_id: string;
  diagnosis_id: string;
  portfolio_name: string;
  total_market_value: number;
  effective_stock_limit: number;
  effective_sector_limit: number;
  unallocated_cash: number;
  rebalance_turnover_pct: number;
  section_1_portfolio_summary: string;
  section_2_problems_identified: DiagnosisProblemItem[];
  section_3_proposed_trades: DiagnosisTradeExplanation[];
  section_4_why_recommended: string[];
  section_5_before_after_comparison: DiagnosisBeforeAfterComparison;
  section_6_remaining_risks: string[];
  section_7_final_fiduciary_summary: string;
  suggested_followups: string[];
}

export interface DiagnosisChatResponse {
  reply: string;
  portfolio_name: string;
  suggested_followups: string[];
}

/**
 * Fetches the 7-part AI Copilot explanation for an imported brokerage portfolio diagnosis.
 */
export async function fetchDiagnosisExplanation(
  existingPortfolioId: string
): Promise<DiagnosisCopilotExplanation> {
  const res = await fetch(`${API_BASE}/diagnosis/${existingPortfolioId}/explanation`, {
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load diagnosis explanation");
  }
  return res.json();
}

/**
 * Chats with the Diagnosis Copilot regarding an imported portfolio's rebalancing plan.
 */
export async function sendDiagnosisChat(
  existingPortfolioId: string,
  message: string,
  history?: Array<{ role: string; content: string }>
): Promise<DiagnosisChatResponse> {
  const res = await fetch(`${API_BASE}/diagnosis/${existingPortfolioId}/chat`, {
    method: "POST",
    headers: getHeaders(true),
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to communicate with diagnosis copilot");
  }
  return res.json();
}

export interface AppNotification {
  notification_id: string;
  notification_type: string;
  title: string;
  message: string;
  delivery_channel: string;
  delivery_status: string;
  created_at: string;
  sent_at?: string | null;
  read_at?: string | null;
  dismissed_at?: string | null;
  metadata?: Record<string, any>;
}

export async function fetchNotifications(unreadOnly = false): Promise<AppNotification[]> {
  const res = await fetch(`${API_BASE}/notifications?unread_only=${unreadOnly}`, {
    headers: getHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchUnreadNotificationCount(): Promise<number> {
  const res = await fetch(`${API_BASE}/notifications/unread-count`, {
    headers: getHeaders(),
  });
  if (!res.ok) return 0;
  const data = await res.json();
  return data.unread_count || 0;
}

export async function markNotificationRead(notificationId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
    method: "PUT",
    headers: getHeaders(),
  });
  return res.ok;
}

export async function markAllNotificationsRead(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/notifications/mark-all-read`, {
    method: "PUT",
    headers: getHeaders(),
  });
  return res.ok;
}

export async function dismissNotification(notificationId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/notifications/${notificationId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  return res.ok;
}

// -----------------------------------------------------------------------------
// PORTFOLIO MONITORING & REBALANCING (FR-C07, FR-C08)
// -----------------------------------------------------------------------------

export interface HoldingMonitoringData {
  security_id: string;
  symbol: string;
  company_name: string;
  sector_name: string;
  shares_quantity: number;
  latest_price: number;
  current_value: number;
  target_weight_pct: number;
  current_weight_pct: number;
  weight_drift_pct: number;
  abs_drift_pct: number;
  target_value: number;
  pnl_amount: number;
  pnl_pct: number;
  drift_status: "ALIGNED" | "MILD_DRIFT" | "SEVERE_DRIFT";
}

export interface SectorExposureData {
  sector_name: string;
  current_value: number;
  current_weight_pct: number;
  target_weight_pct: number;
  sector_drift_pct: number;
}

export interface PortfolioMonitoringResponse {
  portfolio_id: string;
  portfolio_name: string;
  as_of_date: string;
  total_equity_value: number;
  unallocated_cash: number;
  total_portfolio_value: number;
  holdings_count: number;
  max_weight_drift_pct: number;
  rebalance_recommended: boolean;
  health_status: "OPTIMAL" | "MILD_DRIFT" | "REBALANCE_RECOMMENDED";
  rebalance_reasons: string[];
  holdings: HoldingMonitoringData[];
  sector_exposures: SectorExposureData[];
  concentration_audit: {
    single_stock_violations: any[];
    sector_violations: any[];
    is_compliant: boolean;
  };
}

export interface RebalanceTradeItem {
  security_id: string;
  symbol: string;
  company_name: string;
  sector: string;
  current_quantity: number;
  target_quantity: number;
  trade_quantity: number;
  quantity_change?: number;
  action: "BUY" | "SELL" | "HOLD";
  reference_price: number;
  latest_price?: number;
  trade_value: number;
  current_weight_pct: number;
  target_weight_pct: number;
  post_rebalance_weight_pct?: number;
  drift_pct?: number;
  rationale: string;
}

export interface PostRebalanceSectorItem {
  sector: string;
  post_rebalance_weight_pct: number;
  policy_cap_pct: number;
  within_limit: boolean;
}

export interface RebalanceTransactionCosts {
  total_estimated_costs?: number;
  brokerage?: number;
  stt?: number;
  stt_ctt?: number;
  exchange_charges?: number;
  exchange_turnover_charges?: number;
  gst?: number;
  stamp_duty?: number;
  sebi_charges?: number;
  sebi_turnover_fees?: number;
  net_cash_impact?: number;
  broker_name?: string;
  broker_profile?: string;
}

export interface RebalancePreviewResponse {
  portfolio_id: string;
  portfolio_name: string;
  trigger_status: "REBALANCE_TRIGGERED" | "NO_ACTION_REQUIRED";
  triggers_breached: string[];
  total_portfolio_value: number;
  current_cash?: number;
  post_rebalance_cash: number;
  total_post_rebalance_invested?: number;
  unallocated_cash_post_rebalance?: number;
  trades_count: number;
  trades_required_count?: number;
  turnover_amount: number;
  turnover_pct: number;
  trades: RebalanceTradeItem[];
  post_rebalance_sectors?: PostRebalanceSectorItem[];
  transaction_costs?: RebalanceTransactionCosts;
  non_custodial_disclosure?: string;
}

export async function fetchPortfolioMonitoring(portfolioId: string): Promise<PortfolioMonitoringResponse | null> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/monitoring`, {
    headers: getHeaders(),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function checkPortfolioDriftAndTrigger(portfolioId: string): Promise<RebalancePreviewResponse | null> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/check-drift-and-trigger`, {
    method: "POST",
    headers: getHeaders(),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function fetchRebalancePreview(portfolioId: string): Promise<RebalancePreviewResponse | null> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/rebalance-preview`, {
    headers: getHeaders(),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function applyPortfolioRebalance(
  portfolioId: string,
  stockDriftThreshold?: number,
  sectorDriftThreshold?: number
): Promise<PortfolioVersion> {
  const params = new URLSearchParams();
  if (stockDriftThreshold !== undefined) params.append("stock_drift_threshold", stockDriftThreshold.toString());
  if (sectorDriftThreshold !== undefined) params.append("sector_drift_threshold", sectorDriftThreshold.toString());
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/apply-rebalance${qs}`, {
    method: "POST",
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to apply rebalance to portfolio");
  }
  return res.json();
}





