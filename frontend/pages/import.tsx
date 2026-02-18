import { useState, useCallback } from "react";
import Head from "next/head";
import Sidebar from "@/components/Sidebar";
import DarkModeToggle from "@/components/DarkModeToggle";
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  Clock,
  ArrowRight,
} from "lucide-react";
import { format } from "date-fns";
import { formatCurrency } from "@/utils/currency";

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
  raw_data: Record<string, any>;
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

export default function Import() {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [selectedFormat, setSelectedFormat] = useState("monarch");
  const [defaultCurrency, setDefaultCurrency] = useState("USD");
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

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

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
      alert(
        err instanceof Error ? err.message : "Failed to import transactions",
      );
    } finally {
      setImporting(false);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "income":
        return "text-green-600 dark:text-green-400";
      case "expense":
        return "text-red-600 dark:text-red-400";
      case "transfer":
        return "text-blue-600 dark:text-blue-400";
      default:
        return "text-gray-600 dark:text-gray-400";
    }
  };

  return (
    <>
      <Head>
        <title>Import Transactions - Canopy</title>
      </Head>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
        <Sidebar />
        <main className="flex-1 ml-64 p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                  Import Transactions
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  Import transactions from CSV files
                </p>
              </div>
              <DarkModeToggle />
            </div>

            {!preview && !importResult && (
              <>
                {/* Configuration */}
                <div className="card p-6 mb-6">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                    Import Settings
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Bank Format
                      </label>
                      <select
                        value={selectedFormat}
                        onChange={(e) => setSelectedFormat(e.target.value)}
                        className="input-modern"
                      >
                        <option value="monarch">Monarch Money</option>
                        <option value="generic">Generic CSV</option>
                        <option value="chase">Chase</option>
                        <option value="bank_of_america">Bank of America</option>
                        <option value="wells_fargo">Wells Fargo</option>
                        <option value="capital_one">Capital One</option>
                        <option value="amex">American Express</option>
                        <option value="td_bank">TD Bank</option>
                        <option value="rbc">RBC</option>
                        <option value="nubank">Nubank</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Default Currency
                      </label>
                      <select
                        value={defaultCurrency}
                        onChange={(e) => setDefaultCurrency(e.target.value)}
                        className="input-modern"
                      >
                        <option value="USD">USD - US Dollar</option>
                        <option value="CAD">CAD - Canadian Dollar</option>
                        <option value="BRL">BRL - Brazilian Real</option>
                        <option value="EUR">EUR - Euro</option>
                        <option value="GBP">GBP - British Pound</option>
                      </select>
                    </div>
                    <div className="flex items-end">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={skipDuplicates}
                          onChange={(e) => setSkipDuplicates(e.target.checked)}
                          className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Skip Duplicates
                        </span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Upload Area */}
                <div
                  className={`card p-12 text-center border-2 border-dashed transition-colors ${
                    dragActive
                      ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                      : "border-gray-300 dark:border-gray-600"
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {uploading ? (
                    <div className="flex flex-col items-center gap-4">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                      <p className="text-gray-600 dark:text-gray-400">
                        Processing CSV file...
                      </p>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                        Drop your CSV file here
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400 mb-6">
                        or click to browse your files
                      </p>
                      <label className="btn-primary cursor-pointer inline-flex items-center gap-2">
                        <FileText size={20} />
                        Choose CSV File
                        <input
                          type="file"
                          accept=".csv"
                          onChange={handleFileInput}
                          className="hidden"
                        />
                      </label>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
                        Supports Monarch Money, Chase, Bank of America, and many
                        other formats
                      </p>
                    </>
                  )}
                </div>
              </>
            )}

            {/* Preview */}
            {preview && (
              <div className="space-y-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="card p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                          Total Rows
                        </p>
                        <p className="text-3xl font-bold text-gray-900 dark:text-white">
                          {preview.preview.total_rows}
                        </p>
                      </div>
                      <FileText className="w-8 h-8 text-gray-400" />
                    </div>
                  </div>
                  <div className="card p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                          Valid
                        </p>
                        <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                          {preview.preview.valid_rows}
                        </p>
                      </div>
                      <CheckCircle className="w-8 h-8 text-green-500" />
                    </div>
                  </div>
                  <div className="card p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                          Duplicates
                        </p>
                        <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
                          {preview.preview.duplicate_rows}
                        </p>
                      </div>
                      <AlertCircle className="w-8 h-8 text-yellow-500" />
                    </div>
                  </div>
                  <div className="card p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                          Errors
                        </p>
                        <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                          {preview.preview.error_rows}
                        </p>
                      </div>
                      <XCircle className="w-8 h-8 text-red-500" />
                    </div>
                  </div>
                </div>

                {/* File Info */}
                <div className="card p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        {preview.filename}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <span>
                          Format:{" "}
                          <strong className="text-gray-900 dark:text-white">
                            {preview.used_format}
                          </strong>
                        </span>
                        {preview.detected_format &&
                          preview.detected_format !== preview.used_format && (
                            <span className="text-yellow-600 dark:text-yellow-400">
                              (Detected: {preview.detected_format})
                            </span>
                          )}
                        {preview.preview.date_range && (
                          <span>
                            Date Range:{" "}
                            <strong className="text-gray-900 dark:text-white">
                              {format(
                                new Date(preview.preview.date_range.start),
                                "MMM dd, yyyy",
                              )}{" "}
                              -{" "}
                              {format(
                                new Date(preview.preview.date_range.end),
                                "MMM dd, yyyy",
                              )}
                            </strong>
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => setPreview(null)}
                        className="btn-secondary"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleImport}
                        disabled={importing || preview.preview.valid_rows === 0}
                        className="btn-primary flex items-center gap-2"
                      >
                        {importing ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            Importing...
                          </>
                        ) : (
                          <>
                            <Download size={20} />
                            Import {preview.preview.valid_rows} Transactions
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Transaction Preview */}
                <div className="card">
                  <div className="p-6 border-b border-gray-100 dark:border-gray-700">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                      Transaction Preview
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Showing first 50 transactions
                    </p>
                  </div>
                  <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-96 overflow-y-auto">
                    {preview.preview.transactions.slice(0, 50).map((tx) => (
                      <div
                        key={tx.row_number}
                        className={`p-4 ${
                          tx.has_error
                            ? "bg-red-50 dark:bg-red-900/20"
                            : tx.is_duplicate
                              ? "bg-yellow-50 dark:bg-yellow-900/20"
                              : "hover:bg-gray-50 dark:hover:bg-gray-700/50"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                #{tx.row_number + 1}
                              </span>
                              <h4 className="font-semibold text-gray-900 dark:text-white">
                                {tx.description}
                              </h4>
                              {tx.category && (
                                <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                                  {tx.category}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
                              <span>
                                {format(new Date(tx.date), "MMM dd, yyyy")}
                              </span>
                              {tx.account && <span>{tx.account}</span>}
                              {tx.has_error && (
                                <span className="text-red-600 dark:text-red-400 flex items-center gap-1">
                                  <XCircle size={14} />
                                  {tx.error_message}
                                </span>
                              )}
                              {tx.is_duplicate && (
                                <span className="text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
                                  <AlertCircle size={14} />
                                  Duplicate: {tx.duplicate_reason}
                                </span>
                              )}
                            </div>
                          </div>
                          <div
                            className={`text-right font-bold ${getTypeColor(tx.type)}`}
                          >
                            <div className="text-lg">
                              {tx.type === "expense" ? "-" : "+"}
                              {formatCurrency(Math.abs(tx.amount), tx.currency)}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                              {tx.type}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Import Result */}
            {importResult && (
              <div className="space-y-6">
                <div className="card p-8 text-center">
                  {importResult.status === "completed" ? (
                    <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                  ) : importResult.status === "partially_completed" ? (
                    <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  ) : (
                    <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                  )}
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    Import{" "}
                    {importResult.status === "completed"
                      ? "Complete"
                      : importResult.status === "partially_completed"
                        ? "Partially Complete"
                        : "Failed"}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Imported {importResult.imported_count} of{" "}
                    {importResult.total_rows} transactions
                    {importResult.skipped_count > 0 &&
                      ` (${importResult.skipped_count} duplicates skipped)`}
                  </p>
                  <div className="flex justify-center gap-4">
                    <button
                      onClick={() => {
                        setImportResult(null);
                        window.location.href = "/transactions";
                      }}
                      className="btn-primary flex items-center gap-2"
                    >
                      View Transactions
                      <ArrowRight size={20} />
                    </button>
                    <button
                      onClick={() => setImportResult(null)}
                      className="btn-secondary"
                    >
                      Import Another File
                    </button>
                  </div>
                </div>

                {importResult.errors.length > 0 && (
                  <div className="card p-6">
                    <h3 className="text-lg font-bold text-red-600 dark:text-red-400 mb-4">
                      Errors ({importResult.errors.length})
                    </h3>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {importResult.errors.map((error, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-red-50 dark:bg-red-900/20 rounded text-sm"
                        >
                          <p className="font-semibold text-gray-900 dark:text-white">
                            {error.description}
                          </p>
                          <p className="text-red-600 dark:text-red-400">
                            {error.error}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
