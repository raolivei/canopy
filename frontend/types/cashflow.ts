/** Mirrors backend/models/cashflow.py. Money arrives as 2-decimal JSON numbers. */

export type ReportingCurrency = "CAD" | "USD";
export type FlowKind = "income" | "expense";
export type PeriodKind = "month" | "quarter" | "year";

export interface CurrencyFlow {
  income: number;
  expenses: number;
  net: number;
}

export interface FxProvenance {
  from_currency: string;
  to_currency: string;
  pair: string;
  rate: number;
  as_of: string;
  source: string | null;
}

export interface ReportingTotals {
  currency: string;
  income: number;
  expenses: number;
  net: number;
  savings_rate: number | null;
  by_currency: Record<string, CurrencyFlow>;
  fx_complete: boolean;
  unconverted: Record<string, CurrencyFlow>;
  fx: FxProvenance[];
}

export interface MonthlySummary extends ReportingTotals {
  month: string;
}

export interface MonthlySummaryResponse {
  data: MonthlySummary[];
  total_months: number;
  currency: string;
  fx_complete: boolean;
}

export interface CategoryBreakdownItem {
  category: string;
  amount: number;
  percentage: number;
  by_currency: Record<string, CurrencyFlow>;
  fx_complete: boolean;
  unconverted: Record<string, CurrencyFlow>;
}

export interface CategoryBreakdownResponse {
  month: string;
  kind: FlowKind;
  total: number;
  categories: CategoryBreakdownItem[];
  currency: string;
  fx_complete: boolean;
  unconverted: Record<string, CurrencyFlow>;
  fx: FxProvenance[];
}

export interface PeriodTotals extends ReportingTotals {
  start: string;
  end: string;
}

export interface ComparisonResponse {
  kind: PeriodKind;
  current: PeriodTotals;
  prior: PeriodTotals;
  delta: {
    income: number;
    expenses: number;
    net: number;
    savings_rate_points: number | null;
  };
  currency: string;
  fx_complete: boolean;
}
