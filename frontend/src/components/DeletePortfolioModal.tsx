"use client";

import React, { useState, useMemo } from "react";
import { PortfolioVersion, PortfolioSummary, deletePortfolio, deletePortfoliosBatch, deleteAllPortfolios } from "../lib/api";
import { IconTrash, IconX, IconAlertCircle } from "./icons";

export interface DeletePortfolioItem {
  portfolio_id: string;
  portfolio_name?: string;
  version_number?: number;
  investment_amount?: number;
  holdings_count?: number;
  risk_category?: string;
}

interface DeletePortfolioModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolio?: PortfolioVersion | PortfolioSummary | null;
  portfolios?: (PortfolioSummary | PortfolioVersion | DeletePortfolioItem)[];
  isDeleteAll?: boolean;
  onDeleted: () => void;
}

export function DeletePortfolioModal({
  isOpen,
  onClose,
  portfolio,
  portfolios,
  isDeleteAll = false,
  onDeleted,
}: DeletePortfolioModalProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Normalize targets into an array of items to delete
  const itemsToDelete: DeletePortfolioItem[] = useMemo(() => {
    if (portfolios && portfolios.length > 0) {
      return portfolios.map((p) => {
        const item = p as any;
        return {
          portfolio_id: item.portfolio_id,
          portfolio_name:
            item.portfolio_name ||
            item.latest_version?.portfolio_name ||
            `Portfolio v#${item.latest_version?.version_number || item.version_number || 1}`,
          version_number: item.version_number ?? item.latest_version?.version_number ?? 1,
          investment_amount:
            item.investment_amount !== undefined
              ? Number(item.investment_amount)
              : item.latest_version?.investment_amount !== undefined
              ? Number(item.latest_version.investment_amount)
              : 0,
          holdings_count:
            Array.isArray(item.holdings)
              ? item.holdings.length
              : Array.isArray(item.latest_version?.holdings)
              ? item.latest_version.holdings.length
              : item.holdings_count ?? 0,
          risk_category: item.risk_category || item.latest_version?.risk_category || "moderate",
        };
      });
    }

    if (portfolio) {
      const p = portfolio as any;
      return [
        {
          portfolio_id: p.portfolio_id,
          portfolio_name:
            p.portfolio_name ||
            p.latest_version?.portfolio_name ||
            `Portfolio v#${p.latest_version?.version_number || p.version_number || 1}`,
          version_number: p.version_number ?? p.latest_version?.version_number ?? 1,
          investment_amount:
            p.investment_amount !== undefined
              ? Number(p.investment_amount)
              : p.latest_version?.investment_amount !== undefined
              ? Number(p.latest_version.investment_amount)
              : 0,
          holdings_count:
            Array.isArray(p.holdings)
              ? p.holdings.length
              : Array.isArray(p.latest_version?.holdings)
              ? p.latest_version.holdings.length
              : p.holdings_count ?? 0,
          risk_category: p.risk_category || p.latest_version?.risk_category || "moderate",
        },
      ];
    }

    return [];
  }, [portfolio, portfolios]);

  if (!isOpen || itemsToDelete.length === 0) return null;

  const totalCapital = itemsToDelete.reduce((acc, curr) => acc + (curr.investment_amount || 0), 0);
  const totalHoldings = itemsToDelete.reduce((acc, curr) => acc + (curr.holdings_count || 0), 0);
  const count = itemsToDelete.length;

  const handleDelete = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      if (isDeleteAll) {
        await deleteAllPortfolios();
      } else if (itemsToDelete.length > 1) {
        await deletePortfoliosBatch(itemsToDelete.map((i) => i.portfolio_id));
      } else {
        await deletePortfolio(itemsToDelete[0].portfolio_id);
      }
      setIsDeleting(false);
      onDeleted();
      onClose();
    } catch (err: unknown) {
      setIsDeleting(false);
      const msg = err instanceof Error ? err.message : "Failed to delete portfolio(s)";
      setError(msg);
    }
  };

  const dialogTitle = isDeleteAll
    ? "Delete All Portfolios"
    : count > 1
    ? `Delete ${count} Selected Portfolios`
    : `Delete Portfolio`;

  const confirmButtonText = isDeleteAll
    ? "Delete All Portfolios"
    : count > 1
    ? `Delete ${count} Portfolios`
    : "Delete Portfolio";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn">
      <div
        className="w-full max-w-lg rounded-2xl bg-white border border-[#E5E3DA] shadow-xl overflow-hidden animate-scaleUp"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-portfolio-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#E5E3DA] bg-[#FDFBF7]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-red-50 border border-red-200 text-red-600 flex items-center justify-center shrink-0">
              <IconTrash className="w-5 h-5" />
            </div>
            <div>
              <h3 id="delete-portfolio-title" className="text-base font-bold text-[#142A3B]">
                {dialogTitle}
              </h3>
              <p className="text-xs text-[#66758A]">
                {isDeleteAll
                  ? "Wiping all saved portfolios from account"
                  : count > 1
                  ? `Batch deletion of ${count} investor portfolios`
                  : "Irreversible portfolio removal"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isDeleting}
            type="button"
            className="p-1.5 text-[#66758A] hover:text-[#142A3B] hover:bg-[#E5E3DA]/50 rounded-lg transition-colors cursor-pointer"
            aria-label="Close dialog"
          >
            <IconX className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-left">
          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
              <IconAlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* List of portfolios to be deleted */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-[#4A5568]">
              <span>Portfolios targeted for deletion ({count}):</span>
              {totalCapital > 0 && (
                <span className="text-[#142A3B] font-bold">
                  Total: ₹{totalCapital.toLocaleString("en-IN")}
                </span>
              )}
            </div>

            <div className="max-h-48 overflow-y-auto space-y-2 border border-[#E5E3DA] rounded-xl p-2.5 bg-[#FDFBF7]">
              {itemsToDelete.map((item) => (
                <div
                  key={item.portfolio_id}
                  className="p-2.5 rounded-lg bg-white border border-[#E5E3DA] flex items-center justify-between gap-3 text-xs"
                >
                  <div className="min-w-0">
                    <div className="font-bold text-[#142A3B] truncate">{item.portfolio_name}</div>
                    <div className="text-[11px] text-[#66758A] flex items-center gap-2 mt-0.5">
                      <span>v#{item.version_number}</span>
                      <span>•</span>
                      <span className="uppercase text-[#285C4D] font-medium">
                        {item.risk_category?.replace("_", " ")}
                      </span>
                      <span>•</span>
                      <span>{item.holdings_count} stocks</span>
                    </div>
                  </div>
                  {item.investment_amount ? (
                    <div className="text-right shrink-0 font-bold text-[#142A3B]">
                      ₹{item.investment_amount.toLocaleString("en-IN")}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          <div className="text-xs text-[#4A5568] leading-relaxed space-y-2">
            <p>
              Are you sure you want to permanently delete{" "}
              {isDeleteAll
                ? "all saved portfolios"
                : count > 1
                ? `these ${count} portfolios`
                : "this portfolio"}
              ? This action will immediately remove:
            </p>
            <ul className="list-disc list-inside space-y-1 text-[#66758A] pl-1">
              <li>Stock allocations, integer whole-share decisions, and execution order slips</li>
              <li>Agent deliberation audit logs, reasoning evidence, and SEC/BSE filings links</li>
              <li>Scenario stress simulations and historical version snapshots</li>
            </ul>
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs">
              <strong>Account Safety:</strong> Your Lucid investor account and other portfolios will remain untouched. Registered credentials, financial goals, and SEBI suitability assessment answers are safely preserved.
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-[#E5E3DA] bg-[#FDFBF7]">
          <button
            onClick={onClose}
            disabled={isDeleting}
            type="button"
            className="px-4 py-2 rounded-xl border border-[#E5E3DA] bg-white text-xs font-bold text-[#142A3B] hover:bg-[#F7F6F1] transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            type="button"
            className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-2 transition-colors cursor-pointer shadow-xs"
          >
            {isDeleting ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                <span>Deleting...</span>
              </>
            ) : (
              <>
                <IconTrash className="w-3.5 h-3.5" />
                <span>{confirmButtonText}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DeletePortfolioModal;
