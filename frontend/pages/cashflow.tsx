import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowDownRight, ArrowUpRight, PiggyBank, TrendingDown, TrendingUp } from "lucide-react";

import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { PeriodSelector } from "@/components/ui/PeriodSelector";
import { Select } from "@/components/ui/Select";
import { SkeletonChart, SkeletonMetricCard } from "@/components/ui/Skeleton";
import { ColumnDef, Table } from "@/components/ui/Table";
import { ChartTransition } from "@/components/ChartTransition";
import { CashflowSummary } from "@/components/charts/CashflowSummary";
import { CategoryBreakdown } from "@/components/charts/CategoryBreakdown";
import { useCurrencyView, viewCurrency } from "@/hooks/useCurrencyView";
import { useMoney } from "@/hooks/useMoney";
import type {
  CategoryBreakdownResponse,
  ComparisonResponse,
  CurrencyFlow,
  MonthlySummary,
  MonthlySummaryResponse,
  PeriodKind,
} from "@/types/cashflow";
import {
  CASHFLOW_PERIODS,
  monthLabel,
  periodToRange,
  sumMonths,
  toCashflowSummaryData,
  toCategoryData,
} from "@/utils/cashflowMapping";
import { cn } from "@/utils/cn";
import type { TimePeriod } from "@/utils/dateFiltering";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

const COMPARISON_OPTIONS = [
  { value: "month", label: "Month vs previous month" },
  { value: "quarter", label: "Quarter vs previous quarter" },
  { value: "year", label: "Year vs previous year" },
];

function MetricCard({
  title,
  value,
  subtitle,
  icon,
  tone = "neutral",
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  tone?: "neutral" | "good" | "bad";
}) {
  const iconBg = {
    neutral: "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300",
    good: "bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400",
    bad: "bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400",
  }[tone];
  return (
    <Card>
      <CardContent className="p-5">
        <div className={cn("mb-3 inline-flex rounded-lg p-2", iconBg)}>{icon}</div>
        <p className="mb-1 text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
        <p className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{value}</p>
        {subtitle && <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

/** Amounts that could not be converted are shown, never hidden inside a total. */
function FxNotice({ unconverted, currency }: { unconverted: Record<string, CurrencyFlow>; currency: string }) {
  const { fmt } = useMoney();
  const entries = Object.entries(unconverted);
  if (entries.length === 0) return null;
  return (
    <div
      role="status"
      className="mb-6 flex items-start gap-2 rounded-lg border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800 dark:border-warning-800 dark:bg-warning-950/30 dark:text-warning-200"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <span>
        Totals are in {currency} and exclude amounts with no exchange rate on file:{" "}
        {entries
          .map(([ccy, flow]) => `${ccy} ${fmt(flow.expenses, ccy)} spent / ${fmt(flow.income, ccy)} received`)
          .join("; ")}
        . They are listed separately rather than converted with a guessed rate.
      </span>
    </div>
  );
}

function ComparisonCard({
  kind,
  onKindChange,
  data,
  isLoading,
  currency,
}: {
  kind: PeriodKind;
  onKindChange: (k: PeriodKind) => void;
  data?: ComparisonResponse;
  isLoading: boolean;
  currency: string;
}) {
  const { fmt, pct } = useMoney();
  const rows: { label: string; current: number; prior: number; delta: number; invert?: boolean }[] = data
    ? [
        { label: "Income", current: data.current.income, prior: data.prior.income, delta: data.delta.income },
        { label: "Expenses", current: data.current.expenses, prior: data.prior.expenses, delta: data.delta.expenses, invert: true },
        { label: "Net", current: data.current.net, prior: data.prior.net, delta: data.delta.net },
      ]
    : [];
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle>Period comparison</CardTitle>
          <CardDescription>
            {data ? `${data.current.start} → ${data.current.end} vs ${data.prior.start} → ${data.prior.end}` : "Current vs previous period"}
          </CardDescription>
        </div>
        <Select
          options={COMPARISON_OPTIONS}
          value={kind}
          onChange={(v) => onKindChange(v as PeriodKind)}
          className="w-full sm:w-64"
        />
      </CardHeader>
      <CardContent>
        {isLoading || !data ? (
          <SkeletonChart className="h-32" />
        ) : (
          <dl className="divide-y divide-slate-100 dark:divide-slate-800">
            {rows.map(({ label, current, prior, delta, invert }) => {
              const good = invert ? delta <= 0 : delta >= 0;
              return (
                <div key={label} className="grid grid-cols-3 gap-2 py-2 text-sm">
                  <dt className="text-slate-500 dark:text-slate-400">{label}</dt>
                  <dd className="text-right font-medium text-slate-900 dark:text-white">
                    {fmt(current, currency)}
                    <span className="block text-xs font-normal text-slate-400">was {fmt(prior, currency)}</span>
                  </dd>
                  <dd
                    className={cn(
                      "flex items-start justify-end gap-1 text-right font-medium",
                      good ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400",
                    )}
                  >
                    {delta >= 0 ? <ArrowUpRight className="h-4 w-4" aria-hidden /> : <ArrowDownRight className="h-4 w-4" aria-hidden />}
                    {fmt(delta, currency)}
                  </dd>
                </div>
              );
            })}
            <div className="grid grid-cols-3 gap-2 py-2 text-sm">
              <dt className="text-slate-500 dark:text-slate-400">Savings rate</dt>
              <dd className="text-right font-medium text-slate-900 dark:text-white">
                {data.current.savings_rate === null ? "—" : pct(data.current.savings_rate * 100, 1)}
                <span className="block text-xs font-normal text-slate-400">
                  was {data.prior.savings_rate === null ? "—" : pct(data.prior.savings_rate * 100, 1)}
                </span>
              </dd>
              <dd className="text-right font-medium text-slate-700 dark:text-slate-200">
                {data.delta.savings_rate_points === null ? "—" : `${data.delta.savings_rate_points >= 0 ? "+" : ""}${data.delta.savings_rate_points.toFixed(1)} pts`}
              </dd>
            </div>
          </dl>
        )}
        {data && !data.fx_complete && (
          <p className="mt-2 text-xs text-warning-700 dark:text-warning-300">Some amounts in this comparison have no exchange rate and are excluded.</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function CashflowPage() {
  const [period, setPeriod] = useState<TimePeriod>("6m");
  const [comparisonKind, setComparisonKind] = useState<PeriodKind>("month");
  const [breakdownMonth, setBreakdownMonth] = useState<string | null>(null);
  const { view } = useCurrencyView();
  const currency = viewCurrency(view);
  const { fmt, pct } = useMoney();

  const range = useMemo(() => periodToRange(period), [period]);

  const summary = useQuery<MonthlySummaryResponse>({
    queryKey: ["cashflow", "summary", range.start, range.end, currency],
    queryFn: () =>
      getJson(`/v1/cashflow/summary?start_date=${range.start}&end_date=${range.end}&reporting_currency=${currency}`),
  });
  const months: MonthlySummary[] = useMemo(() => summary.data?.data ?? [], [summary.data]);
  const selectedMonth = breakdownMonth && months.some((m) => m.month === breakdownMonth) ? breakdownMonth : months[months.length - 1]?.month ?? null;

  const expenses = useQuery<CategoryBreakdownResponse>({
    queryKey: ["cashflow", "categories", selectedMonth, "expense", currency],
    enabled: selectedMonth !== null,
    queryFn: () => getJson(`/v1/cashflow/categories?month=${selectedMonth}&kind=expense&reporting_currency=${currency}`),
  });
  const income = useQuery<CategoryBreakdownResponse>({
    queryKey: ["cashflow", "categories", selectedMonth, "income", currency],
    enabled: selectedMonth !== null,
    queryFn: () => getJson(`/v1/cashflow/categories?month=${selectedMonth}&kind=income&reporting_currency=${currency}`),
  });
  const comparison = useQuery<ComparisonResponse>({
    queryKey: ["cashflow", "comparison", comparisonKind, currency],
    queryFn: () => getJson(`/v1/cashflow/comparison?kind=${comparisonKind}&reporting_currency=${currency}`),
  });

  const totals = useMemo(() => sumMonths(months), [months]);
  const chartData = useMemo(() => toCashflowSummaryData(months), [months]);
  const monthOptions = useMemo(() => months.map((m) => ({ value: m.month, label: monthLabel(m.month) })).reverse(), [months]);

  const columns: ColumnDef<MonthlySummary>[] = [
    { id: "month", header: "Month", accessorKey: "month", cell: (v: string) => monthLabel(v) },
    { id: "income", header: "Income", accessorKey: "income", align: "right", cell: (v: number) => fmt(v, currency) },
    { id: "expenses", header: "Expenses", accessorKey: "expenses", align: "right", cell: (v: number) => fmt(v, currency) },
    {
      id: "net",
      header: "Net",
      accessorKey: "net",
      align: "right",
      cell: (v: number) => (
        <span className={v >= 0 ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400"}>{fmt(v, currency)}</span>
      ),
    },
    {
      id: "savings_rate",
      header: "Savings rate",
      accessorKey: "savings_rate",
      align: "right",
      cell: (v: number | null) => (v === null ? "—" : pct(v * 100, 1)),
    },
    {
      id: "fx",
      header: "FX",
      accessorKey: "fx_complete",
      align: "center",
      cell: (v: boolean) => (v ? <Badge variant="success">Complete</Badge> : <Badge variant="warning">Partial</Badge>),
    },
  ];

  const header = (
    <PageHeader
      title="Cash Flow"
      description="Income, spending and what is left, month by month. Transfers and investment trades are excluded."
      actions={<PeriodSelector selectedPeriod={period} onPeriodChange={setPeriod} periods={CASHFLOW_PERIODS} />}
    />
  );

  if (summary.isError) {
    return (
      <PageLayout title="Cash Flow">
        {header}
        <Card>
          <CardContent className="flex flex-col items-start gap-3 p-6">
            <p className="text-sm text-slate-600 dark:text-slate-300">Could not load cash flow: {(summary.error as Error).message}</p>
            <Button variant="secondary" onClick={() => summary.refetch()}>
              Try again
            </Button>
          </CardContent>
        </Card>
      </PageLayout>
    );
  }

  if (summary.isLoading) {
    return (
      <PageLayout title="Cash Flow">
        {header}
        <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonMetricCard key={i} />
          ))}
        </div>
        <SkeletonChart />
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Cash Flow" description="Monthly income, expenses and savings">
      {header}

      <FxNotice unconverted={totals.unconverted} currency={currency} />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4"
        aria-label="Period totals"
      >
        <MetricCard title="Income" value={fmt(totals.income, currency)} subtitle={`${months.length} months`} icon={<TrendingUp className="h-5 w-5" />} tone="good" />
        <MetricCard title="Expenses" value={fmt(totals.expenses, currency)} subtitle={`${months.length} months`} icon={<TrendingDown className="h-5 w-5" />} tone="bad" />
        <MetricCard
          title="Net"
          value={fmt(totals.net, currency)}
          subtitle={totals.net >= 0 ? "Saved" : "Overspent"}
          icon={totals.net >= 0 ? <PiggyBank className="h-5 w-5" /> : <ArrowDownRight className="h-5 w-5" />}
          tone={totals.net >= 0 ? "good" : "bad"}
        />
        <MetricCard
          title="Savings rate"
          value={totals.savings_rate === null ? "—" : pct(totals.savings_rate * 100, 1)}
          subtitle={totals.savings_rate === null ? "No income in period" : "Net ÷ income"}
          icon={<PiggyBank className="h-5 w-5" />}
        />
      </motion.div>

      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Monthly cash flow</CardTitle>
            <CardDescription>Income and expenses stacked, net per month and the running total</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartTransition isLoading={summary.isFetching && months.length === 0}>
              <CashflowSummary data={chartData} currency={currency} />
            </ChartTransition>
          </CardContent>
        </Card>
        <div className="lg:col-span-2">
          <ComparisonCard kind={comparisonKind} onKindChange={setComparisonKind} data={comparison.data} isLoading={comparison.isLoading} currency={currency} />
        </div>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle>Spending by category</CardTitle>
              <CardDescription>{selectedMonth ? monthLabel(selectedMonth) : "No month selected"}</CardDescription>
            </div>
            {monthOptions.length > 0 && (
              <Select options={monthOptions} value={selectedMonth ?? undefined} onChange={setBreakdownMonth} className="w-full sm:w-40" />
            )}
          </CardHeader>
          <CardContent>
            <ChartTransition isLoading={expenses.isLoading}>
              {expenses.data && expenses.data.categories.length > 0 ? (
                <CategoryBreakdown data={toCategoryData(expenses.data.categories)} currency={currency} showLegend maxLegendHeight="max-h-40" />
              ) : (
                <p className="py-10 text-center text-sm text-slate-500">No spending recorded for this month.</p>
              )}
            </ChartTransition>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Income by source</CardTitle>
            <CardDescription>{selectedMonth ? monthLabel(selectedMonth) : "No month selected"}</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartTransition isLoading={income.isLoading}>
              {income.data && income.data.categories.length > 0 ? (
                <CategoryBreakdown data={toCategoryData(income.data.categories)} currency={currency} showLegend maxLegendHeight="max-h-40" />
              ) : (
                <p className="py-10 text-center text-sm text-slate-500">No income recorded for this month.</p>
              )}
            </ChartTransition>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Month by month</CardTitle>
          <CardDescription>Totals in {currency}; FX shows whether every currency could be converted</CardDescription>
        </CardHeader>
        <CardContent>
          <Table<MonthlySummary>
            data={[...months].reverse()}
            columns={columns}
            compact
            getRowKey={(row) => row.month}
            emptyMessage="No transactions in this period."
          />
        </CardContent>
      </Card>
    </PageLayout>
  );
}
