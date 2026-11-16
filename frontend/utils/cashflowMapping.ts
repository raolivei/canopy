/**
 * Pure helpers between the cash-flow API and the page/charts.
 * No fetching, no React; everything here is unit tested.
 */

import type { CashflowSummaryData } from "@/components/charts/CashflowSummary";
import type { CategoryBreakdownData } from "@/components/charts/CategoryBreakdown";
import type { PeriodConfig, TimePeriod } from "@/utils/dateFiltering";
import type { CategoryBreakdownItem, CurrencyFlow, MonthlySummary } from "@/types/cashflow";

/** Periods that make sense for monthly cash flow (no 5-day view, no open-ended "all"). */
export const CASHFLOW_PERIODS: PeriodConfig[] = [
  { value: "1m", label: "1M" },
  { value: "3m", label: "3M" },
  { value: "6m", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "ytd", label: "YTD" },
];

const MONTHS_FOR_PERIOD: Partial<Record<TimePeriod, number>> = { "1m": 1, "3m": 3, "6m": 6, "1y": 12 };

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** ``2026-03`` → ``Mar 2026``. Unknown input is returned unchanged. */
export function monthLabel(key: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(key);
  if (!match) return key;
  const month = Number(match[2]);
  if (month < 1 || month > 12) return key;
  return `${MONTH_NAMES[month - 1]} ${match[1]}`;
}

/** Local-date ISO string (``yyyy-mm-dd``) without timezone shifting. */
export function formatIsoDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/**
 * Calendar-month range for a period, ending today.
 * ``1m`` is the current month; ``3m`` the current and two previous months; ``ytd`` from Jan 1.
 */
export function periodToRange(period: TimePeriod, today: Date = new Date()): { start: string; end: string } {
  const end = formatIsoDate(today);
  if (period === "ytd") {
    return { start: formatIsoDate(new Date(today.getFullYear(), 0, 1)), end };
  }
  const months = MONTHS_FOR_PERIOD[period] ?? 12;
  const start = new Date(today.getFullYear(), today.getMonth() - (months - 1), 1);
  return { start: formatIsoDate(start), end };
}

/** Chart rows: month label plus a running cumulative net. */
export function toCashflowSummaryData(months: MonthlySummary[]): CashflowSummaryData[] {
  let cumulative = 0;
  return months.map((m) => {
    cumulative += m.net;
    return {
      date: monthLabel(m.month),
      income: m.income,
      expenses: m.expenses,
      net: m.net,
      cumulative: Number(cumulative.toFixed(2)),
    };
  });
}

export function toCategoryData(items: CategoryBreakdownItem[]): CategoryBreakdownData[] {
  return items.map((item) => ({ category: item.category, amount: item.amount, pct: item.percentage }));
}

export interface PeriodSummary {
  income: number;
  expenses: number;
  net: number;
  savings_rate: number | null;
  fx_complete: boolean;
  unconverted: Record<string, CurrencyFlow>;
}

/** Totals over several months, carrying unconverted amounts per currency so nothing disappears. */
export function sumMonths(months: MonthlySummary[]): PeriodSummary {
  const totals: PeriodSummary = { income: 0, expenses: 0, net: 0, savings_rate: null, fx_complete: true, unconverted: {} };
  for (const m of months) {
    totals.income += m.income;
    totals.expenses += m.expenses;
    totals.fx_complete = totals.fx_complete && m.fx_complete;
    for (const [currency, flow] of Object.entries(m.unconverted ?? {})) {
      const bucket = (totals.unconverted[currency] ??= { income: 0, expenses: 0, net: 0 });
      bucket.income += flow.income;
      bucket.expenses += flow.expenses;
      bucket.net += flow.net;
    }
  }
  totals.income = Number(totals.income.toFixed(2));
  totals.expenses = Number(totals.expenses.toFixed(2));
  totals.net = Number((totals.income - totals.expenses).toFixed(2));
  totals.savings_rate = totals.income > 0 ? totals.net / totals.income : null;
  return totals;
}
