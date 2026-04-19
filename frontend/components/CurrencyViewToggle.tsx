/**
 * Questrade-style four-way currency view toggle.
 *
 * Placed on the dashboard, Accounts, and Holdings pages. Writes the
 * selection to localStorage via :mod:`useCurrencyView` so every page
 * stays in sync.
 *
 * Also surfaces the Bank of Canada USD/CAD rate in the trailing caption
 * and warns when the rate is stale (BoC unreachable or holiday gap
 * longer than ~3 days).
 */

import React from "react";
import { cn } from "@/utils/cn";
import {
  CurrencyView,
  useCurrencyView,
  viewLabel,
} from "@/hooks/useCurrencyView";
import { useFxRate } from "@/hooks/useFxRate";
import { AlertTriangle } from "lucide-react";
import { PrivacyModeToggle } from "@/components/PrivacyModeToggle";

const OPTIONS: { value: CurrencyView; label: string; description: string }[] = [
  { value: "CAD", label: "CAD", description: "Native CAD balances only" },
  { value: "USD", label: "USD", description: "Native USD balances only" },
  {
    value: "COMBINED_CAD",
    label: "Combined (CAD)",
    description: "All balances converted to CAD",
  },
  {
    value: "COMBINED_USD",
    label: "Combined (USD)",
    description: "All balances converted to USD",
  },
];

interface CurrencyViewToggleProps {
  className?: string;
  showFxCaption?: boolean;
}

export function CurrencyViewToggle({
  className,
  showFxCaption = true,
}: CurrencyViewToggleProps) {
  const { view, setView, hydrated } = useCurrencyView();
  const fx = useFxRate();

  return (
    <div className={cn("flex flex-col items-start gap-1.5", className)}>
      <div className="flex flex-wrap items-center gap-2">
      <div
        role="group"
        aria-label="Currency view"
        className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-0.5 shadow-sm"
      >
        {OPTIONS.map((opt) => {
          const active = hydrated && view === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => setView(opt.value)}
              title={opt.description}
              aria-pressed={active}
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded-md transition-colors",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500",
                active
                  ? "bg-emerald-600 text-white shadow"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white",
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
      <PrivacyModeToggle showLabel />
      </div>
      {showFxCaption && (
        <FxCaption
          rate={fx.data?.rate ?? null}
          asOfDate={fx.data?.as_of_date ?? null}
          isStale={fx.data?.is_stale ?? true}
          isLoading={fx.isLoading}
          error={fx.error as Error | null}
          view={view}
        />
      )}
    </div>
  );
}

function FxCaption({
  rate,
  asOfDate,
  isStale,
  isLoading,
  error,
  view,
}: {
  rate: number | null;
  asOfDate: string | null;
  isStale: boolean;
  isLoading: boolean;
  error: Error | null;
  view: CurrencyView;
}) {
  // The FX rate only affects combined views; for single-currency views
  // the caption is informational. We still show it so the user always
  // knows what the current BoC rate is.
  const viewDescription = viewLabel(view);
  if (isLoading && rate == null) {
    return (
      <p className="text-[11px] text-slate-400 dark:text-slate-500">
        Loading FX… · Showing {viewDescription}
      </p>
    );
  }
  if (rate == null || error) {
    return (
      <p className="flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400">
        <AlertTriangle className="w-3 h-3" />
        FX unavailable — combined views fall back to native balances.
      </p>
    );
  }
  return (
    <p
      className={cn(
        "text-[11px]",
        isStale
          ? "text-amber-600 dark:text-amber-400"
          : "text-slate-400 dark:text-slate-500",
      )}
    >
      {isStale && <AlertTriangle className="inline w-3 h-3 -mt-0.5 mr-1" />}
      USD/CAD {rate.toFixed(4)}
      {asOfDate && <> · as of {asOfDate}</>}
      {" · "}Showing {viewDescription}
    </p>
  );
}

export default CurrencyViewToggle;
