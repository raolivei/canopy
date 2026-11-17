import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ChevronLeft, ChevronRight, Pencil, PiggyBank, Plus, Trash2, Wallet } from "lucide-react";

import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ConfirmModal, Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { SkeletonChart, SkeletonMetricCard } from "@/components/ui/Skeleton";
import { ColumnDef, Table } from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";
import { ChartTransition } from "@/components/ChartTransition";
import { BudgetVsActualsChart } from "@/components/charts/BudgetVsActualsChart";
import { useMoney } from "@/hooks/useMoney";
import type { Budget, BudgetPeriod, BudgetStatus, CategoryStatus } from "@/types/budget";
import {
  BudgetDraft,
  DraftErrors,
  HEALTH_LABEL,
  HEALTH_VARIANT,
  currentMonthKey,
  diffCategories,
  draftFromBudget,
  draftToInput,
  emptyDraft,
  hasErrors,
  isMonthKey,
  newCategoryDraft,
  shiftMonthKey,
  statusPeriodLabel,
  toBudgetVsActuals,
  validateDraft,
} from "@/utils/budgetMapping";
import { monthLabel } from "@/utils/cashflowMapping";
import { cn } from "@/utils/cn";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // keep the status-based message
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

const PERIOD_OPTIONS = [
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

function BudgetFormModal({
  isOpen,
  onClose,
  initial,
  onSubmit,
  saving,
  serverError,
}: {
  isOpen: boolean;
  onClose: () => void;
  initial?: Budget;
  onSubmit: (draft: BudgetDraft) => void;
  saving: boolean;
  serverError: string | null;
}) {
  const [draft, setDraft] = useState<BudgetDraft>(emptyDraft());
  const [errors, setErrors] = useState<DraftErrors>({ categories: {} });
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setDraft(initial ? draftFromBudget(initial) : emptyDraft());
      setErrors({ categories: {} });
      setTouched(false);
    }
  }, [isOpen, initial]);

  const update = (patch: Partial<BudgetDraft>) => {
    const next = { ...draft, ...patch };
    setDraft(next);
    if (touched) setErrors(validateDraft(next));
  };
  const updateCategory = (key: string, patch: { category_name?: string; amount_limit?: string }) =>
    update({ categories: draft.categories.map((c) => (c.key === key ? { ...c, ...patch } : c)) });

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const found = validateDraft(draft);
    setErrors(found);
    setTouched(true);
    if (!hasErrors(found)) onSubmit(draft);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initial ? "Edit budget" : "New budget"}
      description="A total for the period, with optional limits per category."
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" form="budget-form" variant="primary" loading={saving} loadingText="Saving…">
            {initial ? "Save changes" : "Create budget"}
          </Button>
        </>
      }
    >
      <form id="budget-form" onSubmit={submit} noValidate className="space-y-4">
        <Input
          label="Name"
          value={draft.name}
          onChange={(e) => update({ name: e.target.value })}
          error={errors.name}
          placeholder="Household"
          autoFocus
        />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label="Total amount (CAD)"
            inputMode="decimal"
            value={draft.amount}
            onChange={(e) => update({ amount: e.target.value })}
            error={errors.amount}
            placeholder="2000.00"
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Period</label>
            <Select options={PERIOD_OPTIONS} value={draft.period} onChange={(v) => update({ period: v as BudgetPeriod })} />
            <p className="mt-1 text-xs text-slate-400">Quarterly periods are not supported yet (#116).</p>
          </div>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-medium text-slate-700 dark:text-slate-300">Category limits</legend>
          {draft.categories.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-slate-400">No category limits. The total still tracks all spending.</p>
          )}
          {draft.categories.map((category, index) => {
            const err = errors.categories[category.key] ?? {};
            return (
              <div key={category.key} className="grid grid-cols-[1fr_auto_auto] items-start gap-2 sm:grid-cols-[1fr_10rem_auto]">
                <Input
                  aria-label={`Category ${index + 1} name`}
                  value={category.category_name}
                  onChange={(e) => updateCategory(category.key, { category_name: e.target.value })}
                  error={err.name}
                  placeholder="Groceries"
                />
                <Input
                  aria-label={`Category ${index + 1} limit`}
                  inputMode="decimal"
                  value={category.amount_limit}
                  onChange={(e) => updateCategory(category.key, { amount_limit: e.target.value })}
                  error={err.limit}
                  placeholder="600.00"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  ariaLabel={`Remove category ${index + 1}`}
                  onClick={() => update({ categories: draft.categories.filter((c) => c.key !== category.key) })}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            );
          })}
          <Button
            type="button"
            variant="secondary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => update({ categories: [...draft.categories, newCategoryDraft()] })}
          >
            Add category limit
          </Button>
        </fieldset>

        {serverError && (
          <p role="alert" className="text-sm text-danger-600 dark:text-danger-400">
            {serverError}
          </p>
        )}
      </form>
    </Modal>
  );
}

function MonthPicker({ value, onChange }: { value: string; onChange: (next: string) => void }) {
  return (
    <div className="flex items-center gap-1" role="group" aria-label="Status month">
      <Button variant="ghost" size="sm" ariaLabel="Previous month" onClick={() => onChange(shiftMonthKey(value, -1))}>
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <input
        type="month"
        aria-label="Month"
        value={value}
        onChange={(e) => isMonthKey(e.target.value) && onChange(e.target.value)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
      />
      <Button variant="ghost" size="sm" ariaLabel="Next month" onClick={() => onChange(shiftMonthKey(value, 1))}>
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}

function Metric({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="mb-1 text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
        <div className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{value}</div>
        {hint && <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export default function BudgetsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { fmt, pct } = useMoney();

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [month, setMonth] = useState<string>(() => currentMonthKey());
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Budget | undefined>(undefined);
  const [deleting, setDeleting] = useState<Budget | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const budgets = useQuery<Budget[]>({ queryKey: ["budgets"], queryFn: () => api("/v1/budgets/") });
  const list = useMemo(() => budgets.data ?? [], [budgets.data]);
  const selected = list.find((b) => b.id === selectedId) ?? list[0] ?? null;

  const status = useQuery<BudgetStatus>({
    queryKey: ["budget-status", selected?.id, month],
    enabled: selected !== null,
    queryFn: () => api(`/v1/budgets/${selected!.id}/status?month=${month}`),
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["budgets"] });
    queryClient.invalidateQueries({ queryKey: ["budget-status"] });
  };

  const save = useMutation({
    mutationFn: async (draft: BudgetDraft) => {
      const input = draftToInput(draft);
      if (!editing) {
        return api<Budget>("/v1/budgets/", { method: "POST", body: JSON.stringify(input) });
      }
      await api<Budget>(`/v1/budgets/${editing.id}`, {
        method: "PUT",
        body: JSON.stringify({ name: input.name, amount: input.amount, period: input.period }),
      });
      const diff = diffCategories(editing, draft);
      for (const id of diff.removed) await api(`/v1/budgets/${editing.id}/categories/${id}`, { method: "DELETE" });
      for (const c of diff.changed) {
        await api(`/v1/budgets/${editing.id}/categories/${c.id}`, {
          method: "PUT",
          body: JSON.stringify({ category_name: c.category_name, amount_limit: c.amount_limit }),
        });
      }
      for (const c of diff.added) await api(`/v1/budgets/${editing.id}/categories`, { method: "POST", body: JSON.stringify(c) });
      return api<Budget>(`/v1/budgets/${editing.id}`);
    },
    onSuccess: (budget) => {
      setFormOpen(false);
      setServerError(null);
      setSelectedId(budget.id);
      refresh();
      addToast({ title: editing ? "Budget updated" : "Budget created", variant: "success" });
    },
    onError: (error: Error) => setServerError(error.message),
  });

  const remove = useMutation({
    mutationFn: (budget: Budget) => api(`/v1/budgets/${budget.id}`, { method: "DELETE" }),
    onSuccess: () => {
      setDeleting(null);
      setSelectedId(null);
      refresh();
      addToast({ title: "Budget deleted", variant: "success" });
    },
    onError: (error: Error) => addToast({ title: "Could not delete budget", description: error.message, variant: "danger" }),
  });

  const openCreate = () => {
    setEditing(undefined);
    setServerError(null);
    setFormOpen(true);
  };
  const openEdit = (budget: Budget) => {
    setEditing(budget);
    setServerError(null);
    setFormOpen(true);
  };

  const columns: ColumnDef<CategoryStatus>[] = [
    { id: "category", header: "Category", accessorKey: "category_name" },
    { id: "limit", header: "Limit", accessorKey: "amount_limit", align: "right", cell: (v: number) => fmt(v, "CAD") },
    { id: "actual", header: "Spent", accessorKey: "actual_spent", align: "right", cell: (v: number) => fmt(v, "CAD") },
    {
      id: "remaining",
      header: "Remaining",
      accessorKey: "remaining",
      align: "right",
      cell: (v: number) => <span className={v < 0 ? "text-danger-600 dark:text-danger-400" : ""}>{fmt(v, "CAD")}</span>,
    },
    { id: "used", header: "Used", accessorKey: "percentage_used", align: "right", cell: (v: number) => pct(v, 0) },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      align: "center",
      cell: (v: CategoryStatus["status"]) => (
        <Badge variant={HEALTH_VARIANT[v]} dot>
          {HEALTH_LABEL[v]}
        </Badge>
      ),
    },
  ];

  const header = (
    <PageHeader
      title="Budgets"
      description="Planned spending per month or year, with optional limits per category"
      actions={
        <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
          New budget
        </Button>
      }
    />
  );

  if (budgets.isError) {
    return (
      <PageLayout title="Budgets">
        {header}
        <Card>
          <CardContent className="flex flex-col items-start gap-3 p-6">
            <p className="text-sm text-slate-600 dark:text-slate-300">Could not load budgets: {(budgets.error as Error).message}</p>
            <Button variant="secondary" onClick={() => budgets.refetch()}>
              Try again
            </Button>
          </CardContent>
        </Card>
      </PageLayout>
    );
  }

  const data = status.data;
  const categorised = data ? data.categories.reduce((sum, c) => sum + c.actual_spent, 0) : 0;
  const otherSpend = data ? Number((data.total_spent - categorised).toFixed(2)) : 0;
  const unconverted = data ? Object.entries(data.unconverted) : [];

  return (
    <PageLayout title="Budgets" description="Budgets and spending against them">
      {header}

      {budgets.isLoading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonMetricCard key={i} />
          ))}
        </div>
      ) : list.length === 0 ? (
        <Card variant="highlight">
          <CardContent className="flex flex-col items-center gap-4 p-10 text-center">
            <div className="rounded-xl bg-primary-100 p-3 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
              <PiggyBank className="h-6 w-6" aria-hidden />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">No budgets yet</h2>
              <p className="mt-1 max-w-md text-sm text-slate-600 dark:text-slate-400">
                Set a total for the month or year and, if you like, limits for the categories you want to watch. Spending
                is matched by transaction category.
              </p>
            </div>
            <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              Create your first budget
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-center gap-2" role="tablist" aria-label="Budgets">
            {list.map((b) => (
              <button
                key={b.id}
                type="button"
                role="tab"
                aria-selected={selected?.id === b.id}
                onClick={() => setSelectedId(b.id)}
                className={cn(
                  "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                  selected?.id === b.id
                    ? "bg-primary-600 text-white"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
                )}
              >
                {b.name}
                <span className="ml-1.5 text-xs opacity-75">{b.period}</span>
              </button>
            ))}
          </div>

          {selected && (
            <>
              <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">{selected.name}</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {fmt(selected.amount, "CAD")} per {selected.period === "yearly" ? "year" : "month"}
                    {data && ` · ${data.period_start} to ${data.period_end}`}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <MonthPicker value={month} onChange={setMonth} />
                  <Button variant="secondary" size="sm" leftIcon={<Pencil className="h-4 w-4" />} onClick={() => openEdit(selected)}>
                    Edit
                  </Button>
                  <Button variant="danger" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setDeleting(selected)}>
                    Delete
                  </Button>
                </div>
              </div>

              {data && unconverted.length > 0 && (
                <div
                  role="status"
                  className="mb-6 flex items-start gap-2 rounded-lg border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800 dark:border-warning-800 dark:bg-warning-950/30 dark:text-warning-200"
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                  <span>
                    Spend with no exchange rate on file is not counted against this CAD budget:{" "}
                    {unconverted.map(([ccy, flow]) => `${ccy} ${fmt(flow.expenses, ccy)}`).join("; ")}.
                  </span>
                </div>
              )}

              {status.isLoading || !data ? (
                <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                  {[1, 2, 3, 4].map((i) => (
                    <SkeletonMetricCard key={i} />
                  ))}
                </div>
              ) : (
                <>
                  <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4" aria-label="Budget totals">
                    <Metric label="Budget" value={fmt(data.total_budget, "CAD")} hint={statusPeriodLabel(data.period, data.period_start, monthLabel(month))} />
                    <Metric label="Spent" value={fmt(data.total_spent, "CAD")} hint={otherSpend > 0 ? `${fmt(otherSpend, "CAD")} outside category limits` : "All spend in listed categories"} />
                    <Metric
                      label="Remaining"
                      value={<span className={data.remaining < 0 ? "text-danger-600 dark:text-danger-400" : ""}>{fmt(data.remaining, "CAD")}</span>}
                      hint={pct(data.percentage_used, 0) + " used"}
                    />
                    <Metric
                      label="Status"
                      value={
                        <Badge variant={HEALTH_VARIANT[data.status]} dot className="text-sm">
                          {HEALTH_LABEL[data.status]}
                        </Badge>
                      }
                      hint="Under 80% on track, 80–100% close, above over"
                    />
                  </div>

                  <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-5">
                    <Card className="lg:col-span-3">
                      <CardHeader>
                        <CardTitle>Budget vs actual</CardTitle>
                        <CardDescription>Per category limit for {statusPeriodLabel(data.period, data.period_start, monthLabel(month))}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {data.categories.length === 0 ? (
                          <p className="py-10 text-center text-sm text-slate-500">
                            No category limits on this budget. Edit it to add some.
                          </p>
                        ) : (
                          <ChartTransition isLoading={status.isFetching && !data}>
                            <BudgetVsActualsChart data={toBudgetVsActuals(data.categories)} currency="CAD" />
                          </ChartTransition>
                        )}
                      </CardContent>
                    </Card>
                    <Card className="lg:col-span-2">
                      <CardHeader>
                        <CardTitle>How to read this</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                        <p className="flex items-start gap-2">
                          <Wallet className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden />
                          The total counts every expense in the period, including categories without a limit. Transfers and
                          investment trades are excluded.
                        </p>
                        <p>Click a category row to open those transactions.</p>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Category limits</CardTitle>
                      <CardDescription>Green under 80%, amber between 80% and 100%, red over</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Table<CategoryStatus>
                        data={data.categories}
                        columns={columns}
                        compact
                        getRowKey={(row) => row.category_id}
                        onRowClick={(row) => router.push({ pathname: "/transactions", query: { category: row.category_name } })}
                        emptyMessage="No category limits yet."
                      />
                    </CardContent>
                  </Card>
                </>
              )}
            </>
          )}
        </>
      )}

      <BudgetFormModal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        initial={editing}
        onSubmit={(draft) => save.mutate(draft)}
        saving={save.isPending}
        serverError={serverError}
      />
      <ConfirmModal
        isOpen={deleting !== null}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && remove.mutate(deleting)}
        title="Delete this budget?"
        description={deleting ? `"${deleting.name}" will be hidden from your budgets. Past status stays available in history.` : undefined}
        confirmText="Delete"
        variant="danger"
        loading={remove.isPending}
      />
    </PageLayout>
  );
}
