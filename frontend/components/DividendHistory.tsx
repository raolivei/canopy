import React from "react";
import { DollarSign, Calendar } from "lucide-react";

interface Dividend {
  id: number;
  asset_id: number;
  asset_symbol: string;
  amount: number;
  payment_date: string;
  dividend_type: string;
  notes?: string;
}

interface DividendHistoryProps {
  dividends: Dividend[];
  currency?: string;
  onDelete?: (id: number) => void;
}

function formatCurrency(value: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

const TYPE_COLORS: Record<string, string> = {
  cash: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  stock: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  reinvested: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
};

export default function DividendHistory({ dividends, currency = "USD", onDelete }: DividendHistoryProps) {
  const totalDividends = dividends.reduce((sum, d) => sum + Number(d.amount), 0);

  if (dividends.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Dividend History
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          No dividends recorded yet
        </p>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Dividend History
        </h3>
        <div className="text-right">
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Received</p>
          <p className="text-xl font-bold text-green-600 dark:text-green-400">
            {formatCurrency(totalDividends, currency)}
          </p>
        </div>
      </div>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {dividends.map((dividend) => (
          <div
            key={dividend.id}
            className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <DollarSign className="w-4 h-4 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  {dividend.asset_symbol}
                </p>
                <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <Calendar className="w-3 h-3" />
                  {formatDate(dividend.payment_date)}
                </div>
              </div>
            </div>
            <div className="text-right">
              <p className="font-medium text-green-600 dark:text-green-400">
                +{formatCurrency(Number(dividend.amount), currency)}
              </p>
              <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLORS[dividend.dividend_type] || TYPE_COLORS.cash}`}>
                {dividend.dividend_type}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
