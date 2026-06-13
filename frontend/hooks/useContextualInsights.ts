import { useQuery } from "@tanstack/react-query";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export interface BudgetWarning {
  category_name: string;
  type: "on_track" | "warning" | "critical";
  actual_spent: number;
  budget_limit: number;
  percent_used: number;
  message: string;
}

export interface MoMComparison {
  category_name: string;
  current_month_amount: number;
  previous_month_amount: number;
  change_percent: number;
  type: "increase" | "decrease" | "stable";
  message: string;
}

export interface TransactionAnomaly {
  transaction_id: string;
  merchant: string;
  amount: number;
  category: string;
  deviation_percent: number;
  type: "outlier" | "unusual_time" | "duplicate_pattern";
  message: string;
}

export interface RecurringPrediction {
  merchant: string;
  category: string;
  expected_amount: number;
  expected_date: string;
  confidence: number;
  message: string;
}

export interface ContextualInsightsSummary {
  budget_warnings: BudgetWarning[];
  mom_comparisons: MoMComparison[];
  anomalies: TransactionAnomaly[];
  recurring_predictions: RecurringPrediction[];
}

export function useContextualInsights() {
  return useQuery<ContextualInsightsSummary>({
    queryKey: ["contextual-insights"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/contextual-insights/summary`);
      if (!res.ok) {
        throw new Error(`Failed to fetch contextual insights: ${res.status}`);
      }
      return res.json();
    },
    retry: 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useBudgetWarnings() {
  return useQuery<BudgetWarning[]>({
    queryKey: ["budget-warnings"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/contextual-insights/budget-warnings`);
      if (!res.ok) throw new Error("Failed to fetch budget warnings");
      return res.json();
    },
    retry: 1,
  });
}

export function useMoMComparisons() {
  return useQuery<MoMComparison[]>({
    queryKey: ["mom-comparisons"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/contextual-insights/mom-comparisons`);
      if (!res.ok) throw new Error("Failed to fetch MoM comparisons");
      return res.json();
    },
    retry: 1,
  });
}

export function useTransactionAnomalies() {
  return useQuery<TransactionAnomaly[]>({
    queryKey: ["transaction-anomalies"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/contextual-insights/anomalies`);
      if (!res.ok) throw new Error("Failed to fetch anomalies");
      return res.json();
    },
    retry: 1,
  });
}

export function useRecurringPredictions() {
  return useQuery<RecurringPrediction[]>({
    queryKey: ["recurring-predictions"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/contextual-insights/recurring-predictions`);
      if (!res.ok) throw new Error("Failed to fetch predictions");
      return res.json();
    },
    retry: 1,
  });
}
