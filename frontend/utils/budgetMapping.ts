/**
 * Pure helpers for the Budgets page: month keys, form validation and the
 * mapping from a status payload to the chart contract. No React, no fetch.
 */

import type { BudgetVsActualsData } from "@/components/charts/BudgetVsActualsChart";
import type { Budget, BudgetHealth, BudgetInput, BudgetPeriod, CategoryStatus } from "@/types/budget";

export function currentMonthKey(today: Date = new Date()): string {
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
}

/** ``2026-01`` + (-1) → ``2025-12``. */
export function shiftMonthKey(key: string, delta: number): string {
  const [year, month] = key.split("-").map(Number);
  const date = new Date(year, month - 1 + delta, 1);
  return currentMonthKey(date);
}

export function isMonthKey(value: string): boolean {
  return /^\d{4}-(0[1-9]|1[0-2])$/.test(value);
}

export interface CategoryDraft {
  /** Stable key for React lists; ids exist only for persisted categories. */
  key: string;
  id?: number;
  category_name: string;
  amount_limit: string;
}

export interface BudgetDraft {
  name: string;
  amount: string;
  period: BudgetPeriod;
  categories: CategoryDraft[];
}

export interface DraftErrors {
  name?: string;
  amount?: string;
  categories: Record<string, { name?: string; limit?: string }>;
  form?: string;
}

let draftCounter = 0;
export function newCategoryDraft(): CategoryDraft {
  draftCounter += 1;
  return { key: `new-${draftCounter}`, category_name: "", amount_limit: "" };
}

export function emptyDraft(): BudgetDraft {
  return { name: "", amount: "", period: "monthly", categories: [] };
}

export function draftFromBudget(budget: Budget): BudgetDraft {
  return {
    name: budget.name,
    amount: budget.amount.toFixed(2),
    period: budget.period,
    categories: budget.categories.map((c) => ({
      key: `id-${c.id}`,
      id: c.id,
      category_name: c.category_name,
      amount_limit: c.amount_limit.toFixed(2),
    })),
  };
}

const MONEY = /^\d+(\.\d{1,2})?$/;

function moneyError(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return "Required";
  if (!MONEY.test(trimmed)) return "Enter an amount with up to two decimals";
  if (Number(trimmed) <= 0) return "Must be greater than zero";
  return undefined;
}

export function validateDraft(draft: BudgetDraft): DraftErrors {
  const errors: DraftErrors = { categories: {} };
  if (!draft.name.trim()) errors.name = "Required";
  else if (draft.name.trim().length > 200) errors.name = "Keep it under 200 characters";
  errors.amount = moneyError(draft.amount);

  const seen = new Map<string, string>();
  for (const category of draft.categories) {
    const entry: { name?: string; limit?: string } = {};
    const name = category.category_name.trim();
    if (!name) entry.name = "Required";
    else if (seen.has(name.toLowerCase())) entry.name = "Duplicate category";
    else seen.set(name.toLowerCase(), category.key);
    entry.limit = moneyError(category.amount_limit);
    if (entry.name || entry.limit) errors.categories[category.key] = entry;
  }
  return errors;
}

export function hasErrors(errors: DraftErrors): boolean {
  return Boolean(errors.name || errors.amount || errors.form) || Object.keys(errors.categories).length > 0;
}

export function draftToInput(draft: BudgetDraft): BudgetInput {
  return {
    name: draft.name.trim(),
    amount: Number(draft.amount),
    period: draft.period,
    categories: draft.categories.map((c) => ({ category_name: c.category_name.trim(), amount_limit: Number(c.amount_limit) })),
  };
}

export interface CategoryDiff {
  added: { category_name: string; amount_limit: number }[];
  changed: { id: number; category_name: string; amount_limit: number }[];
  removed: number[];
}

/** What to POST / PUT / DELETE so the server matches the edited draft. */
export function diffCategories(original: Budget, draft: BudgetDraft): CategoryDiff {
  const byId = new Map(original.categories.map((c) => [c.id, c]));
  const diff: CategoryDiff = { added: [], changed: [], removed: [] };
  const kept = new Set<number>();
  for (const c of draft.categories) {
    const name = c.category_name.trim();
    const limit = Number(c.amount_limit);
    if (c.id === undefined) {
      diff.added.push({ category_name: name, amount_limit: limit });
      continue;
    }
    kept.add(c.id);
    const before = byId.get(c.id);
    if (before && (before.category_name !== name || before.amount_limit !== limit)) {
      diff.changed.push({ id: c.id, category_name: name, amount_limit: limit });
    }
  }
  diff.removed = original.categories.filter((c) => !kept.has(c.id)).map((c) => c.id);
  return diff;
}

export function toBudgetVsActuals(categories: CategoryStatus[]): BudgetVsActualsData[] {
  return categories.map((c) => ({
    category: c.category_name,
    budget: c.amount_limit,
    actual: c.actual_spent,
    variance: Number((c.actual_spent - c.amount_limit).toFixed(2)),
    variancePct: Number((c.percentage_used - 100).toFixed(1)),
  }));
}

export const HEALTH_LABEL: Record<BudgetHealth, string> = { under: "On track", warning: "Close to limit", over: "Over" };
export const HEALTH_VARIANT: Record<BudgetHealth, "success" | "warning" | "danger"> = {
  under: "success",
  warning: "warning",
  over: "danger",
};
