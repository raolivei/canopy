import { useMemo, useState } from "react";
import { useRouter } from "next/router";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Upload, CheckCircle, AlertCircle, X, ArrowRight } from "lucide-react";
import Link from "next/link";

// Mirrors backend/services/wealthsimple/filename_parser.py::is_wealthsimple_filename.
// Keep in sync.
const WS_PREFIXES = [
  "Chequing-",
  "credit-card-statement-",
  "Portfolio line of credit-",
  "Direct Indexing-",
  "Crypto-",
  "FHSA-",
  "TFSA Long-",
  "TFSA-",
  "Retirement ",
  "Emerging ",
];

function looksLikeWealthsimple(filename: string): boolean {
  const base = filename.split("/").pop() ?? filename;
  const stem = base.toLowerCase().endsWith(".csv")
    ? base.slice(0, -4)
    : base;
  if (stem.includes("monthly-statement-transactions")) return true;
  if (stem.startsWith("credit-card-statement-transactions")) return true;
  return WS_PREFIXES.some((p) => stem.startsWith(p));
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface FileResult {
  filename: string;
  success: boolean;
  review_id?: number;
  as_of_date?: string;
  line_count?: number;
  total_value_cad?: string;
  error?: string;
}

interface BatchResponse {
  results: FileResult[];
  imported_count: number;
  failed_count: number;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function PortfolioImportPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [replace, setReplace] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<FileResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const summary = useMemo(() => {
    if (!results) return null;
    const ok = results.filter((r) => r.success).length;
    return { ok, failed: results.length - ok, total: results.length };
  }, [results]);

  const wsFileCount = useMemo(
    () => files.filter((f) => looksLikeWealthsimple(f.name)).length,
    [files]
  );
  const snapshotFiles = useMemo(
    () => files.filter((f) => !looksLikeWealthsimple(f.name)),
    [files]
  );

  const dropWealthsimpleFiles = () => {
    setFiles((prev) => prev.filter((f) => !looksLikeWealthsimple(f.name)));
  };

  const onSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(e.target.files ?? []);
    setFiles(picked);
    setResults(null);
    setError(null);
  };

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) {
      setError("Choose one or more CSV / tab-separated files.");
      return;
    }
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const fd = new FormData();
      for (const f of files) fd.append("files", f);
      const q = replace ? "?replace=true" : "";
      const res = await fetch(`${API_URL}/v1/portfolio-reviews/import/batch${q}`, {
        method: "POST",
        body: fd,
      });
      const text = await res.text();
      if (!res.ok) {
        try {
          const j = JSON.parse(text);
          setError(j.detail || text || res.statusText);
        } catch {
          setError(text || res.statusText);
        }
        return;
      }
      const data: BatchResponse = JSON.parse(text);
      setResults(data.results);
      if (data.imported_count > 0) {
        setFiles([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout title="Import snapshot">
      <PageHeader
        title="Import portfolio snapshot"
        description="Upload one or more Canadian holdings snapshots (CSV or tab-separated) for assets that don't auto-sync \u2014 e.g. private equity, real estate, DPSP. Brazil and crypto sections are ignored. For Wealthsimple monthly statements, use the Wealthsimple importer instead."
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Files</CardTitle>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Uses the dedicated portfolio review parser. One review per file, keyed
            by as-of date.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Spreadsheet exports
              </label>
              <input
                type="file"
                multiple
                accept=".csv,.txt,text/csv"
                onChange={onSelect}
                className="block w-full text-sm text-slate-600 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary-50 file:text-primary-700 dark:file:bg-primary-950 dark:file:text-primary-300"
              />
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
                You can select multiple files. Each is imported independently \u2014 one bad file won't cancel the rest.
              </p>
            </div>

            {wsFileCount > 0 && (
              <div className="rounded-md border border-amber-300 bg-amber-50 p-4 text-sm dark:border-amber-800/60 dark:bg-amber-950/40">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-amber-900 dark:text-amber-200">
                      {wsFileCount === 1
                        ? "This looks like a Wealthsimple monthly statement."
                        : `${wsFileCount} of these look like Wealthsimple monthly statements.`}
                    </div>
                    <p className="mt-1 text-amber-800 dark:text-amber-300/90">
                      {
                        "This page is for CAD portfolio snapshots (private equity, real estate, DPSP). Wealthsimple statements belong in the Wealthsimple importer, where they\u2019re auto-classified into investments, cash, and debt."
                      }
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        rightIcon={<ArrowRight className="w-4 h-4" />}
                        onClick={() =>
                          router.push("/portfolio/wealthsimple-import")
                        }
                      >
                        Go to Wealthsimple importer
                      </Button>
                      {snapshotFiles.length > 0 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={dropWealthsimpleFiles}
                        >
                          Drop Wealthsimple files, keep the {snapshotFiles.length}{" "}
                          snapshot file
                          {snapshotFiles.length === 1 ? "" : "s"}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {files.length > 0 && (
              <ul className="divide-y divide-slate-200 dark:divide-slate-800 rounded-md border border-slate-200 dark:border-slate-800">
                {files.map((f, i) => {
                  const isWs = looksLikeWealthsimple(f.name);
                  return (
                    <li
                      key={`${f.name}-${i}`}
                      className="flex items-center justify-between gap-3 px-3 py-2 text-sm"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-slate-700 dark:text-slate-200">
                            {f.name}
                          </span>
                          {isWs && (
                            <span className="shrink-0 rounded-full border border-amber-300 bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300">
                              Wealthsimple
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-500">
                          {formatSize(f.size)}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(i)}
                        className="shrink-0 rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                        aria-label={`Remove ${f.name}`}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}

            <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={replace}
                onChange={(e) => setReplace(e.target.checked)}
                className="rounded border-slate-300"
              />
              Replace existing reviews that share an as-of date
            </label>

            {error && (
              <div className="flex items-start gap-2 text-sm text-danger-600 dark:text-danger-400">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {summary && (
              <div className="rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm">
                <div className="font-medium text-slate-700 dark:text-slate-200">
                  {summary.ok} of {summary.total} imported
                  {summary.failed > 0 && (
                    <span className="text-danger-600 dark:text-danger-400">
                      {" "}\u00b7 {summary.failed} failed
                    </span>
                  )}
                </div>
                <ul className="mt-2 space-y-1">
                  {results?.map((r, i) => (
                    <li
                      key={`${r.filename}-${i}`}
                      className="flex items-start gap-2"
                    >
                      {r.success ? (
                        <CheckCircle className="w-4 h-4 shrink-0 mt-0.5 text-success-600 dark:text-success-400" />
                      ) : (
                        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-danger-600 dark:text-danger-400" />
                      )}
                      <div className="min-w-0">
                        <div className="truncate text-slate-700 dark:text-slate-200">
                          {r.filename}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-500">
                          {r.success
                            ? `Review ${r.review_id} \u00b7 ${r.as_of_date} \u00b7 ${r.line_count} lines`
                            : r.error}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex flex-wrap gap-3">
              <Button
                type="submit"
                variant="primary"
                disabled={loading || files.length === 0}
                leftIcon={<Upload className="w-4 h-4" />}
              >
                {loading
                  ? "Importing\u2026"
                  : files.length > 1
                    ? `Import ${files.length} files`
                    : "Import"}
              </Button>
              <Link href="/">
                <Button type="button" variant="ghost">
                  Back to dashboard
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </PageLayout>
  );
}
