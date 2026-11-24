import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import ExchangePage from "@/pages/exchange";
import type { Exchange, ExchangeSummary } from "@/types/exchange";

jest.mock("next/router", () => ({ useRouter: () => ({ pathname: "/exchange", push: jest.fn(), query: {} }) }));
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
const addToast = jest.fn();
jest.mock("@/components/ui/Toast", () => ({ useToast: () => ({ addToast }) }));

const brl: Exchange = {
  id: 1,
  date: "2026-10-01",
  provider: "remitly",
  from_currency: "CAD",
  from_amount: 1000,
  to_currency: "BRL",
  to_amount: 3900,
  fee_amount: 3.99,
  fee_currency: "CAD",
  quoted_rate: null,
  effective_rate: 3.9,
  from_asset_id: null,
  to_asset_id: null,
  from_label: "Bank CAD",
  to_label: "BRL account",
  external_id: null,
  source: "manual",
  notes: null,
  benchmark: null,
  created_at: "",
  updated_at: "",
};

function summaryOf(list: Exchange[]): ExchangeSummary {
  return {
    count: list.length,
    pairs: list.length
      ? [
          {
            from_currency: "CAD",
            to_currency: "BRL",
            count: list.length,
            total_from: 1000,
            total_to: 3900,
            average_rate: 3.9,
            fees: { CAD: 3.99 },
            benchmark_coverage: 0,
            spread_cost: null,
            spread_pct: null,
          },
        ]
      : [],
  };
}

function mockApi(initial: Exchange[]) {
  let exchanges = [...initial];
  const calls: { method: string; url: string; body?: Record<string, unknown> }[] = [];
  global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ method, url, body });
    const respond = (status: number, payload?: unknown) =>
      ({ ok: status < 400, status, json: async () => payload ?? {} }) as Response;

    if (method === "GET" && url.endsWith("/v1/exchange/")) return respond(200, exchanges);
    if (method === "GET" && url.endsWith("/v1/exchange/summary")) return respond(200, summaryOf(exchanges));
    if (method === "GET" && url.endsWith("/v1/accounts/"))
      return respond(200, { accounts: [{ id: "asset:5", name: "Wise CAD", currency: "CAD", institution: "Wise" }] });
    if (method === "POST" && url.endsWith("/v1/exchange/")) {
      const created = { ...brl, ...body, id: 2, effective_rate: body.to_amount / body.from_amount } as Exchange;
      exchanges = [created, ...exchanges];
      return respond(201, created);
    }
    const match = /\/v1\/exchange\/(\d+)$/.exec(url);
    if (match && method === "PUT") {
      exchanges = exchanges.map((e) => (e.id === Number(match[1]) ? ({ ...e, ...body } as Exchange) : e));
      return respond(200, exchanges.find((e) => e.id === Number(match[1])));
    }
    if (match && method === "DELETE") {
      exchanges = exchanges.filter((e) => e.id !== Number(match[1]));
      return respond(204);
    }
    return respond(404, { detail: "not mocked" });
  }) as unknown as typeof fetch;
  return calls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ExchangePage />
    </QueryClientProvider>,
  );
}

beforeEach(() => addToast.mockClear());

describe("Exchange page", () => {
  it("shows an empty state, validates the form and creates an exchange", async () => {
    const calls = mockApi([]);
    renderPage();

    fireEvent.click(await screen.findByRole("button", { name: "Add your first exchange" }));
    const dialog = await screen.findByRole("dialog");

    fireEvent.click(within(dialog).getByRole("button", { name: "Add exchange" }));
    expect(within(dialog).getAllByText("Required")).toHaveLength(2);
    expect(calls.some((c) => c.method === "POST")).toBe(false);

    fireEvent.change(within(dialog).getByLabelText("Amount sent"), { target: { value: "1350" } });
    fireEvent.change(within(dialog).getByLabelText("Amount received"), { target: { value: "990" } });
    fireEvent.change(within(dialog).getByLabelText("Fee"), { target: { value: "4.50" } });
    expect(within(dialog).getByText("1 CAD = 0.7333 USD")).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: "Add exchange" }));

    await waitFor(() => expect(calls.find((c) => c.method === "POST")).toBeTruthy());
    expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({
      provider: "wise",
      from_currency: "CAD",
      from_amount: 1350,
      to_currency: "USD",
      to_amount: 990,
      fee_amount: 4.5,
      fee_currency: "CAD",
    });
    await waitFor(() => expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ title: "Exchange added" })));
  });

  it("lists exchanges with summary, edits and deletes", async () => {
    const calls = mockApi([brl]);
    renderPage();

    const table = await screen.findByRole("table");
    const row = within(table).getAllByRole("row")[1];
    expect(row).toHaveTextContent("Remitly");
    expect(row).toHaveTextContent("1 CAD = 3.9000 BRL");
    expect(row).toHaveTextContent("BRL account");
    expect(await screen.findByText(/No reference rate for this pair/)).toBeInTheDocument();

    fireEvent.click(within(row).getByRole("button", { name: /Edit exchange/ }));
    let dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByLabelText("Amount received")).toHaveValue("3900.00");
    fireEvent.change(within(dialog).getByLabelText("Amount received"), { target: { value: "3950" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Save changes" }));
    await waitFor(() => expect(calls.find((c) => c.method === "PUT")?.body).toMatchObject({ to_amount: 3950 }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());

    fireEvent.click(within(screen.getByRole("table")).getByRole("button", { name: /Delete exchange/ }));
    dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));
    await waitFor(() => expect(calls.some((c) => c.method === "DELETE" && c.url.endsWith("/v1/exchange/1"))).toBe(true));
    expect(await screen.findByText("No exchanges yet")).toBeInTheDocument();
  });
});
