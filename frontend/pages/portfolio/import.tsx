import { useState } from "react";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Upload, CheckCircle, AlertCircle } from "lucide-react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export default function PortfolioImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [replace, setReplace] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Choose a CSV or tab-separated file.");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const q = replace ? "?replace=true" : "";
      const res = await fetch(`${API_URL}/v1/portfolio-reviews/import${q}`, {
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
      const data = JSON.parse(text);
      setMessage(
        `Imported review as of ${data.as_of_date} with ${data.lines?.length ?? 0} lines.`
      );
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
        description="Upload a Canadian holdings snapshot (CSV or tab-separated) for assets that don't auto-sync — e.g. private equity, real estate, DPSP. Brazil and crypto sections are ignored."
      />

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>File</CardTitle>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Uses the dedicated portfolio review parser (not bank transaction CSV).
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Spreadsheet export
              </label>
              <input
                type="file"
                accept=".csv,.txt,text/csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm text-slate-600 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary-50 file:text-primary-700 dark:file:bg-primary-950 dark:file:text-primary-300"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={replace}
                onChange={(e) => setReplace(e.target.checked)}
                className="rounded border-slate-300"
              />
              Replace existing review with the same as-of date
            </label>
            {error && (
              <div className="flex items-start gap-2 text-sm text-danger-600 dark:text-danger-400">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
            {message && (
              <div className="flex items-start gap-2 text-sm text-success-600 dark:text-success-400">
                <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{message}</span>
              </div>
            )}
            <div className="flex flex-wrap gap-3">
              <Button type="submit" variant="primary" disabled={loading} leftIcon={<Upload className="w-4 h-4" />}>
                {loading ? "Importing…" : "Import"}
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
