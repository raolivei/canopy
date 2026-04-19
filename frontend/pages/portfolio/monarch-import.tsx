import { useState } from "react";
import Link from "next/link";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  Upload,
  CheckCircle,
  AlertCircle,
  Eye,
  Trash2,
  Info,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

// ---------------------------------------------------------------------------
// Response types (mirror backend/models/monarch_import_schemas.py)
// ---------------------------------------------------------------------------

type MonarchFileReport = {
  filename: string;
  header_ok: boolean;
  rows_seen: number;
  imported: number;
  skipped_pseudo: number;
  skipped_foreign: number;
  skipped_unknown_account: number;
  skipped_ws_covered: number;
  skipped_canonical_dup: number;
  skipped_source_dup: number;
  assets_created: string[];
  liabilities_created: string[];
  assets_touched: string[];
  liabilities_touched: string[];
  warnings: string[];
};

type BalancesFileReport = {
  filename: string;
  header_ok: boolean;
  rows_seen: number;
  inserted: number;
  updated: number;
  skipped_pseudo: number;
  skipped_foreign: number;
  skipped_unknown_account: number;
  assets_created: string[];
  liabilities_created: string[];
  assets_touched: string[];
  liabilities_touched: string[];
  warnings: string[];
};

type PreviewResponse = {
  transactions: {
    files: MonarchFileReport[];
    would_import: number;
    assets_would_create: string[];
    liabilities_would_create: string[];
  };
  balances: {
    files: BalancesFileReport[];
    would_insert: number;
    would_update: number;
    assets_would_create: string[];
    liabilities_would_create: string[];
  };
};

type CommitResponse = {
  transactions: {
    files: MonarchFileReport[];
    transactions_added: number;
    assets_created: string[];
    liabilities_created: string[];
  };
  balances: {
    files: BalancesFileReport[];
    balances_inserted: number;
    balances_updated: number;
    assets_created: string[];
    liabilities_created: string[];
  };
};

function safeDetail(text: string, fallback: string): string {
  try {
    const parsed = JSON.parse(text);
    return typeof parsed.detail === "string" ? parsed.detail : fallback;
  } catch {
    return text || fallback;
  }
}

export default function MonarchImportPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [committed, setCommitted] = useState<CommitResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setPreview(null);
    setCommitted(null);
    setError(null);
  };

  const pick = (list: FileList | null) => {
    if (!list) return;
    reset();
    setFiles(Array.from(list));
  };

  const formData = () => {
    const fd = new FormData();
    for (const f of files) fd.append("files", f);
    return fd;
  };

  const post = async (path: string): Promise<Response> =>
    fetch(`${API_URL}${path}`, { method: "POST", body: formData() });

  const runPreview = async () => {
    if (files.length === 0) {
      setError("Choose a Monarch export CSV.");
      return;
    }
    setLoading(true);
    setError(null);
    setCommitted(null);
    try {
      const res = await post("/v1/monarch-import/preview");
      const text = await res.text();
      if (!res.ok) {
        setError(safeDetail(text, res.statusText));
        return;
      }
      setPreview(JSON.parse(text));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setLoading(false);
    }
  };

  const runCommit = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const res = await post("/v1/monarch-import/commit");
      const text = await res.text();
      if (!res.ok) {
        setError(safeDetail(text, res.statusText));
        return;
      }
      setCommitted(JSON.parse(text));
      setPreview(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  };

  const txReports =
    preview?.transactions.files ?? committed?.transactions.files ?? [];
  const balReports =
    preview?.balances.files ?? committed?.balances.files ?? [];

  return (
    <PageLayout title="Monarch import">
      <PageHeader
        title="Monarch Money CSV drop zone"
        description="Backfill historical transactions AND account-balance snapshots from Monarch. Drop both the transactions CSV and the balances CSV together — Canopy auto-detects each file, routes it to the right importer, autocreates accounts, skips Monarch's Transfer/Income pseudo-accounts, drops non-CAD/USD rows, and defers to Wealthsimple for any dates where WS already owns the account."
      />

      <Card className="max-w-4xl">
        <CardHeader>
          <CardTitle>Files</CardTitle>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            In Monarch: <b>Settings &rarr; Data</b>. Use both
            {" "}<b>Download transactions</b> and <b>Download account balances</b>
            {" "}— drop the two CSVs here. Balance snapshots are what fills
            RBC / Scotia / credit card balances on the Accounts page.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="flex items-start gap-2 rounded-md border border-sky-300 bg-sky-50 p-3 text-sm text-sky-800 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-200">
              <Info className="mt-0.5 h-4 w-4 shrink-0" />
              <div className="space-y-1">
                <div className="font-medium">Dedup & routing guarantees</div>
                <ul className="list-disc pl-5 text-xs leading-relaxed">
                  <li>
                    <span className="font-medium">Auto-routing:</span> files
                    with a <code>Date,Balance,Account</code> header are
                    treated as balance snapshots; everything else is parsed
                    as transactions.
                  </li>
                  <li>
                    <span className="font-medium">Layer 1 — per-account
                    cutover:</span> if Wealthsimple already owns an
                    account from date <code>X</code> onward, any Monarch
                    transaction row for that account with date &ge;{" "}
                    <code>X</code> is dropped.
                  </li>
                  <li>
                    <span className="font-medium">Layer 2 — canonical
                    hash:</span> a source-agnostic fingerprint of
                    (account, date, amount) catches cross-source
                    duplicates that slip through Layer 1.
                  </li>
                  <li>
                    <span className="font-medium">Balances upsert:</span>{" "}
                    re-uploading a balances CSV updates rows in place;
                    no duplicates, no history rewriting.
                  </li>
                  <li>
                    Liability balances (credit cards, LOC) are stored as
                    positive &ldquo;amount owed&rdquo; — Monarch&apos;s negative sign is
                    flipped automatically.
                  </li>
                </ul>
              </div>
            </div>

            <label className="block">
              <span className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Monarch CSV files (transactions + balances)
              </span>
              <input
                type="file"
                multiple
                accept=".csv,text/csv"
                onChange={(e) => pick(e.target.files)}
                className="block w-full text-sm text-slate-600 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary-50 file:text-primary-700 dark:file:bg-primary-950 dark:file:text-primary-300"
              />
            </label>

            {files.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {files.length} file{files.length === 1 ? "" : "s"} selected
                </div>
                <ul className="text-sm text-slate-600 dark:text-slate-400 list-disc pl-5 max-h-40 overflow-auto">
                  {files.map((f) => (
                    <li key={f.name}>{f.name}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                variant="ghost"
                onClick={runPreview}
                disabled={loading || files.length === 0}
                leftIcon={<Eye className="w-4 h-4" />}
              >
                {loading && !committed ? "Previewing\u2026" : "Preview"}
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={runCommit}
                disabled={loading || files.length === 0}
                leftIcon={<Upload className="w-4 h-4" />}
              >
                {loading && preview ? "Importing\u2026" : "Import"}
              </Button>
              {files.length > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setFiles([]);
                    reset();
                  }}
                  leftIcon={<Trash2 className="w-4 h-4" />}
                >
                  Clear
                </Button>
              )}
              <Link href="/">
                <Button type="button" variant="ghost">
                  Back to dashboard
                </Button>
              </Link>
            </div>

            {error && (
              <div className="flex items-start gap-2 text-sm text-danger-600 dark:text-danger-400">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {committed && (
              <div className="p-4 rounded-md bg-success-50 dark:bg-success-950/30 text-success-700 dark:text-success-300 text-sm space-y-2">
                <div className="flex items-center gap-2 font-medium">
                  <CheckCircle className="w-4 h-4" />
                  Import complete
                </div>
                <div>
                  <b>{committed.transactions.transactions_added}</b> transaction
                  {committed.transactions.transactions_added === 1 ? "" : "s"}{" "}
                  imported &middot;{" "}
                  <b>{committed.balances.balances_inserted}</b> balance snapshot
                  {committed.balances.balances_inserted === 1 ? "" : "s"}{" "}
                  inserted &middot;{" "}
                  <b>{committed.balances.balances_updated}</b> updated.
                </div>
                {(committed.transactions.assets_created.length > 0 ||
                  committed.transactions.liabilities_created.length > 0 ||
                  committed.balances.assets_created.length > 0 ||
                  committed.balances.liabilities_created.length > 0) && (
                  <div>
                    <div className="text-xs font-medium mb-1">
                      Autocreated accounts
                    </div>
                    <ul className="list-disc pl-5 text-xs opacity-90">
                      {Array.from(
                        new Set([
                          ...committed.transactions.assets_created,
                          ...committed.transactions.liabilities_created,
                          ...committed.balances.assets_created,
                          ...committed.balances.liabilities_created,
                        ]),
                      ).map((n) => (
                        <li key={n}>{n}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {preview && (
              <div className="p-4 rounded-md border border-slate-200 dark:border-slate-800 text-sm space-y-1">
                <div className="font-medium text-slate-700 dark:text-slate-200">
                  Dry run
                </div>
                <div className="text-slate-600 dark:text-slate-300">
                  Would import <b>{preview.transactions.would_import}</b>{" "}
                  transaction
                  {preview.transactions.would_import === 1 ? "" : "s"} &middot;{" "}
                  insert <b>{preview.balances.would_insert}</b> balance
                  snapshot{preview.balances.would_insert === 1 ? "" : "s"}{" "}
                  &middot; update <b>{preview.balances.would_update}</b>.
                </div>
                <div className="text-slate-600 dark:text-slate-300 text-xs">
                  Would autocreate{" "}
                  <b>
                    {
                      new Set([
                        ...preview.transactions.assets_would_create,
                        ...preview.balances.assets_would_create,
                      ]).size
                    }
                  </b>{" "}
                  asset(s) +{" "}
                  <b>
                    {
                      new Set([
                        ...preview.transactions.liabilities_would_create,
                        ...preview.balances.liabilities_would_create,
                      ]).size
                    }
                  </b>{" "}
                  liabilit
                  {new Set([
                    ...preview.transactions.liabilities_would_create,
                    ...preview.balances.liabilities_would_create,
                  ]).size === 1
                    ? "y"
                    : "ies"}
                  .
                </div>
              </div>
            )}

            {txReports.length > 0 && (
              <div className="space-y-3">
                <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                  Transaction files
                </div>
                {txReports.map((f) => (
                  <TransactionFileRow key={f.filename} f={f} />
                ))}
              </div>
            )}

            {balReports.length > 0 && (
              <div className="space-y-3">
                <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                  Balance files
                </div>
                {balReports.map((f) => (
                  <BalanceFileRow key={f.filename} f={f} />
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </PageLayout>
  );
}

function TransactionFileRow({ f }: { f: MonarchFileReport }) {
  const skippedTotal =
    f.skipped_pseudo +
    f.skipped_foreign +
    f.skipped_unknown_account +
    f.skipped_ws_covered +
    f.skipped_canonical_dup +
    f.skipped_source_dup;

  return (
    <div
      className={`rounded-md border p-4 text-sm ${
        f.header_ok
          ? "border-slate-300 dark:border-slate-700"
          : "border-danger-300 bg-danger-50 dark:border-danger-800 dark:bg-danger-950/30"
      }`}
    >
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="font-medium text-slate-800 dark:text-slate-100">
          {f.filename}
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400">
          {f.rows_seen} seen &middot; {f.imported} imported &middot;{" "}
          {skippedTotal} skipped
        </div>
      </div>
      {!f.header_ok && (
        <div className="text-danger-700 dark:text-danger-300">
          Header mismatch — doesn&rsquo;t look like a Monarch transactions
          export.
        </div>
      )}
      {f.header_ok && (
        <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-600 dark:text-slate-400 sm:grid-cols-3">
          <li>Pseudo: {f.skipped_pseudo}</li>
          <li>Foreign currency: {f.skipped_foreign}</li>
          <li>Unknown account: {f.skipped_unknown_account}</li>
          <li>Covered by Wealthsimple: {f.skipped_ws_covered}</li>
          <li>Canonical duplicates: {f.skipped_canonical_dup}</li>
          <li>Source duplicates: {f.skipped_source_dup}</li>
        </ul>
      )}
      {(f.assets_created.length > 0 || f.liabilities_created.length > 0) && (
        <div className="mt-3 text-xs text-slate-600 dark:text-slate-400">
          <span className="font-medium">Autocreated:</span>{" "}
          {[...f.assets_created, ...f.liabilities_created].join(", ")}
        </div>
      )}
      {f.warnings.length > 0 && (
        <details className="mt-2 text-xs">
          <summary className="cursor-pointer text-slate-500 dark:text-slate-400">
            {f.warnings.length} warning{f.warnings.length === 1 ? "" : "s"}
          </summary>
          <ul className="mt-1 list-disc pl-5 text-slate-500 dark:text-slate-400">
            {f.warnings.slice(0, 20).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
            {f.warnings.length > 20 && (
              <li>\u2026 and {f.warnings.length - 20} more</li>
            )}
          </ul>
        </details>
      )}
    </div>
  );
}

function BalanceFileRow({ f }: { f: BalancesFileReport }) {
  const skippedTotal =
    f.skipped_pseudo + f.skipped_foreign + f.skipped_unknown_account;
  const written = f.inserted + f.updated;

  return (
    <div
      className={`rounded-md border p-4 text-sm ${
        f.header_ok
          ? "border-slate-300 dark:border-slate-700"
          : "border-danger-300 bg-danger-50 dark:border-danger-800 dark:bg-danger-950/30"
      }`}
    >
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="font-medium text-slate-800 dark:text-slate-100">
          {f.filename}
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400">
          {f.rows_seen} seen &middot; {written} written ({f.inserted} new,{" "}
          {f.updated} updated) &middot; {skippedTotal} skipped
        </div>
      </div>
      {!f.header_ok && (
        <div className="text-danger-700 dark:text-danger-300">
          Header mismatch — expected{" "}
          <code>Date,Balance,Account</code>.
        </div>
      )}
      {f.header_ok && (
        <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-600 dark:text-slate-400 sm:grid-cols-3">
          <li>Pseudo: {f.skipped_pseudo}</li>
          <li>Foreign currency: {f.skipped_foreign}</li>
          <li>Unknown account: {f.skipped_unknown_account}</li>
          <li>Assets touched: {f.assets_touched.length}</li>
          <li>Liabilities touched: {f.liabilities_touched.length}</li>
        </ul>
      )}
      {(f.assets_created.length > 0 || f.liabilities_created.length > 0) && (
        <div className="mt-3 text-xs text-slate-600 dark:text-slate-400">
          <span className="font-medium">Autocreated:</span>{" "}
          {[...f.assets_created, ...f.liabilities_created].join(", ")}
        </div>
      )}
      {f.warnings.length > 0 && (
        <details className="mt-2 text-xs">
          <summary className="cursor-pointer text-slate-500 dark:text-slate-400">
            {f.warnings.length} warning{f.warnings.length === 1 ? "" : "s"}
          </summary>
          <ul className="mt-1 list-disc pl-5 text-slate-500 dark:text-slate-400">
            {f.warnings.slice(0, 20).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
            {f.warnings.length > 20 && (
              <li>\u2026 and {f.warnings.length - 20} more</li>
            )}
          </ul>
        </details>
      )}
    </div>
  );
}
