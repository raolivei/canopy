import { cn } from "@/utils/cn";
import { PERIOD_CONFIGS, PeriodConfig, TimePeriod } from "@/utils/dateFiltering";

interface PeriodSelectorProps {
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
  periods?: PeriodConfig[];
  className?: string;
}

/**
 * Period selector button group for filtering time-series data.
 * Provides quick access to common time periods (5D, 1M, 3M, etc.)
 */
export function PeriodSelector({
  selectedPeriod,
  onPeriodChange,
  periods = PERIOD_CONFIGS,
  className,
}: PeriodSelectorProps) {
  return (
    <div
      className={cn(
        "flex gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg w-fit",
        className
      )}
      role="group"
      aria-label="Time period selector"
    >
      {periods.map((period) => (
        <button
          key={period.value}
          onClick={() => onPeriodChange(period.value)}
          className={cn(
            "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
            selectedPeriod === period.value
              ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          )}
          aria-pressed={selectedPeriod === period.value}
        >
          {period.label}
        </button>
      ))}
    </div>
  );
}
