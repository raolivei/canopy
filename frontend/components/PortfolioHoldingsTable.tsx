import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface Holding {
  asset_id: number;
  symbol: string;
  name: string;
  asset_type: string;
  total_shares: number;
  average_cost: number;
  current_price: number | null;
  cost_basis: number;
  market_value: number | null;
  unrealized_gain_loss: number | null;
  return_pct: number | null;
  allocation_pct: number | null;
}

interface HoldingsTableProps {
  holdings: Holding[];
  onSelect?: (holding: Holding) => void;
  currency?: string;
}

function formatCurrency(value: number | null, currency: string = "USD"): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number | null): string {
  if (value === null) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatShares(value: number): string {
  if (value >= 1) {
    return value.toLocaleString("en-US", { maximumFractionDigits: 4 });
  }
  return value.toFixed(8);
}

export default function PortfolioHoldingsTable({ holdings, onSelect, currency = "USD" }: HoldingsTableProps) {
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
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">Symbol</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">Shares</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">Avg Cost</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">Price</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">Market Value</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">Gain/Loss</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">Return</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500 dark:text-gray-400">Allocation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {holdings.map((holding) => {
              const isPositive = holding.unrealized_gain_loss !== null && holding.unrealized_gain_loss > 0;
              const isNegative = holding.unrealized_gain_loss !== null && holding.unrealized_gain_loss < 0;
              return (
                <tr key={holding.asset_id} onClick={() => onSelect?.(holding)} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors">
                  <td className="px-4 py-4">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{holding.symbol}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[200px]">{holding.name}</p>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right text-gray-900 dark:text-white">{formatShares(holding.total_shares)}</td>
                  <td className="px-4 py-4 text-right text-gray-900 dark:text-white">{formatCurrency(holding.average_cost, currency)}</td>
                  <td className="px-4 py-4 text-right text-gray-900 dark:text-white">{formatCurrency(holding.current_price, currency)}</td>
                  <td className="px-4 py-4 text-right font-medium text-gray-900 dark:text-white">{formatCurrency(holding.market_value, currency)}</td>
                  <td className="px-4 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {isPositive && <TrendingUp className="w-4 h-4 text-green-500" />}
                      {isNegative && <TrendingDown className="w-4 h-4 text-red-500" />}
                      {!isPositive && !isNegative && <Minus className="w-4 h-4 text-gray-400" />}
                      <span className={isPositive ? "text-green-600 dark:text-green-400" : isNegative ? "text-red-600 dark:text-red-400" : "text-gray-500"}>
                        {formatCurrency(holding.unrealized_gain_loss, currency)}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <span className={isPositive ? "text-green-600 dark:text-green-400" : isNegative ? "text-red-600 dark:text-red-400" : "text-gray-500"}>
                      {formatPercent(holding.return_pct)}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right text-gray-500 dark:text-gray-400">
                    {holding.allocation_pct !== null ? holding.allocation_pct.toFixed(1) + "%" : "—"}
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
