import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import BudgetsPage from "@/pages/budgets";
import type { Budget, BudgetStatus } from "@/types/budget";

const push = jest.fn();
jest.mock("next/router", () => ({ useRouter: () => ({ pathname: "/budgets", push, query: {} }) }));
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
jest.mock("@/components/charts/BudgetVsActualsChart", () => ({
  BudgetVsActualsChart: ({ data }: { data: unknown[] }) => <div data-testid="budget-chart" data-points={data.length} />,
}));
jest.mock("@/components/ChartTransition", () => ({
  ChartTransition: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
const addToast = jest.fn();
jest.mock("@/components/ui/Toast", () => ({ useToast: () => ({ addToast }) }));

const household: Budget = {
  id: 1,
  name: "Household",
  amount: 2000,
  currency: "CAD",
  period: "monthly",
  active: true,
  created_at: "",
  updated_at: "",
  categories: [{ id: 10, budget_id: 1, category_name: "Groceries", amount_limit: 600, created_at: "", updated_at: "" }],
};

const statusFor = (month: string): BudgetStatus => ({
  budget_id: 1,
  budget_name: "Household",
  period: "monthly",
  period_start: `${month}-01`,
  period_end: `${month}-28`,
  currency: "CAD",
  total_budget: 2000,
  total_spent: 1700,
  remaining: 300,
  percentage_used: 85,
  status: "warning",
  fx_complete: false,
  spent_by_currency: { CAD: { income: 0, expenses: 1700, net: -1700 }, USD: { income: 0, expenses: 40, net: -40 } },
  unconverted: { USD: { income: 0, expenses: 40, net: -40 } },
  fx: [],
  categories: [
    {
      category_id: 10,
      category_name: "Groceries",
      amount_limit: 600,
      actual_spent: 650,
      remaining: -50,
      percentage_used: 108.3,
      status: "over",
      by_currency: {},
      fx_complete: true,
      unconverted: {},
    },
  ],
});

function mockApi(initial: Budget[]) {
  let budgets = [...initial];
  const calls: { method: string; url: string; body?: unknown }[] = [];
  global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ method, url, body });
    const respond = (status: number, payload?: unknown) =>
      ({ ok: status < 400, status, json: async () => payload ?? {} }) as Response;

    if (method === "GET" && url.endsWith("/v1/budgets/")) return respond(200, budgets);
    if (method === "POST" && url.endsWith("/v1/budgets/")) {
      const created: Budget = {
        ...household,
        id: 99,
        name: body.name,
        amount: body.amount,
        period: body.period,
        categories: body.categories.map((c: { category_name: string; amount_limit: number }, i: number) => ({
          id: 100 + i,
          budget_id: 99,
          category_name: c.category_name,
          amount_limit: c.amount_limit,
          created_at: "",
          updated_at: "",
        })),
      };
      budgets = [...budgets, created];
      return respond(201, created);
    }
    if (method === "DELETE" && /\/v1\/budgets\/\d+$/.test(url)) {
      budgets = budgets.filter((b) => !url.endsWith(`/${b.id}`));
      return respond(204);
    }
    const status = /\/v1\/budgets\/(\d+)\/status\?month=(\d{4}-\d{2})/.exec(url);
    if (status) return respond(200, statusFor(status[2]));
    return respond(404, { detail: "not mocked" });
  }) as unknown as typeof fetch;
  return calls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <BudgetsPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  push.mockClear();
  addToast.mockClear();
});

describe("Budgets page", () => {
  it("shows an empty state, validates the form, and creates a budget", async () => {
    const calls = mockApi([]);
    renderPage();

    fireEvent.click(await screen.findByRole("button", { name: "Create your first budget" }));
    const dialog = await screen.findByRole("dialog");

    fireEvent.click(within(dialog).getByRole("button", { name: "Create budget" }));
    expect(within(dialog).getAllByText("Required").length).toBeGreaterThanOrEqual(2);
    expect(calls.some((c) => c.method === "POST")).toBe(false);

    fireEvent.change(within(dialog).getByLabelText("Name"), { target: { value: "Household" } });
    fireEvent.change(within(dialog).getByLabelText("Total amount (CAD)"), { target: { value: "2000" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Add category limit" }));
    fireEvent.change(within(dialog).getByLabelText("Category 1 name"), { target: { value: "Groceries" } });
    fireEvent.change(within(dialog).getByLabelText("Category 1 limit"), { target: { value: "600" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Create budget" }));

    await waitFor(() => expect(calls.find((c) => c.method === "POST")).toBeTruthy());
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({
      name: "Household",
      amount: 2000,
      period: "monthly",
      categories: [{ category_name: "Groceries", amount_limit: 600 }],
    });
    await waitFor(() => expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ title: "Budget created" })));
    expect(await screen.findByRole("tab", { name: /Household/ })).toBeInTheDocument();
  });

  it("shows status, FX notice, chart and category table with drill-down, and changes month", async () => {
    const calls = mockApi([household]);
    renderPage();

    const totals = await screen.findByLabelText("Budget totals");
    expect(within(totals).getByText("Budget").nextSibling).toHaveTextContent("2,000.00");
    expect(within(totals).getByText("Spent").nextSibling).toHaveTextContent("1,700.00");
    expect(within(totals).getByText("Close to limit")).toBeInTheDocument();
    expect(screen.getByText(/outside category limits/)).toHaveTextContent("1,050.00");

    expect(screen.getByRole("status")).toHaveTextContent("USD");
    expect(screen.getByRole("status")).toHaveTextContent("40.00");
    expect(screen.getByTestId("budget-chart")).toHaveAttribute("data-points", "1");

    const row = within(screen.getByRole("table")).getAllByRole("row")[1];
    expect(row).toHaveTextContent("Groceries");
    expect(row).toHaveTextContent("Over");
    fireEvent.click(row);
    expect(push).toHaveBeenCalledWith({ pathname: "/transactions", query: { category: "Groceries" } });

    fireEvent.click(screen.getByRole("button", { name: "Previous month" }));
    await waitFor(() => {
      const months = calls.filter((c) => c.url.includes("/status?month=")).map((c) => c.url.split("month=")[1]);
      expect(months.length).toBeGreaterThan(1);
      const [a, b] = months.slice(-2);
      expect(a > b).toBe(true);
    });
  });

  it("deletes after confirmation", async () => {
    const calls = mockApi([household]);
    renderPage();
    await screen.findByLabelText("Budget totals");

    fireEvent.click(screen.getByRole("button", { name: /Delete/ }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(calls.some((c) => c.method === "DELETE" && c.url.endsWith("/v1/budgets/1"))).toBe(true));
    expect(await screen.findByText("No budgets yet")).toBeInTheDocument();
  });
});
