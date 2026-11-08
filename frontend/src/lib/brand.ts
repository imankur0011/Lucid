/**
 * Centralized Brand Configuration for the Intelligent Portfolio Creation Application.
 * Modify brand parameters in this single file to ensure consistent typography,
 * meta tags, logos, taglines, and regulatory notices across the entire application.
 */

export const BRAND = {
  name: "Lucid",
  symbol: "L",
  legalName: "Lucid Wealth Technologies",
  tagline: "Disciplined stock portfolios, made simple and personal.",
  descriptor: "Intelligent Portfolio Creation & Rebalancing Engine",
  version: "Release Hardened v1.0",
  shortDescription:
    "A portfolio creation and rebalancing engine that calculates balanced, whole-share Indian stock portfolios with transparent explanations.",
  regulatoryNotice:
    "Non-Custodial Investment Planning & Portfolio Engine under SEBI (Investment Advisers) Regulations, 2013 standards",
  navItems: [
    { id: "results", label: "My Portfolio", shortLabel: "Portfolio" },
    { id: "why", label: "Why This Portfolio?", shortLabel: "Why This?" },
    { id: "scenarios", label: "Stress Tests & AI", shortLabel: "Stress & AI" },
    { id: "diagnosis", label: "Demat Diagnosis", shortLabel: "Diagnosis" },
  ],
  supportEmail: "support@lucid.invalid",
  currencySymbol: "₹",
  locale: "en-IN",
} as const;

export type NavigationTab =
  | "generator"
  | "results"
  | "why"
  | "diagnosis"
  | "scenarios"
  | "benchmarks"
  | "onboarding";

export const CURRENCY_FORMATTER = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export const PERCENT_FORMATTER = new Intl.NumberFormat("en-IN", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
});

export function formatINR(amount: number): string {
  return CURRENCY_FORMATTER.format(amount);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}
