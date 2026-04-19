import React, { useMemo } from "react";
import { CurrencyBadge } from "@/components/ui/Badge";
import { cn } from "@/utils/cn";

/** Mirrors ``BALANCE_BASED_ASSET_TYPES`` in ``portfolio_calculator.py``. */
const BALANCE_BASED_ASSET_TYPES = new Set([
  "bank_account",
  "bank_checking",
  "bank_savings",
  "retirement_rrsp",
  "retirement_tfsa",
  "retirement_fhsa",
  "retirement_dpsp",
  "crowdfunding",
  "cash",
]);

interface Holding {
  asset_id: number;
  symbol: string;
  name: string;
  asset_type: string;
  currency?: string;
  total_shares: number;
  average_cost: number;
  current_price: number | null;
  cost_basis: number;
  market_value: number | null;
  market_value_converted?: number;
  unrealized_gain_loss: number | null;
  return_pct: number | null;
  allocation_pct: number | null;
}

function isBalanceBasedAsset(assetType: string): boolean {
  return BALANCE_BASED_ASSET_TYPES.has(assetType);
}

function sortByAbsMarketValue(a: Holding, b: Holding): number {
  const av = Math.abs(Number(a.market_value ?? 0));
  const bv = Math.abs(Number(b.market_value ?? 0));
  return bv - av;
}

interface HoldingsTableProps {
  holdings: Holding[];
  onSelect?: (holding: Holding) => void;
  currency?: string;
  convertToDisplay?: (
    value: number | string | null,
    fromCurrency: string,
  ) => number;
}

function formatCurrency(
  value: number | null,
  currency: string = "CAD",
): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

function SectionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <tr className="bg-slate-100/90 dark:bg-slate-800/80">
      <td
        colSpan={4}
        className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300"
      >
        <span className="mr-2">{title}</span>
        <span className="font-normal normal-case text-slate-500 dark:text-slate-400">
          {subtitle}
        </span>
      </td>
    </tr>
  );
}

function HoldingRows({
  rows,
  currency,
  convertToDisplay,
  onSelect,
}: {
  rows: Holding[];
  currency: string;
  convertToDisplay?: HoldingsTableProps["convertToDisplay"];
  onSelect?: (holding: Holding) => void;
}) {
  const getDisplayValue = (
    value: number | string | null,
    holdingCurrency: string,
  ): number | null => {
    if (value === null) return null;
    if (convertToDisplay) {
      return convertToDisplay(value, holdingCurrency);
    }
    return Number(value);
  };

  return (
    <>
      {rows.map((holding) => {
        const holdingCurrency = (holding.currency || "CAD").trim() || "CAD";
        const displayValue = getDisplayValue(
          holding.market_value,
          holdingCurrency,
        );
        return (
          <tr
            key={holding.asset_id}
            onClick={() => onSelect?.(holding)}
            className={cn(
              "hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors",
              onSelect && "cursor-pointer",
            )}
          >
            <td className="px-4 py-4">
              <div>
                {isBalanceBasedAsset(holding.asset_type) ? (
                  <p className="font-medium text-slate-900 dark:text-white truncate max-w-[280px]">
                    {holding.name?.trim() || holding.symbol}
                  </p>
                ) : (
                  <>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {holding.symbol}
                    </p>
                    <p className="text-sm text-slate-500 dark:text-slate-400 truncate max-w-[240px]">
                      {holding.name}
                    </p>
                  </>
                )}
              </div>
            </td>
            <td className="px-4 py-4 text-center">
              <CurrencyBadge currency={holdingCurrency.toUpperCase()} />
            </td>
            <td className="px-4 py-4 text-right text-slate-600 dark:text-slate-400">
              {holdingCurrency === "BTC" || holdingCurrency === "ETH"
                ? `${Number(holding.market_value).toFixed(4)} ${holdingCurrency}`
                : formatCurrency(
                    Number(holding.market_value),
                    holdingCurrency,
                  )}
            </td>
            <td className="px-4 py-4 text-right font-medium text-slate-900 dark:text-white">
              {formatCurrency(displayValue, currency)}
            </td>
          </tr>
        );
      })}
    </>
  );
}

export default function PortfolioHoldingsTable({
  holdings,
  onSelect,
  currency = "CAD",
  convertToDisplay,
}: HoldingsTableProps) {
  const { securities, accounts } = useMemo(() => {
    const sec = holdings.filter((h) => !isBalanceBasedAsset(h.asset_type));
    const acc = holdings.filter((h) => isBalanceBasedAsset(h.asset_type));
    sec.sort(sortByAbsMarketValue);
    acc.sort(sortByAbsMarketValue);
    return { securities: sec, accounts: acc };
  }, [holdings]);

  if (holdings.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-500 dark:text-slate-400">
          No positions yet. Add your first asset or import balances to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-slate-50/80 dark:bg-slate-900/80">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Symbol / account
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Currency
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Original value
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Converted ({currency})
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          <SectionHeader
            title="Securities"
            subtitle="Stocks, ETFs, funds, crypto — priced from lots or quotes"
          />
          {securities.length === 0 ? (
            <tr>
              <td
                colSpan={4}
                className="px-4 py-3 text-sm text-slate-500 dark:text-slate-400"
              >
                No securities in this view (try Combined CAD/USD or add lots).
              </td>
            </tr>
          ) : (
            <HoldingRows
              rows={securities}
              currency={currency}
              convertToDisplay={convertToDisplay}
              onSelect={onSelect}
            />
          )}
          <SectionHeader
            title="Cash & accounts"
            subtitle="Bank and registered balances imported as positions"
          />
          {accounts.length === 0 ? (
            <tr>
              <td
                colSpan={4}
                className="px-4 py-3 text-sm text-slate-500 dark:text-slate-400"
              >
                No balance-based accounts in this view.
              </td>
            </tr>
          ) : (
            <HoldingRows
              rows={accounts}
              currency={currency}
              convertToDisplay={convertToDisplay}
              onSelect={onSelect}
            />
          )}
        </tbody>
      </table>
    </div>
  );
}
