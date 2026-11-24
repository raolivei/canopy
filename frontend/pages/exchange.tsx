import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeftRight, ArrowRight, Pencil, Plus, Trash2 } from "lucide-react";

import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { ConfirmModal, Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { SkeletonMetricCard, SkeletonTable } from "@/components/ui/Skeleton";
import { ColumnDef, Table } from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";
import { useMoney } from "@/hooks/useMoney";
import type { Exchange, ExchangeProvider, ExchangeSummary, PairSummary } from "@/types/exchange";
import { CURRENCY_OPTIONS } from "@/utils/currencies";
import {
  ExchangeDraft,
  ExchangeDraftErrors,
  PROVIDER_LABEL,
  PROVIDER_OPTIONS,
  assetOptions,
  draftEffectiveRate,
  draftFromExchange,
  draftToInput,
  emptyDraft,
  formatRate,
  hasErrors,
  legName,
  validateDraft,
} from "@/utils/exchangeMapping";

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

interface AccountLite {
  id: string;
  name: string;
  currency: string;
  institution?: string | null;
}

const NO_ACCOUNT = { value: "", label: "No linked account" };

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{children}</label>;
}

function ExchangeFormModal({
  isOpen,
  onClose,
  initial,
  accountOptions,
  onSubmit,
  saving,
  serverError,
}: {
  isOpen: boolean;
  onClose: () => void;
  initial?: Exchange;
  accountOptions: { value: string; label: string }[];
  onSubmit: (draft: ExchangeDraft) => void;
  saving: boolean;
  serverError: string | null;
}) {
  const [draft, setDraft] = useState<ExchangeDraft>(emptyDraft());
  const [errors, setErrors] = useState<ExchangeDraftErrors>({});
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setDraft(initial ? draftFromExchange(initial) : emptyDraft());
      setErrors({});
      setTouched(false);
    }
  }, [isOpen, initial]);

  const update = (patch: Partial<ExchangeDraft>) => {
    const next = { ...draft, ...patch };
    setDraft(next);
    if (touched) setErrors(validateDraft(next));
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const found = validateDraft(draft);
    setErrors(found);
    setTouched(true);
    if (!hasErrors(found)) onSubmit(draft);
  };

  const rate = draftEffectiveRate(draft);
  const accounts = [NO_ACCOUNT, ...accountOptions];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initial ? "Edit exchange" : "New exchange"}
      description="Record a currency conversion between your own balances."
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" form="exchange-form" variant="primary" loading={saving} loadingText="Saving…">
            {initial ? "Save changes" : "Add exchange"}
          </Button>
        </>
      }
    >
      <form id="exchange-form" onSubmit={submit} noValidate className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label="Date"
            type="date"
            value={draft.date}
            onChange={(e) => update({ date: e.target.value })}
            error={errors.date}
          />
          <div>
            <FieldLabel>Provider</FieldLabel>
            <Select
              options={PROVIDER_OPTIONS}
              value={draft.provider}
              onChange={(v) => update({ provider: v as ExchangeProvider })}
            />
          </div>
        </div>

        <fieldset className="space-y-3 rounded-lg border border-slate-200 p-3 dark:border-slate-700">
          <legend className="px-1 text-sm font-medium text-slate-700 dark:text-slate-300">You sent</legend>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-[10rem_1fr]">
            <div>
              <FieldLabel>From currency</FieldLabel>
              <Select
                options={CURRENCY_OPTIONS}
                value={draft.from_currency}
                onChange={(v) => update({ from_currency: v })}
                searchable
              />
            </div>
            <Input
              label="Amount sent"
              inputMode="decimal"
              value={draft.from_amount}
              onChange={(e) => update({ from_amount: e.target.value })}
              error={errors.from_amount}
              placeholder="1000.00"
              helperText="Total that left your balance, fees included"
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <FieldLabel>From account</FieldLabel>
              <Select options={accounts} value={draft.from_asset_id} onChange={(v) => update({ from_asset_id: v })} />
            </div>
            <Input
              label="From label"
              value={draft.from_label}
              onChange={(e) => update({ from_label: e.target.value })}
              error={errors.from_label}
              placeholder="Wise CAD balance"
            />
          </div>
        </fieldset>

        <fieldset className="space-y-3 rounded-lg border border-slate-200 p-3 dark:border-slate-700">
          <legend className="px-1 text-sm font-medium text-slate-700 dark:text-slate-300">You received</legend>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-[10rem_1fr]">
            <div>
              <FieldLabel>To currency</FieldLabel>
              <Select
                options={CURRENCY_OPTIONS}
                value={draft.to_currency}
                onChange={(v) => update({ to_currency: v })}
                error={errors.to_currency}
                searchable
              />
              {errors.to_currency && (
                <p className="mt-1 text-xs text-danger-600 dark:text-danger-400">{errors.to_currency}</p>
              )}
            </div>
            <Input
              label="Amount received"
              inputMode="decimal"
              value={draft.to_amount}
              onChange={(e) => update({ to_amount: e.target.value })}
              error={errors.to_amount}
              placeholder="3900.00"
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <FieldLabel>To account</FieldLabel>
              <Select options={accounts} value={draft.to_asset_id} onChange={(v) => update({ to_asset_id: v })} />
            </div>
            <Input
              label="To label"
              value={draft.to_label}
              onChange={(e) => update({ to_label: e.target.value })}
              error={errors.to_label}
              placeholder="BRL account"
            />
          </div>
        </fieldset>

        <p className="text-sm text-slate-600 dark:text-slate-300" aria-live="polite">
          Effective rate (all-in):{" "}
          <span className="font-medium tabular-nums">
            {rate === null ? "—" : formatRate(rate, draft.from_currency, draft.to_currency)}
          </span>
        </p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Input
            label="Fee"
            inputMode="decimal"
            value={draft.fee_amount}
            onChange={(e) => update({ fee_amount: e.target.value })}
            error={errors.fee_amount}
            placeholder="0.00"
            helperText="Already part of the amount sent"
          />
          <div>
            <FieldLabel>Fee currency</FieldLabel>
            <Select
              options={CURRENCY_OPTIONS}
              value={draft.fee_currency || draft.from_currency}
              onChange={(v) => update({ fee_currency: v })}
              searchable
            />
          </div>
          <Input
            label="Quoted rate"
            inputMode="decimal"
            value={draft.quoted_rate}
            onChange={(e) => update({ quoted_rate: e.target.value })}
            error={errors.quoted_rate}
            helperText="Optional, as shown by the provider"
          />
        </div>

        <Textarea
          label="Notes"
          value={draft.notes}
          onChange={(e) => update({ notes: e.target.value })}
          error={errors.notes}
          rows={2}
        />

        {serverError && (
          <p role="alert" className="text-sm text-danger-600 dark:text-danger-400">
            {serverError}
          </p>
        )}
      </form>
    </Modal>
  );
}

function PairCard({ pair }: { pair: PairSummary }) {
  const { fmt, pct } = useMoney();
  const fees = Object.entries(pair.fees);
  return (
    <Card>
      <CardContent className="space-y-2 p-5">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500 dark:text-slate-400">
          {pair.from_currency} <ArrowRight className="h-3.5 w-3.5" aria-hidden /> {pair.to_currency}
          <Badge variant="secondary" size="sm">
            {pair.count} {pair.count === 1 ? "exchange" : "exchanges"}
          </Badge>
        </div>
        <div className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
          {fmt(pair.total_to, pair.to_currency)}
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          from {fmt(pair.total_from, pair.from_currency)} · avg{" "}
          {formatRate(pair.average_rate, pair.from_currency, pair.to_currency)}
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Fees (included): {fees.length ? fees.map(([ccy, amount]) => fmt(amount, ccy)).join(" + ") : "none recorded"}
        </p>
        {pair.spread_pct !== null && pair.spread_cost !== null ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Spread vs Bank of Canada: {pct(pair.spread_pct)} ({fmt(pair.spread_cost, pair.to_currency)}
            {pair.benchmark_coverage < pair.count ? `, ${pair.benchmark_coverage} of ${pair.count} with a rate` : ""})
          </p>
        ) : (
          <p className="text-xs text-slate-400 dark:text-slate-500">No reference rate for this pair</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function ExchangePage() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { fmt, pct } = useMoney();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Exchange | undefined>(undefined);
  const [deleting, setDeleting] = useState<Exchange | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const exchanges = useQuery<Exchange[]>({ queryKey: ["exchanges"], queryFn: () => api("/v1/exchange/") });
  const summary = useQuery<ExchangeSummary>({ queryKey: ["exchange-summary"], queryFn: () => api("/v1/exchange/summary") });
  const accounts = useQuery<{ accounts: AccountLite[] }>({
    queryKey: ["accounts-lite"],
    queryFn: () => api("/v1/accounts/"),
  });

  const accountOptions = useMemo(() => assetOptions(accounts.data?.accounts ?? []), [accounts.data]);
  const assetNames = useMemo(
    () =>
      new Map(
        (accounts.data?.accounts ?? [])
          .filter((a) => a.id.startsWith("asset:"))
          .map((a) => [a.id.slice("asset:".length), a.name] as [string, string]),
      ),
    [accounts.data],
  );
  const list = exchanges.data ?? [];

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["exchanges"] });
    queryClient.invalidateQueries({ queryKey: ["exchange-summary"] });
  };

  const save = useMutation({
    mutationFn: (draft: ExchangeDraft) => {
      const input = draftToInput(draft);
      return editing
        ? api<Exchange>(`/v1/exchange/${editing.id}`, { method: "PUT", body: JSON.stringify(input) })
        : api<Exchange>("/v1/exchange/", { method: "POST", body: JSON.stringify(input) });
    },
    onSuccess: () => {
      setFormOpen(false);
      setServerError(null);
      refresh();
      addToast({ title: editing ? "Exchange updated" : "Exchange added", variant: "success" });
    },
    onError: (error: Error) => setServerError(error.message),
  });

  const remove = useMutation({
    mutationFn: (exchange: Exchange) => api(`/v1/exchange/${exchange.id}`, { method: "DELETE" }),
    onSuccess: () => {
      setDeleting(null);
      refresh();
      addToast({ title: "Exchange deleted", variant: "success" });
    },
    onError: (error: Error) => addToast({ title: "Could not delete exchange", description: error.message, variant: "danger" }),
  });

  const openCreate = () => {
    setEditing(undefined);
    setServerError(null);
    setFormOpen(true);
  };
  const openEdit = (exchange: Exchange) => {
    setEditing(exchange);
    setServerError(null);
    setFormOpen(true);
  };

  const columns: ColumnDef<Exchange>[] = [
    { id: "date", header: "Date", accessorKey: "date" },
    {
      id: "provider",
      header: "Provider",
      accessorKey: "provider",
      cell: (v: ExchangeProvider) => <Badge variant="outline">{PROVIDER_LABEL[v] ?? v}</Badge>,
    },
    {
      id: "from",
      header: "Sent",
      accessorKey: "from_amount",
      align: "right",
      cell: (_: number, row: Exchange) => (
        <div>
          <div className="tabular-nums">{fmt(row.from_amount, row.from_currency)}</div>
          <div className="text-xs text-slate-400">{legName(row.from_asset_id, row.from_label, row.from_currency, assetNames)}</div>
        </div>
      ),
    },
    {
      id: "to",
      header: "Received",
      accessorKey: "to_amount",
      align: "right",
      cell: (_: number, row: Exchange) => (
        <div>
          <div className="tabular-nums">{fmt(row.to_amount, row.to_currency)}</div>
          <div className="text-xs text-slate-400">{legName(row.to_asset_id, row.to_label, row.to_currency, assetNames)}</div>
        </div>
      ),
    },
    {
      id: "rate",
      header: "Rate",
      accessorKey: "effective_rate",
      align: "right",
      cell: (_: number, row: Exchange) => (
        <div>
          <div className="tabular-nums">{formatRate(row.effective_rate, row.from_currency, row.to_currency)}</div>
          {row.benchmark && (
            <div className="text-xs text-slate-400">{pct(row.benchmark.spread_pct)} vs Bank of Canada</div>
          )}
        </div>
      ),
    },
    {
      id: "fee",
      header: "Fee",
      accessorKey: "fee_amount",
      align: "right",
      cell: (_: number | null, row: Exchange) =>
        row.fee_amount === null ? "—" : fmt(row.fee_amount, row.fee_currency ?? row.from_currency),
    },
    {
      id: "actions",
      header: "",
      align: "right",
      cell: (_: unknown, row: Exchange) => (
        <div className="flex justify-end gap-1">
          <Button
            variant="ghost"
            size="sm"
            ariaLabel={`Edit exchange on ${row.date}`}
            onClick={(e) => {
              e.stopPropagation();
              openEdit(row);
            }}
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            ariaLabel={`Delete exchange on ${row.date}`}
            onClick={(e) => {
              e.stopPropagation();
              setDeleting(row);
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const header = (
    <PageHeader
      title="Exchange"
      description="Currency conversions between your own balances. A standalone log: Cash Flow and Budgets are unaffected."
      actions={
        <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
          Add exchange
        </Button>
      }
    />
  );

  let body: React.ReactNode;
  if (exchanges.isError) {
    body = (
      <Card>
        <CardContent className="flex flex-col items-start gap-3 p-6">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Could not load exchanges: {(exchanges.error as Error).message}
          </p>
          <Button variant="secondary" onClick={() => exchanges.refetch()}>
            Try again
          </Button>
        </CardContent>
      </Card>
    );
  } else if (exchanges.isLoading) {
    body = (
      <>
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SkeletonMetricCard key={i} />
          ))}
        </div>
        <SkeletonTable />
      </>
    );
  } else if (list.length === 0) {
    body = (
      <Card variant="highlight">
        <CardContent className="flex flex-col items-center gap-4 p-10 text-center">
          <div className="rounded-xl bg-primary-100 p-3 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
            <ArrowLeftRight className="h-6 w-6" aria-hidden />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">No exchanges yet</h2>
            <p className="mt-1 max-w-md text-sm text-slate-600 dark:text-slate-400">
              Log each time you convert money, for example CAD to USD in Wise or CAD to BRL. Canopy tracks your
              effective rate, fees and, for CAD/USD, the spread against the Bank of Canada rate.
            </p>
          </div>
          <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
            Add your first exchange
          </Button>
        </CardContent>
      </Card>
    );
  } else {
    body = (
      <>
        {summary.data && summary.data.pairs.length > 0 && (
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {summary.data.pairs.map((pair) => (
              <PairCard key={`${pair.from_currency}-${pair.to_currency}`} pair={pair} />
            ))}
          </div>
        )}
        <Card>
          <CardContent noPadding>
            <Table
              data={list}
              columns={columns}
              compact
              getRowKey={(row) => row.id}
              onRowClick={openEdit}
              emptyMessage="No exchanges"
            />
          </CardContent>
        </Card>
      </>
    );
  }

  return (
    <PageLayout title="Exchange" description="Currency exchange log">
      {header}
      {body}

      <ExchangeFormModal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        initial={editing}
        accountOptions={accountOptions}
        onSubmit={(draft) => save.mutate(draft)}
        saving={save.isPending}
        serverError={serverError}
      />

      <ConfirmModal
        isOpen={deleting !== null}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && remove.mutate(deleting)}
        title="Delete exchange?"
        description={
          deleting
            ? `${fmt(deleting.from_amount, deleting.from_currency)} → ${fmt(deleting.to_amount, deleting.to_currency)} on ${deleting.date} will be removed.`
            : undefined
        }
        confirmText="Delete"
        variant="danger"
        loading={remove.isPending}
      />
    </PageLayout>
  );
}
