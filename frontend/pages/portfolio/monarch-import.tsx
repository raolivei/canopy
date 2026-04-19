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

type PreviewResponse = {
  files: MonarchFileReport[];
  would_import: number;
  assets_would_create: string[];
  liabilities_would_create: string[];
};

type CommitResponse = {
  files: MonarchFileReport[];
  transactions_added: number;
  assets_created: string[];
  liabilities_created: string[];
};

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

  const reports = preview?.files ?? committed?.files ?? [];

  return (
    <PageLayout title="Monarch import">
      <PageHeader
        title="Monarch Money CSV drop zone"
        description="Backfill historical transactions from Monarch. Canopy auto-creates accounts, skips Monarch's Transfer/Income pseudo-accounts, drops non-CAD rows, and defers to Wealthsimple for any dates where WS already owns the account."
      />

      <Card className="max-w-4xl">
        <CardHeader>
          <CardTitle>Files</CardTitle>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Export from Monarch via Settings &rarr; Data &rarr; Download
            transactions. Drop the CSV here.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="flex items-start gap-2 rounded-md border border-sky-300 bg-sky-50 p-3 text-sm text-sky-800 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-200">
              <Info className="mt-0.5 h-4 w-4 shrink-0" />
              <div className="space-y-1">
                <div className="font-medium">Dedup guarantees</div>
                <ul className="list-disc pl-5 text-xs leading-relaxed">
                  <li>
                    <span className="font-medium">Layer 1 - per-account
                    cutover:</span> if Wealthsimple already owns an
                    account from date <code>X</code> onward, any Monarch
                    row for that account with date &ge; <code>X</code> is
                    dropped.
                  </li>
                  <li>
                    <span className="font-medium">Layer 2 - canonical
                    hash:</span> a source-agnostic fingerprint of
                    (account, date, amount) catches cross-source
                    duplicates that slip through Layer 1.
                  </li>
                  <li>
                    Re-uploading the same Monarch CSV is a no-op
                    (source hash match).
                  </li>
                </ul>
              </div>
            </div>

            <label className="block">
              <span className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Monarch transactions CSV
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
              <div className="p-4 rounded-md bg-success-50 dark:bg-success-950/30 text-success-700 dark:text-success-300 text-sm space-y-1">
                <div className="flex items-center gap-2 font-medium">
                  <CheckCircle className="w-4 h-4" />
                  Import complete
                </div>
                <div>
                  {committed.transactions_added} transaction
                  {committed.transactions_added === 1 ? "" : "s"} imported.{" "}
                  {committed.assets_created.length} asset
                  {committed.assets_created.length === 1 ? "" : "s"} +{" "}
                  {committed.liabilities_created.length} liabilit
                  {committed.liabilities_created.length === 1 ? "y" : "ies"}
                  {" "}autocreated.
                </div>
                {(committed.assets_created.length > 0 ||
                  committed.liabilities_created.length > 0) && (
                  <ul className="mt-2 list-disc pl-5 text-xs opacity-90">
                    {[
                      ...committed.assets_created,
                      ...committed.liabilities_created,
                    ].map((n) => (
                      <li key={n}>{n}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {preview && (
              <div className="p-4 rounded-md border border-slate-200 dark:border-slate-800 text-sm space-y-1">
                <div className="font-medium text-slate-700 dark:text-slate-200">
                  Dry run
                </div>
                <div className="text-slate-600 dark:text-slate-300">
                  Would import <b>{preview.would_import}</b> transaction
                  {preview.would_import === 1 ? "" : "s"} and autocreate{" "}
                  <b>{preview.assets_would_create.length}</b> asset
                  {preview.assets_would_create.length === 1 ? "" : "s"} +{" "}
                  <b>{preview.liabilities_would_create.length}</b> liabilit
                  {preview.liabilities_would_create.length === 1 ? "y" : "ies"}.
                </div>
              </div>
            )}

            {reports.length > 0 && (
              <div className="space-y-3">
                {reports.map((f) => (
                  <FileRow key={f.filename} f={f} />
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </PageLayout>
  );
}

function FileRow({ f }: { f: MonarchFileReport }) {
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
          Header mismatch - this doesn&rsquo;t look like a Monarch export.
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

function safeDetail(text: string, fallback: string): string {
  try {
    const j = JSON.parse(text);
    if (typeof j?.detail === "string") return j.detail;
  } catch {
    // not JSON
  }
  return text || fallback;
}
