import React from "react";
import { CurrencyBadge } from "@/components/ui/Badge";
import { cn } from "@/utils/cn";

interface Holding {
  asset_id: number;
  symbol: string;
  name: string;
  asset_type: string;
  currency: string;
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
  currency: string = "USD",
): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

export default function PortfolioHoldingsTable({
  holdings,
  onSelect,
  currency = "USD",
  convertToDisplay,
}: HoldingsTableProps) {
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

  if (holdings.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-500 dark:text-slate-400">
          No holdings yet. Add your first asset to get started.
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
              Symbol
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Currency
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Original Value
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Converted ({currency})
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {holdings.map((holding) => {
            const displayValue = getDisplayValue(
              holding.market_value,
              holding.currency,
            );
            return (
              <tr
                key={holding.asset_id}
                onClick={() => onSelect?.(holding)}
                className={cn(
                  "hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors",
                  onSelect && "cursor-pointer"
                )}
              >
                <td className="px-4 py-4">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {holding.symbol}
                    </p>
                    <p className="text-sm text-slate-500 dark:text-slate-400 truncate max-w-[200px]">
                      {holding.name}
                    </p>
                  </div>
                </td>
                <td className="px-4 py-4 text-center">
                  <CurrencyBadge currency={holding.currency} />
                </td>
                <td className="px-4 py-4 text-right text-slate-600 dark:text-slate-400">
                  {holding.currency === "BTC" || holding.currency === "ETH"
                    ? `${Number(holding.market_value).toFixed(4)} ${holding.currency}`
                    : formatCurrency(
                        Number(holding.market_value),
                        holding.currency,
                      )}
                </td>
                <td className="px-4 py-4 text-right font-medium text-slate-900 dark:text-white">
                  {formatCurrency(displayValue, currency)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
