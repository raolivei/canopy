import { useState, useCallback } from "react";
import { useRouter } from "next/router";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  ArrowRight,
  Loader2,
  File,
} from "lucide-react";
import { format } from "date-fns";
import { formatCurrency } from "@/utils/currency";
import { motion } from "framer-motion";
import { cn } from "@/utils/cn";

interface TransactionPreview {
  row_number: number;
  description: string;
  amount: number;
  currency: string;
  type: string;
  category?: string;
  date: string;
  account?: string;
  is_duplicate: boolean;
  duplicate_reason?: string;
  has_error: boolean;
  error_message?: string;
  raw_data: Record<string, unknown>;
}

interface ImportPreview {
  import_id: string;
  filename: string;
  detected_format?: string;
  used_format: string;
  headers: string[];
  preview: {
    total_rows: number;
    valid_rows: number;
    duplicate_rows: number;
    error_rows: number;
    transactions: TransactionPreview[];
    date_range?: {
      start: string;
      end: string;
    };
  };
}

interface ImportResult {
  import_id: string;
  status: string;
  total_rows: number;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: Array<{ description: string; error: string }>;
  imported_transaction_ids: number[];
  duration_seconds: number;
}

const bankFormats = [
  { value: "monarch", label: "Monarch Money" },
  { value: "generic", label: "Generic CSV" },
  { value: "chase", label: "Chase" },
  { value: "bank_of_america", label: "Bank of America" },
  { value: "wells_fargo", label: "Wells Fargo" },
  { value: "capital_one", label: "Capital One" },
  { value: "amex", label: "American Express" },
  { value: "td_bank", label: "TD Bank" },
  { value: "rbc", label: "RBC" },
  { value: "nubank", label: "Nubank" },
];

const currencyOptions = [
  { value: "USD", label: "USD - US Dollar" },
  { value: "CAD", label: "CAD - Canadian Dollar" },
  { value: "BRL", label: "BRL - Brazilian Real" },
  { value: "EUR", label: "EUR - Euro" },
  { value: "GBP", label: "GBP - British Pound" },
];

export default function Import() {
  const router = useRouter();
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [selectedFormat, setSelectedFormat] = useState("monarch");
  const [defaultCurrency, setDefaultCurrency] = useState("CAD");
  const [skipDuplicates, setSkipDuplicates] = useState(true);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [selectedFormat, defaultCurrency, skipDuplicates]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      alert("Please upload a CSV file");
      return;
    }

    setUploading(true);
    setPreview(null);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("bank_format", selectedFormat);
      formData.append("default_currency", defaultCurrency);
      formData.append("skip_duplicates", skipDuplicates.toString());

      const res = await fetch("/v1/csv-import/preview", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to preview CSV");
      }

      const data = await res.json();
      setPreview(data);
    } catch (err) {
      console.error("Upload failed:", err);
      alert(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleImport = async () => {
    if (!preview) return;

    setImporting(true);

    try {
      const res = await fetch("/v1/csv-import/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          import_id: preview.import_id,
          skip_duplicates: skipDuplicates,
          skip_errors: true,
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Import failed");
      }

      const result = await res.json();
      setImportResult(result);
      setPreview(null);
    } catch (err) {
      console.error("Import failed:", err);
      alert(err instanceof Error ? err.message : "Failed to import transactions");
    } finally {
      setImporting(false);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "income":
        return "text-success-600 dark:text-success-400";
      case "expense":
        return "text-danger-600 dark:text-danger-400";
      case "transfer":
        return "text-primary-600 dark:text-primary-400";
      default:
        return "text-slate-600 dark:text-slate-400";
    }
  };

  return (
    <PageLayout title="Import Transactions" description="Import transactions from CSV files">
      <PageHeader
        title="Import Transactions"
        description="Import transactions from CSV files"
      />

      {!preview && !importResult && (
        <>
          {/* Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <Card>
              <CardHeader>
                <CardTitle>Import Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Select
                    label="Bank Format"
                    options={bankFormats}
                    value={selectedFormat}
                    onChange={setSelectedFormat}
                  />
                  <Select
                    label="Default Currency"
                    options={currencyOptions}
                    value={defaultCurrency}
                    onChange={setDefaultCurrency}
                  />
                  <div className="flex items-end">
                    <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                      <div
                        className={cn(
                          "relative w-11 h-6 rounded-full transition-colors",
                          skipDuplicates ? "bg-primary-600" : "bg-slate-200 dark:bg-slate-700"
                        )}
                      >
                        <span
                          className={cn(
                            "absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform",
                            skipDuplicates && "translate-x-5"
                          )}
                        />
                      </div>
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Skip Duplicates
                      </span>
                    </label>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Upload Area */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardContent className="p-0">
                <div
                  className={cn(
                    "p-12 text-center border-2 border-dashed rounded-lg transition-colors m-1",
                    dragActive
                      ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                      : "border-slate-200 dark:border-slate-700"
                  )}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {uploading ? (
                    <div className="flex flex-col items-center gap-4">
                      <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
                      <p className="text-slate-600 dark:text-slate-400">Processing CSV file...</p>
                    </div>
                  ) : (
                    <>
                      <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-full w-fit mx-auto mb-4">
                        <Upload className="w-10 h-10 text-slate-400" />
                      </div>
                      <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                        Drop your CSV file here
                      </h3>
                      <p className="text-slate-600 dark:text-slate-400 mb-6">
                        or click to browse your files
                      </p>
                      <label className="cursor-pointer">
                        <span className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-primary-600 text-white hover:bg-primary-700 shadow-sm hover:shadow transition-all duration-150 active:scale-[0.98]">
                          <FileText className="w-4 h-4" />
                          Choose CSV File
                        </span>
                        <input
                          type="file"
                          accept=".csv"
                          onChange={handleFileInput}
                          className="hidden"
                        />
                      </label>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-4">
                        Supports Monarch Money, Chase, Bank of America, and many other formats
                      </p>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}

      {/* Preview */}
      {preview && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Rows"
              value={preview.preview.total_rows}
              icon={FileText}
              iconColor="text-slate-400"
            />
            <StatCard
              label="Valid"
              value={preview.preview.valid_rows}
              valueColor="text-success-600 dark:text-success-400"
              icon={CheckCircle}
              iconColor="text-success-500"
            />
            <StatCard
              label="Duplicates"
              value={preview.preview.duplicate_rows}
              valueColor="text-warning-600 dark:text-warning-400"
              icon={AlertCircle}
              iconColor="text-warning-500"
            />
            <StatCard
              label="Errors"
              value={preview.preview.error_rows}
              valueColor="text-danger-600 dark:text-danger-400"
              icon={XCircle}
              iconColor="text-danger-500"
            />
          </div>

          {/* File Info */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                    <File className="w-6 h-6 text-slate-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">
                      {preview.filename}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400 mt-1">
                      <span>
                        Format: <strong className="text-slate-900 dark:text-white">{preview.used_format}</strong>
                      </span>
                      {preview.detected_format && preview.detected_format !== preview.used_format && (
                        <Badge variant="warning" size="sm">Detected: {preview.detected_format}</Badge>
                      )}
                      {preview.preview.date_range && (
                        <span>
                          {format(new Date(preview.preview.date_range.start), "MMM dd, yyyy")} —{" "}
                          {format(new Date(preview.preview.date_range.end), "MMM dd, yyyy")}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button variant="secondary" onClick={() => setPreview(null)}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleImport}
                    loading={importing}
                    disabled={importing || preview.preview.valid_rows === 0}
                    leftIcon={<Download className="w-4 h-4" />}
                  >
                    Import {preview.preview.valid_rows} Transactions
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Transaction Preview */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Transaction Preview</CardTitle>
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Showing first 50 transactions
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[480px] overflow-y-auto">
                {preview.preview.transactions.slice(0, 50).map((tx) => (
                  <div
                    key={tx.row_number}
                    className={cn(
                      "p-4 transition-colors",
                      tx.has_error
                        ? "bg-danger-50 dark:bg-danger-900/20"
                        : tx.is_duplicate
                          ? "bg-warning-50 dark:bg-warning-900/20"
                          : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-slate-400 font-mono">#{tx.row_number + 1}</span>
                          <h4 className="font-medium text-slate-900 dark:text-white truncate">
                            {tx.description}
                          </h4>
                          {tx.category && (
                            <Badge variant="secondary" size="sm">{tx.category}</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-slate-500 dark:text-slate-400">
                          <span>{format(new Date(tx.date), "MMM dd, yyyy")}</span>
                          {tx.account && <span>{tx.account}</span>}
                          {tx.has_error && (
                            <span className="text-danger-600 dark:text-danger-400 flex items-center gap-1">
                              <XCircle className="w-3.5 h-3.5" />
                              {tx.error_message}
                            </span>
                          )}
                          {tx.is_duplicate && (
                            <span className="text-warning-600 dark:text-warning-400 flex items-center gap-1">
                              <AlertCircle className="w-3.5 h-3.5" />
                              Duplicate: {tx.duplicate_reason}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className={cn("text-right font-bold", getTypeColor(tx.type))}>
                        <div className="text-lg">
                          {tx.type === "expense" ? "-" : "+"}
                          {formatCurrency(Math.abs(tx.amount), tx.currency)}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                          {tx.type}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Import Result */}
      {importResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <Card>
            <CardContent className="p-12 text-center">
              {importResult.status === "completed" ? (
                <div className="p-4 bg-success-100 dark:bg-success-900/30 rounded-full w-fit mx-auto mb-4">
                  <CheckCircle className="w-12 h-12 text-success-600 dark:text-success-400" />
                </div>
              ) : importResult.status === "partially_completed" ? (
                <div className="p-4 bg-warning-100 dark:bg-warning-900/30 rounded-full w-fit mx-auto mb-4">
                  <AlertCircle className="w-12 h-12 text-warning-600 dark:text-warning-400" />
                </div>
              ) : (
                <div className="p-4 bg-danger-100 dark:bg-danger-900/30 rounded-full w-fit mx-auto mb-4">
                  <XCircle className="w-12 h-12 text-danger-600 dark:text-danger-400" />
                </div>
              )}
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Import{" "}
                {importResult.status === "completed"
                  ? "Complete"
                  : importResult.status === "partially_completed"
                    ? "Partially Complete"
                    : "Failed"}
              </h2>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                Imported {importResult.imported_count} of {importResult.total_rows} transactions
                {importResult.skipped_count > 0 && ` (${importResult.skipped_count} duplicates skipped)`}
              </p>
              <div className="flex justify-center gap-4">
                <Button
                  variant="primary"
                  onClick={() => router.push("/transactions")}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  View Transactions
                </Button>
                <Button variant="secondary" onClick={() => setImportResult(null)}>
                  Import Another File
                </Button>
              </div>
            </CardContent>
          </Card>

          {importResult.errors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-danger-600 dark:text-danger-400">
                  Errors ({importResult.errors.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="max-h-64 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
                  {importResult.errors.map((error, idx) => (
                    <div key={idx} className="p-4 bg-danger-50 dark:bg-danger-900/20">
                      <p className="font-medium text-slate-900 dark:text-white">{error.description}</p>
                      <p className="text-sm text-danger-600 dark:text-danger-400 mt-1">{error.error}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      )}
    </PageLayout>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  valueColor?: string;
  icon: React.ElementType;
  iconColor?: string;
}

function StatCard({ label, value, valueColor = "text-slate-900 dark:text-white", icon: Icon, iconColor = "text-slate-400" }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">{label}</p>
            <p className={cn("text-3xl font-bold", valueColor)}>{value}</p>
          </div>
          <Icon className={cn("w-8 h-8", iconColor)} />
        </div>
      </CardContent>
    </Card>
  );
}
