/** Mirrors backend/models/budget.py. Money arrives as 2-decimal JSON numbers. */

import type { CurrencyFlow, FxProvenance } from "@/types/cashflow";

export type BudgetPeriod = "monthly" | "yearly";
export type BudgetHealth = "under" | "warning" | "over";

export interface BudgetCategory {
  id: number;
  budget_id: number;
  category_name: string;
  amount_limit: number;
  created_at: string;
  updated_at: string;
}

export interface Budget {
  id: number;
  name: string;
  amount: number;
  currency: string;
  period: BudgetPeriod;
  active: boolean;
  created_at: string;
  updated_at: string;
  categories: BudgetCategory[];
}

export interface CategoryStatus {
  category_id: number;
  category_name: string;
  amount_limit: number;
  actual_spent: number;
  remaining: number;
  percentage_used: number;
  status: BudgetHealth;
  by_currency: Record<string, CurrencyFlow>;
  fx_complete: boolean;
  unconverted: Record<string, CurrencyFlow>;
}

export interface BudgetStatus {
  budget_id: number;
  budget_name: string;
  period: BudgetPeriod;
  period_start: string;
  period_end: string;
  currency: string;
  total_budget: number;
  total_spent: number;
  remaining: number;
  percentage_used: number;
  status: BudgetHealth;
  fx_complete: boolean;
  spent_by_currency: Record<string, CurrencyFlow>;
  unconverted: Record<string, CurrencyFlow>;
  fx: FxProvenance[];
  categories: CategoryStatus[];
}

export interface BudgetCategoryInput {
  category_name: string;
  amount_limit: number;
}

export interface BudgetInput {
  name: string;
  amount: number;
  period: BudgetPeriod;
  categories: BudgetCategoryInput[];
}
