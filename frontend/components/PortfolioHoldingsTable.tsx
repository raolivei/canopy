import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

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

function formatPercent(value: number | string | null): string {
  if (value === null) return "—";
  const num = Number(value);
  return `${num >= 0 ? "+" : ""}${num.toFixed(2)}%`;
}

function formatShares(value: number | string): string {
  const num = Number(value);
  if (num >= 1) {
    return num.toLocaleString("en-US", { maximumFractionDigits: 4 });
  }
  return num.toFixed(8);
}

export default function PortfolioHoldingsTable({
  holdings,
  onSelect,
  currency = "USD",
  convertToDisplay,
}: HoldingsTableProps) {
  // Helper to get display value
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
      <div className="card p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">
          No holdings yet. Add your first asset to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                Symbol
              </th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-500 dark:text-gray-400">
                Currency
              </th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">
                Original Value
              </th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">
                Converted ({currency})
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {holdings.map((holding) => {
              const displayValue = getDisplayValue(
                holding.market_value,
                holding.currency,
              );
              return (
                <tr
                  key={holding.asset_id}
                  onClick={() => onSelect?.(holding)}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-4">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {holding.symbol}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                        {holding.name}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-center">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        holding.currency === "CAD"
                          ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400"
                          : holding.currency === "USD"
                            ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                            : holding.currency === "BRL"
                              ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400"
                              : "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400"
                      }`}
                    >
                      {holding.currency}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right text-gray-600 dark:text-gray-400">
                    {holding.currency === "BTC" || holding.currency === "ETH"
                      ? `${Number(holding.market_value).toFixed(4)} ${holding.currency}`
                      : formatCurrency(
                          Number(holding.market_value),
                          holding.currency,
                        )}
                  </td>
                  <td className="px-4 py-4 text-right font-medium text-gray-900 dark:text-white">
                    {formatCurrency(displayValue, currency)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
