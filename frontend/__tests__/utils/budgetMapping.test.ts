import type { Budget } from "@/types/budget";
import {
  currentMonthKey,
  diffCategories,
  draftFromBudget,
  draftToInput,
  hasErrors,
  isMonthKey,
  shiftMonthKey,
  statusPeriodLabel,
  toBudgetVsActuals,
  validateDraft,
} from "@/utils/budgetMapping";

const budget: Budget = {
  id: 7,
  name: "Household",
  amount: 2000,
  currency: "CAD",
  period: "monthly",
  active: true,
  created_at: "",
  updated_at: "",
  categories: [
    { id: 1, budget_id: 7, category_name: "Groceries", amount_limit: 600, created_at: "", updated_at: "" },
    { id: 2, budget_id: 7, category_name: "Dining", amount_limit: 200, created_at: "", updated_at: "" },
  ],
};

describe("month keys", () => {
  it("formats and shifts across year boundaries", () => {
    expect(currentMonthKey(new Date(2026, 0, 15))).toBe("2026-01");
    expect(shiftMonthKey("2026-01", -1)).toBe("2025-12");
    expect(shiftMonthKey("2026-12", 1)).toBe("2027-01");
    expect(isMonthKey("2026-02")).toBe(true);
    expect(isMonthKey("2026-13")).toBe(false);
  });
});

describe("validateDraft", () => {
  it("requires a name and a positive two-decimal amount", () => {
    const errors = validateDraft({ name: " ", amount: "12.345", period: "monthly", categories: [] });
    expect(errors.name).toBe("Required");
    expect(errors.amount).toMatch(/two decimals/);
    expect(hasErrors(errors)).toBe(true);

    expect(validateDraft({ name: "x", amount: "0", period: "monthly", categories: [] }).amount).toMatch(/greater than zero/);
    expect(hasErrors(validateDraft({ name: "x", amount: "10.50", period: "monthly", categories: [] }))).toBe(false);
  });

  it("flags empty, duplicate and invalid category rows by key", () => {
    const errors = validateDraft({
      name: "x",
      amount: "10",
      period: "monthly",
      categories: [
        { key: "a", category_name: "Food", amount_limit: "5" },
        { key: "b", category_name: "food", amount_limit: "" },
        { key: "c", category_name: "", amount_limit: "-1" },
      ],
    });
    expect(errors.categories.a).toBeUndefined();
    expect(errors.categories.b).toEqual({ name: "Duplicate category", limit: "Required" });
    expect(errors.categories.c.name).toBe("Required");
    expect(errors.categories.c.limit).toMatch(/two decimals/);
  });
});

describe("draft round trip and diff", () => {
  it("builds a draft from a budget and an API input from a draft", () => {
    const draft = draftFromBudget(budget);
    expect(draft.amount).toBe("2000.00");
    expect(draft.categories.map((c) => c.id)).toEqual([1, 2]);
    expect(draftToInput({ ...draft, name: "  Home " })).toEqual({
      name: "Home",
      amount: 2000,
      period: "monthly",
      categories: [
        { category_name: "Groceries", amount_limit: 600 },
        { category_name: "Dining", amount_limit: 200 },
      ],
    });
  });

  it("computes added, changed and removed categories", () => {
    const draft = draftFromBudget(budget);
    draft.categories = [
      { ...draft.categories[0], amount_limit: "650" },
      { key: "new-1", category_name: "Fuel", amount_limit: "100" },
    ];
    expect(diffCategories(budget, draft)).toEqual({
      added: [{ category_name: "Fuel", amount_limit: 100 }],
      changed: [{ id: 1, category_name: "Groceries", amount_limit: 650 }],
      removed: [2],
    });
  });
});

describe("toBudgetVsActuals", () => {
  it("maps status categories to the chart contract", () => {
    expect(
      toBudgetVsActuals([
        {
          category_id: 1,
          category_name: "Groceries",
          amount_limit: 600,
          actual_spent: 450,
          remaining: 150,
          percentage_used: 75,
          status: "under",
          by_currency: {},
          fx_complete: true,
          unconverted: {},
        },
      ]),
    ).toEqual([{ category: "Groceries", budget: 600, actual: 450, variance: -150, variancePct: -25 }]);
  });
});

describe("statusPeriodLabel", () => {
  it("names the year for a yearly budget and the month otherwise", () => {
    expect(statusPeriodLabel("yearly", "2026-01-01", "Nov 2026")).toBe("2026");
    expect(statusPeriodLabel("monthly", "2026-11-01", "Nov 2026")).toBe("Nov 2026");
  });
});
