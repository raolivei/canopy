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
  FileText,
  Eye,
  Trash2,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

type FileClassification = {
  filename: string;
  account_label: string;
  account_kind: string;
  account_class: string;
  account_number: string | null;
  statement_period_start: string | null;
  shape: string;
  skipped: boolean;
  skip_reason: string | null;
  rows_seen: number;
  rows_imported: number;
  rows_duplicate: number;
  rows_unknown: number;
  by_kind: Record<string, number>;
  warnings: string[];
};

type PreviewResponse = {
  files: FileClassification[];
  total_rows_seen: number;
  total_would_import: number;
  total_duplicates: number;
};

type CommitResponse = PreviewResponse & {
  assets_touched: string[];
  liabilities_touched: string[];
  transactions_added: number;
  lots_added: number;
  dividends_added: number;
  account_snapshots_added: number;
  liability_snapshots_added: number;
  duplicates_skipped: number;
};

const ACCOUNT_CLASS_STYLE: Record<string, string> = {
  investment:
    "bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-300",
  cash: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  debt: "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  skip: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
};

export default function WealthsimpleImportPage() {
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

  const runPreview = async () => {
    if (files.length === 0) {
      setError("Choose one or more Wealthsimple CSV files.");
      return;
    }
    setLoading(true);
    setError(null);
    setCommitted(null);
    try {
      const res = await fetch(`${API_URL}/v1/wealthsimple-import/preview`, {
        method: "POST",
        body: formData(),
      });
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
      const res = await fetch(`${API_URL}/v1/wealthsimple-import/commit`, {
        method: "POST",
        body: formData(),
      });
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

  return (
    <PageLayout title="Wealthsimple import">
      <PageHeader
        title="Wealthsimple CSV drop zone"
        description="Drop a month of Wealthsimple statement CSVs and let Canopy classify, deduplicate, and route them into investments, cash, and debt."
      />

      <Card className="max-w-4xl">
        <CardHeader>
          <CardTitle>Files</CardTitle>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Accepts all account types. Direct Indexing files are skipped.
            Duplicates are detected automatically.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <label className="block">
              <span className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Wealthsimple CSVs (multi-select)
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
                {loading && !committed ? "Previewing…" : "Preview"}
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={runCommit}
                disabled={loading || files.length === 0}
                leftIcon={<Upload className="w-4 h-4" />}
              >
                {loading && preview ? "Importing…" : "Import"}
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
                  {committed.transactions_added} transactions,{" "}
                  {committed.lots_added} lots, {committed.dividends_added}{" "}
                  dividends,{" "}
                  {committed.account_snapshots_added +
                    committed.liability_snapshots_added}{" "}
                  balance snapshots. {committed.duplicates_skipped} duplicates
                  skipped.
                </div>
              </div>
            )}

            {preview && (
              <SummaryCounts
                label="Preview"
                totalSeen={preview.total_rows_seen}
                totalImport={preview.total_would_import}
                totalDup={preview.total_duplicates}
              />
            )}

            {(preview || committed) && (
              <div className="space-y-3">
                {(preview?.files ?? committed?.files ?? []).map((f) => (
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

function SummaryCounts({
  label,
  totalSeen,
  totalImport,
  totalDup,
}: {
  label: string;
  totalSeen: number;
  totalImport: number;
  totalDup: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-3 text-sm">
      <StatTile label={`${label} rows seen`} value={totalSeen.toLocaleString()} />
      <StatTile
        label={`${label} would import`}
        value={totalImport.toLocaleString()}
      />
      <StatTile
        label={`${label} duplicates`}
        value={totalDup.toLocaleString()}
      />
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 dark:border-slate-700 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <div className="text-lg font-semibold text-slate-900 dark:text-slate-100 mt-1">
        {value}
      </div>
    </div>
  );
}

function FileRow({ f }: { f: FileClassification }) {
  const badgeClass =
    ACCOUNT_CLASS_STYLE[f.account_class] ?? ACCOUNT_CLASS_STYLE.skip;
  return (
    <div
      className={`border rounded-md p-4 text-sm ${
        f.skipped
          ? "border-slate-200 dark:border-slate-800 opacity-70"
          : "border-slate-300 dark:border-slate-700"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <FileText className="w-4 h-4 text-slate-500" />
        <span className="font-medium text-slate-900 dark:text-slate-100">
          {f.filename}
        </span>
        <span className={`px-2 py-0.5 rounded text-xs ${badgeClass}`}>
          {f.account_class}
        </span>
        <span className="text-xs text-slate-500">{f.account_kind}</span>
        {f.account_number && (
          <span className="text-xs text-slate-400">{f.account_number}</span>
        )}
      </div>
      {f.skipped && f.skip_reason && (
        <div className="mt-2 text-slate-500">Skipped: {f.skip_reason}</div>
      )}
      {!f.skipped && (
        <div className="mt-2 grid grid-cols-4 gap-3 text-xs">
          <div>
            <div className="text-slate-500">Rows seen</div>
            <div className="font-medium">{f.rows_seen}</div>
          </div>
          <div>
            <div className="text-slate-500">Would import</div>
            <div className="font-medium">{f.rows_imported}</div>
          </div>
          <div>
            <div className="text-slate-500">Duplicates</div>
            <div className="font-medium">{f.rows_duplicate}</div>
          </div>
          <div>
            <div className="text-slate-500">Unknown codes</div>
            <div className="font-medium">{f.rows_unknown}</div>
          </div>
        </div>
      )}
      {Object.keys(f.by_kind).length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(f.by_kind).map(([k, v]) => (
            <span
              key={k}
              className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
            >
              {k}: {v}
            </span>
          ))}
        </div>
      )}
      {f.warnings.length > 0 && (
        <ul className="mt-3 text-xs text-amber-600 dark:text-amber-400 list-disc pl-5">
          {f.warnings.slice(0, 5).map((w, i) => (
            <li key={i}>{w}</li>
          ))}
          {f.warnings.length > 5 && (
            <li>…and {f.warnings.length - 5} more</li>
          )}
        </ul>
      )}
    </div>
  );
}

function safeDetail(text: string, fallback: string): string {
  try {
    const j = JSON.parse(text);
    return j.detail || text || fallback;
  } catch {
    return text || fallback;
  }
}
