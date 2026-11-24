/** Mirrors backend/models/exchange.py. Money arrives as 2-decimal JSON numbers; rates as full-precision numbers. */

export type ExchangeProvider = "wise" | "remitly" | "instarem" | "bank" | "other";

export interface ExchangeBenchmark {
  /** 1 from_currency in to_currency at the Bank of Canada reference rate. */
  rate: number;
  as_of: string;
  source: string | null;
  /** Positive when the effective rate was worse than the reference. */
  spread_pct: number;
}

export interface Exchange {
  id: number;
  date: string;
  provider: ExchangeProvider;
  from_currency: string;
  from_amount: number;
  to_currency: string;
  to_amount: number;
  fee_amount: number | null;
  fee_currency: string | null;
  quoted_rate: number | null;
  effective_rate: number;
  from_asset_id: number | null;
  to_asset_id: number | null;
  from_label: string | null;
  to_label: string | null;
  external_id: string | null;
  source: string;
  notes: string | null;
  benchmark: ExchangeBenchmark | null;
  created_at: string;
  updated_at: string;
}

export interface ExchangeInput {
  date: string;
  provider: ExchangeProvider;
  from_currency: string;
  from_amount: number;
  to_currency: string;
  to_amount: number;
  fee_amount: number | null;
  fee_currency: string | null;
  quoted_rate: number | null;
  from_asset_id: number | null;
  to_asset_id: number | null;
  from_label: string | null;
  to_label: string | null;
  notes: string | null;
}

export interface PairSummary {
  from_currency: string;
  to_currency: string;
  count: number;
  total_from: number;
  total_to: number;
  average_rate: number;
  fees: Record<string, number>;
  benchmark_coverage: number;
  spread_cost: number | null;
  spread_pct: number | null;
}

export interface ExchangeSummary {
  count: number;
  pairs: PairSummary[];
}
