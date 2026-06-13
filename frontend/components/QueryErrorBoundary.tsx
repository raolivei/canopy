import React, { useState } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/utils/cn";

interface QueryErrorBoundaryProps {
  error: Error | null;
  isLoading?: boolean;
  onRetry: () => void;
  showCached?: boolean;
  cachedDataAge?: number;
  children?: React.ReactNode;
}

export default function QueryErrorBoundary({
  error,
  isLoading = false,
  onRetry,
  showCached = false,
  cachedDataAge,
  children,
}: QueryErrorBoundaryProps) {
  const [retryCount, setRetryCount] = useState(0);

  if (!error) {
    return children || null;
  }

  const isNetworkError = error.message.includes("Failed to fetch");
  const isServerError = error.message.includes("500") || error.message.includes("502");
  const retryDelay = Math.min(1000 * Math.pow(2, retryCount), 10000); // Exponential backoff

  const handleRetry = () => {
    setRetryCount((prev) => prev + 1);
    // Small delay to show intent (exponential backoff: 1s, 2s, 4s, max 10s)
    setTimeout(onRetry, retryCount > 0 ? retryDelay : 0);
  };

  const getErrorMessage = () => {
    if (isNetworkError) {
      return "Network error — check your connection and try again";
    }
    if (isServerError) {
      return "Server error — our team is looking into this. Try again in a moment.";
    }
    if (error.message.includes("404")) {
      return "Resource not found";
    }
    return error.message || "Failed to load data";
  };

  const getCachedLabel = () => {
    if (!cachedDataAge) return "[STALE]";
    const minutes = Math.floor(cachedDataAge / 60000);
    if (minutes < 1) return "[STALE - just now]";
    if (minutes === 1) return "[STALE - 1 min ago]";
    return `[STALE - ${minutes} min ago]`;
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Error Alert */}
      <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-red-900 dark:text-red-200 mb-1">
              Error Loading Data
            </h3>
            <p className="text-sm text-red-800 dark:text-red-300 mb-3">
              {getErrorMessage()}
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={handleRetry}
                disabled={isLoading}
                leftIcon={
                  <RotateCcw
                    className={cn(
                      "w-4 h-4",
                      isLoading && "animate-spin"
                    )}
                  />
                }
              >
                {isLoading ? "Retrying..." : "Try Again"}
              </Button>
              {retryCount > 0 && (
                <div className="flex items-center px-3 py-1 bg-red-100 dark:bg-red-900/50 rounded text-xs text-red-700 dark:text-red-300">
                  Attempt {retryCount + 1}
                  {retryCount > 2 && " (check connection)"}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Cached Data Notice */}
      {showCached && (
        <div className="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg">
          <p className="text-sm text-amber-800 dark:text-amber-200">
            <span className="font-semibold">{getCachedLabel()}</span> Showing last known data while we reconnect.
          </p>
        </div>
      )}

      {children}
    </div>
  );
}
