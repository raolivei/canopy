import React, { useMemo, useState } from "react";
import { DollarSign, Calendar } from "lucide-react";
import { parseISO, startOfYear, subMonths, subYears } from "date-fns";
import { cn } from "@/utils/cn";
import { Button } from "@/components/ui/Button";

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

type DividendPeriod = "all" | "1m" | "3m" | "ytd" | "1y";

const PERIOD_OPTIONS: { id: DividendPeriod; label: string }[] = [
  { id: "all", label: "All" },
  { id: "1m", label: "1M" },
  { id: "3m", label: "3M" },
  { id: "ytd", label: "YTD" },
  { id: "1y", label: "1Y" },
];

function formatCurrency(value: number, currency: string = "CAD"): string {
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
  cash: "bg-success-100 text-success-800 dark:bg-success-900/30 dark:text-success-400",
  stock: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  reinvested: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
};

function filterDividendsByPeriod(
  dividends: Dividend[],
  period: DividendPeriod,
): Dividend[] {
  if (period === "all") return dividends;
  const now = new Date();
  let start: Date;
  switch (period) {
    case "1m":
      start = subMonths(now, 1);
      break;
    case "3m":
      start = subMonths(now, 3);
      break;
    case "ytd":
      start = startOfYear(now);
      break;
    case "1y":
      start = subYears(now, 1);
      break;
    default:
      return dividends;
  }
  return dividends.filter((d) => {
    const date = parseISO(d.payment_date);
    if (Number.isNaN(date.getTime())) return false;
    return date >= start && date <= now;
  });
}

function totalReceivedLabel(period: DividendPeriod): string {
  switch (period) {
    case "all":
      return "Total received";
    case "1m":
      return "Total received (1M)";
    case "3m":
      return "Total received (3M)";
    case "ytd":
      return "Total received (YTD)";
    case "1y":
      return "Total received (1Y)";
    default:
      return "Total received";
  }
}

export default function DividendHistory({
  dividends,
  currency = "CAD",
}: DividendHistoryProps) {
  const [period, setPeriod] = useState<DividendPeriod>("all");

  const filtered = useMemo(
    () => filterDividendsByPeriod(dividends, period),
    [dividends, period],
  );

  const totalForPeriod = useMemo(
    () => filtered.reduce((sum, d) => sum + Number(d.amount), 0),
    [filtered],
  );

  if (dividends.length === 0) {
    return (
      <div className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Dividend history
        </h3>
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">
          No dividends recorded yet
        </p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            Dividend history
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Filter by payment date; total matches the list below.
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {totalReceivedLabel(period)}
          </p>
          <p className="text-xl font-bold text-success-600 dark:text-success-400">
            {formatCurrency(totalForPeriod, currency)}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {PERIOD_OPTIONS.map((opt) => (
          <Button
            key={opt.id}
            type="button"
            size="sm"
            variant={period === opt.id ? "primary" : "secondary"}
            className="min-w-[3rem]"
            aria-pressed={period === opt.id}
            onClick={() => setPeriod(opt.id)}
          >
            {opt.label}
          </Button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-center py-8 text-slate-500 dark:text-slate-400 text-sm">
          No dividend payments in this range.
        </p>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filtered.map((dividend) => (
            <div
              key={dividend.id}
              className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-success-100 dark:bg-success-900/30 rounded-lg">
                  <DollarSign className="w-4 h-4 text-success-600 dark:text-success-400" />
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {dividend.asset_symbol}
                  </p>
                  <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                    <Calendar className="w-3 h-3" />
                    {formatDate(dividend.payment_date)}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium text-success-600 dark:text-success-400">
                  +{formatCurrency(Number(dividend.amount), currency)}
                </p>
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full",
                    TYPE_COLORS[dividend.dividend_type] || TYPE_COLORS.cash,
                  )}
                >
                  {dividend.dividend_type}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
