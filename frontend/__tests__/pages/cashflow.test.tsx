import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import CashflowPage from "@/pages/cashflow";
import type { CategoryBreakdownResponse, ComparisonResponse, MonthlySummaryResponse } from "@/types/cashflow";

jest.mock("@/components/layout/PageLayout", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PageHeader: ({ title, actions }: { title: string; actions?: React.ReactNode }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
}));
jest.mock("@/components/charts/CashflowSummary", () => ({
  CashflowSummary: ({ data }: { data: unknown[] }) => <div data-testid="cashflow-chart" data-points={data.length} />,
}));
jest.mock("@/components/charts/CategoryBreakdown", () => ({
  CategoryBreakdown: ({ data }: { data: { category: string }[] }) => (
    <div data-testid="category-chart">{data.map((d) => d.category).join(",")}</div>
  ),
}));
jest.mock("@/components/ChartTransition", () => ({
  ChartTransition: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
jest.mock("framer-motion", () => ({
  motion: { div: ({ children, initial, animate, ...rest }: any) => <div {...rest}>{children}</div> },
}));

const flow = (income: number, expenses: number) => ({ income, expenses, net: income - expenses });

const summary: MonthlySummaryResponse = {
  currency: "CAD",
  total_months: 3,
  fx_complete: false,
  data: [
    { month: "2026-03", currency: "CAD", ...flow(5000, 2000), savings_rate: 0.6, by_currency: { CAD: flow(5000, 2000) }, fx_complete: true, unconverted: {}, fx: [] },
    { month: "2026-04", currency: "CAD", ...flow(5000, 2500), savings_rate: 0.5, by_currency: { CAD: flow(5000, 2500) }, fx_complete: true, unconverted: {}, fx: [] },
    {
      month: "2026-05",
      currency: "CAD",
      ...flow(5000, 3000),
      savings_rate: 0.4,
      by_currency: { CAD: flow(5000, 3000), USD: flow(0, 120) },
      fx_complete: false,
      unconverted: { USD: flow(0, 120) },
      fx: [],
    },
  ],
};

const categories = (kind: "income" | "expense", month: string): CategoryBreakdownResponse => ({
  month,
  kind,
  currency: "CAD",
  total: kind === "expense" ? 3000 : 5000,
  fx_complete: true,
  unconverted: {},
  fx: [],
  categories:
    kind === "expense"
      ? [
          { category: "Housing", amount: 1200, percentage: 40, by_currency: {}, fx_complete: true, unconverted: {} },
          { category: "Groceries", amount: 1800, percentage: 60, by_currency: {}, fx_complete: true, unconverted: {} },
        ]
      : [{ category: "Salary", amount: 5000, percentage: 100, by_currency: {}, fx_complete: true, unconverted: {} }],
});

const comparison: ComparisonResponse = {
  kind: "month",
  currency: "CAD",
  fx_complete: true,
  current: { start: "2026-05-01", end: "2026-05-31", currency: "CAD", ...flow(5000, 3000), savings_rate: 0.4, by_currency: {}, fx_complete: true, unconverted: {}, fx: [] },
  prior: { start: "2026-04-01", end: "2026-04-30", currency: "CAD", ...flow(5000, 2500), savings_rate: 0.5, by_currency: {}, fx_complete: true, unconverted: {}, fx: [] },
  delta: { income: 0, expenses: 500, net: -500, savings_rate_points: -10 },
};

function mockFetch() {
  const calls: string[] = [];
  global.fetch = jest.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    calls.push(url);
    const body = url.includes("/summary")
      ? summary
      : url.includes("/comparison")
        ? comparison
        : categories(url.includes("kind=income") ? "income" : "expense", new URL(url, "http://x").searchParams.get("month") ?? "");
    return { ok: true, status: 200, json: async () => body } as Response;
  }) as unknown as typeof fetch;
  return calls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <CashflowPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
});

describe("Cash Flow page", () => {
  it("shows period totals from the summary and flags unconverted amounts", async () => {
    mockFetch();
    renderPage();

    const totals = await screen.findByLabelText("Period totals");
    expect(within(totals).getByText("Income").nextSibling).toHaveTextContent("15,000.00");
    expect(within(totals).getByText("Expenses").nextSibling).toHaveTextContent("7,500.00");
    expect(within(totals).getByText("Net").nextSibling).toHaveTextContent("7,500.00");
    expect(within(totals).getByText("Savings rate").nextSibling).toHaveTextContent("50.0%");

    const notice = screen.getByRole("status");
    expect(notice).toHaveTextContent("USD");
    expect(notice).toHaveTextContent("120.00");
    expect(notice).toHaveTextContent("no exchange rate");
  });

  it("feeds the chart, breakdowns for the latest month, the comparison and the table", async () => {
    const calls = mockFetch();
    renderPage();

    expect(await screen.findByTestId("cashflow-chart")).toHaveAttribute("data-points", "3");
    await waitFor(() => expect(screen.getAllByTestId("category-chart")).toHaveLength(2));
    expect(screen.getAllByTestId("category-chart")[0]).toHaveTextContent("Housing,Groceries");
    expect(screen.getAllByTestId("category-chart")[1]).toHaveTextContent("Salary");
    expect(calls.some((u) => u.includes("/categories?month=2026-05&kind=expense"))).toBe(true);

    expect(await screen.findByText("Period comparison")).toBeInTheDocument();
    expect(screen.getAllByText(/was .*2,500\.00/).length).toBeGreaterThan(0);
    expect(screen.getByText("-10.0 pts")).toBeInTheDocument();

    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows).toHaveLength(3);
    expect(rows[0]).toHaveTextContent("May 2026");
    expect(rows[0]).toHaveTextContent("Partial");
    expect(rows[2]).toHaveTextContent("Complete");
  });

  it("requests a new range when the period changes", async () => {
    const calls = mockFetch();
    renderPage();
    await screen.findByLabelText("Period totals");

    fireEvent.click(screen.getByRole("button", { name: "3M" }));

    await waitFor(() => expect(calls.filter((u) => u.includes("/summary")).length).toBeGreaterThan(1));
    const last = calls.filter((u) => u.includes("/summary")).pop() ?? "";
    const start = new URL(last, "http://x").searchParams.get("start_date") ?? "";
    const expected = new Date();
    expected.setDate(1);
    expected.setMonth(expected.getMonth() - 2);
    expect(start).toBe(`${expected.getFullYear()}-${String(expected.getMonth() + 1).padStart(2, "0")}-01`);
    expect(last).toContain("reporting_currency=CAD");
  });

  it("shows an error state with retry", async () => {
    global.fetch = jest.fn(async () => ({ ok: false, status: 503, json: async () => ({}) }) as Response) as unknown as typeof fetch;
    renderPage();

    expect(await screen.findByText(/Could not load cash flow/)).toHaveTextContent("503");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
