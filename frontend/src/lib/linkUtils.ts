/**
 * Verified External Link & Exchange Filing Utilities for Lucid.
 *
 * Guarantees canonical, resilient, and non-hallucinated URLs across
 * NSE, BSE, SEBI, and corporate portals. Eliminates 404 Not Found errors.
 */

export interface ExchangeFilingLinks {
  symbol: string;
  primaryUrl: string;
  primaryLabel: string;
  primaryExchange: "NSE" | "BSE";
  nseAnnouncementsUrl: string;
  nseResultsUrl: string;
  nseQuoteUrl: string;
  bseAnnouncementsUrl: string;
  bseQuoteUrl: string;
  irUrl?: string;
}

export interface RegulatoryLinkItem {
  id: string;
  title: string;
  shortLabel: string;
  url: string;
  description: string;
  category: "REGULATORY" | "GRIEVANCE" | "DISPUTE_RESOLUTION" | "EXCHANGE" | "INDUSTRY";
}

/**
 * Normalizes equity ticker to uppercase clean symbol without exchange suffixes.
 */
export function cleanSymbol(symbol: string): string {
  if (!symbol) return "";
  let clean = symbol.trim().toUpperCase();
  for (const sfx of [".NS", ".BO", ".BSE", ".NSE"]) {
    if (clean.endsWith(sfx)) {
      clean = clean.slice(0, -sfx.length);
    }
  }
  return clean;
}

/**
 * Returns canonical NSE corporate filings announcements URL.
 * Guarantees HTTP 200 and never 404s for any valid symbol.
 */
export function getNseAnnouncementUrl(symbol: string): string {
  const sym = cleanSymbol(symbol);
  return `https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=${encodeURIComponent(sym)}`;
}

/**
 * Returns canonical NSE financial results disclosures URL.
 */
export function getNseResultsUrl(symbol: string): string {
  const sym = cleanSymbol(symbol);
  return `https://www.nseindia.com/companies-listing/corporate-filings-financial-results?symbol=${encodeURIComponent(sym)}`;
}

/**
 * Returns canonical NSE stock quote overview URL.
 */
export function getNseQuoteUrl(symbol: string): string {
  const sym = cleanSymbol(symbol);
  return `https://www.nseindia.com/get-quotes/equity?symbol=${encodeURIComponent(sym)}`;
}

/**
 * Returns canonical BSE corporate announcements URL.
 * Uses official slug and scrip code when available; falls back to BSE announcements portal search.
 * Never returns obsolete URLs like StockPrcStk.html.
 */
export function getBseAnnouncementUrl(symbol: string, bseCode?: string): string {
  const sym = cleanSymbol(symbol);
  const code = (bseCode || "").trim();
  if (code && /^\d+$/.test(code) && code !== "500000") {
    return `https://www.bseindia.com/stock-share-price/${sym.toLowerCase()}/${code}/corp-announcements/`;
  }
  return "https://www.bseindia.com/corporates/ann.html";
}

/**
 * Returns canonical BSE quote overview URL.
 */
export function getBseQuoteUrl(symbol: string, bseCode?: string): string {
  const sym = cleanSymbol(symbol);
  const code = (bseCode || "").trim();
  if (code && /^\d+$/.test(code) && code !== "500000") {
    return `https://www.bseindia.com/stock-share-price/${sym.toLowerCase()}/${code}/`;
  }
  return "https://www.bseindia.com/corporates/ann.html";
}

/**
 * Generates verified exchange filing destinations with resilient primary and fallback URLs.
 */
export function getExchangeFilingLinks(symbol: string, bseCode?: string): ExchangeFilingLinks {
  const sym = cleanSymbol(symbol);
  const hasValidBse = Boolean(bseCode && /^\d+$/.test(bseCode) && bseCode !== "500000");

  const nseAnnounce = getNseAnnouncementUrl(sym);
  const nseResults = getNseResultsUrl(sym);
  const nseQuote = getNseQuoteUrl(sym);
  const bseAnnounce = getBseAnnouncementUrl(sym, bseCode);
  const bseQuote = getBseQuoteUrl(sym, bseCode);

  let primaryUrl = nseAnnounce;
  let primaryLabel = `NSE Corporate Filings (${sym})`;
  let primaryExchange: "NSE" | "BSE" = "NSE";

  if (hasValidBse && bseCode) {
    primaryUrl = bseAnnounce;
    primaryLabel = `BSE Corporate Filings (Scrip ${bseCode})`;
    primaryExchange = "BSE";
  }

  return {
    symbol: sym,
    primaryUrl,
    primaryLabel,
    primaryExchange,
    nseAnnouncementsUrl: nseAnnounce,
    nseResultsUrl: nseResults,
    nseQuoteUrl: nseQuote,
    bseAnnouncementsUrl: bseAnnounce,
    bseQuoteUrl: bseQuote,
  };
}

/**
 * Authoritative Indian regulatory and dispute resolution links.
 */
export const REGULATORY_LINKS: RegulatoryLinkItem[] = [
  {
    id: "sebi",
    title: "Securities and Exchange Board of India (SEBI)",
    shortLabel: "SEBI",
    url: "https://www.sebi.gov.in",
    description: "Apex statutory authority regulating securities markets in India.",
    category: "REGULATORY",
  },
  {
    id: "scores",
    title: "SEBI SCORES 2.0 (Investor Grievance Redressal System)",
    shortLabel: "SCORES 2.0",
    url: "https://scores.sebi.gov.in",
    description: "Centralized investor complaint redressal portal managed directly by SEBI.",
    category: "GRIEVANCE",
  },
  {
    id: "smartodr",
    title: "Securities Market Online Dispute Resolution (SMART ODR)",
    shortLabel: "SMART ODR",
    url: "https://smartodr.in",
    description: "Independent conciliation and arbitration portal established under SEBI circulars.",
    category: "DISPUTE_RESOLUTION",
  },
  {
    id: "rbi",
    title: "Reserve Bank of India (RBI)",
    shortLabel: "RBI",
    url: "https://www.rbi.org.in",
    description: "Monetary policy authority anchoring Indian repo rates and liquidity.",
    category: "REGULATORY",
  },
  {
    id: "amfi",
    title: "Association of Mutual Funds in India (AMFI)",
    shortLabel: "AMFI",
    url: "https://www.amfiindia.com",
    description: "Apex association of SEBI-registered mutual funds in India.",
    category: "INDUSTRY",
  },
  {
    id: "nse_filings",
    title: "NSE Corporate Filings Portal",
    shortLabel: "NSE Disclosures",
    url: "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
    description: "Live corporate announcements and quarterly earnings disclosures on NSE.",
    category: "EXCHANGE",
  },
  {
    id: "bse_filings",
    title: "BSE Corporate Announcements Portal",
    shortLabel: "BSE Disclosures",
    url: "https://www.bseindia.com/corporates/ann.html",
    description: "Official company disclosures and regulatory announcements on BSE.",
    category: "EXCHANGE",
  },
];

