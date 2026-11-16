import type { MonthlySummary } from "@/types/cashflow";
import { formatIsoDate, monthLabel, periodToRange, sumMonths, toCashflowSummaryData, toCategoryData } from "@/utils/cashflowMapping";

const month = (key: string, income: number, expenses: number, extra: Partial<MonthlySummary> = {}): MonthlySummary => ({
  month: key,
  currency: "CAD",
  income,
  expenses,
  net: income - expenses,
  savings_rate: income > 0 ? (income - expenses) / income : null,
  by_currency: {},
  fx_complete: true,
  unconverted: {},
  fx: [],
  ...extra,
});

describe("periodToRange", () => {
  const today = new Date(2026, 4, 15); // 15 May 2026, local

  it.each([
    ["1m", "2026-05-01"],
    ["3m", "2026-03-01"],
    ["6m", "2025-12-01"],
    ["1y", "2025-06-01"],
    ["ytd", "2026-01-01"],
  ] as const)("%s starts on %s and ends today", (period, start) => {
    expect(periodToRange(period, today)).toEqual({ start, end: "2026-05-15" });
  });

  it("falls back to twelve months for periods that do not apply", () => {
    expect(periodToRange("all", today).start).toBe("2025-06-01");
  });
});

describe("labels and dates", () => {
  it("formats month keys and leaves junk alone", () => {
    expect(monthLabel("2026-03")).toBe("Mar 2026");
    expect(monthLabel("2026-13")).toBe("2026-13");
    expect(monthLabel("hello")).toBe("hello");
  });

  it("formats local ISO dates without timezone drift", () => {
    expect(formatIsoDate(new Date(2026, 0, 1, 0, 30))).toBe("2026-01-01");
  });
});

describe("chart mapping", () => {
  it("adds a running cumulative net", () => {
    const rows = toCashflowSummaryData([month("2026-01", 100, 40), month("2026-02", 50, 80), month("2026-03", 0, 0)]);
    expect(rows.map((r) => [r.date, r.cumulative])).toEqual([
      ["Jan 2026", 60],
      ["Feb 2026", 30],
      ["Mar 2026", 30],
    ]);
  });

  it("maps category items to the pie contract", () => {
    expect(
      toCategoryData([{ category: "Food", amount: 12.5, percentage: 25, by_currency: {}, fx_complete: true, unconverted: {} }]),
    ).toEqual([{ category: "Food", amount: 12.5, pct: 25 }]);
  });
});

describe("sumMonths", () => {
  it("totals income and expenses with a savings rate", () => {
    const totals = sumMonths([month("2026-01", 1000, 250.5), month("2026-02", 1000, 249.5)]);
    expect(totals).toMatchObject({ income: 2000, expenses: 500, net: 1500, fx_complete: true, unconverted: {} });
    expect(totals.savings_rate).toBeCloseTo(0.75);
  });

  it("keeps unconverted amounts per currency and flags incompleteness", () => {
    const totals = sumMonths([
      month("2026-01", 100, 10, { fx_complete: false, unconverted: { USD: { income: 0, expenses: 20, net: -20 } } }),
      month("2026-02", 100, 10, { fx_complete: false, unconverted: { USD: { income: 5, expenses: 30, net: -25 } } }),
      month("2026-03", 0, 0),
    ]);
    expect(totals.fx_complete).toBe(false);
    expect(totals.unconverted).toEqual({ USD: { income: 5, expenses: 50, net: -45 } });
  });

  it("has no savings rate without income", () => {
    expect(sumMonths([month("2026-01", 0, 10)]).savings_rate).toBeNull();
    expect(sumMonths([]).savings_rate).toBeNull();
  });
});
