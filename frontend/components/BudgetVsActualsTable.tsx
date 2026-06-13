import { useMoney } from "@/hooks/useMoney";
import { cn } from "@/utils/cn";
import { TrendingDown, TrendingUp } from "lucide-react";

interface BudgetCategoryRow {
  id: number;
  category_name: string;
  limit_amount: number;
  actual_spent: number;
  variance: number;
  variance_pct: number;
  percent_used: number;
  is_over_budget: boolean;
}

interface BudgetVsActualsTableProps {
  data: BudgetCategoryRow[];
  totalBudget: number;
  totalActual: number;
  totalVariance: number;
  currency?: string;
}

export default function BudgetVsActualsTable({
  data,
  totalBudget,
  totalActual,
  totalVariance,
  currency = "CAD",
}: BudgetVsActualsTableProps) {
  const { fmt } = useMoney();

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 dark:text-slate-400">
        No budget categories configured
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-slate-100/60 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700">
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">
              Category
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">
              Budget
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">
              Spent
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">
              Variance
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">
              Usage
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={`${row.id}-${idx}`}
              className={cn(
                "border-b border-slate-100 dark:border-slate-800 transition-colors",
                row.is_over_budget
                  ? "bg-danger-50/50 dark:bg-danger-950/20 hover:bg-danger-100/50 dark:hover:bg-danger-900/30"
                  : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
              )}
            >
              <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                {row.category_name}
              </td>
              <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">
                {fmt(row.limit_amount, currency)}
              </td>
              <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">
                {fmt(row.actual_spent, currency)}
              </td>
              <td
                className={cn(
                  "px-4 py-3 text-right font-semibold",
                  row.is_over_budget
                    ? "text-danger-700 dark:text-danger-400"
                    : "text-success-700 dark:text-success-400"
                )}
              >
                <div className="flex items-center justify-end gap-1">
                  {row.is_over_budget ? (
                    <TrendingDown className="w-3 h-3" />
                  ) : (
                    <TrendingUp className="w-3 h-3" />
                  )}
                  <span>
                    {row.is_over_budget ? "-" : ""}
                    {fmt(Math.abs(row.variance), currency)}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col items-end gap-1">
                  <span
                    className={cn(
                      "text-sm font-medium",
                      row.is_over_budget
                        ? "text-danger-700 dark:text-danger-400"
                        : row.percent_used >= 80
                          ? "text-warning-700 dark:text-warning-400"
                          : "text-slate-700 dark:text-slate-300"
                    )}
                  >
                    {row.percent_used.toFixed(0)}%
                  </span>
                  <div
                    className={cn(
                      "w-24 h-2 rounded-full overflow-hidden",
                      row.is_over_budget
                        ? "bg-danger-100 dark:bg-danger-900/30"
                        : row.percent_used >= 80
                          ? "bg-warning-100 dark:bg-warning-900/30"
                          : "bg-success-100 dark:bg-success-900/30"
                    )}
                  >
                    <div
                      className={cn(
                        "h-full transition-all",
                        row.is_over_budget
                          ? "bg-danger-500"
                          : row.percent_used >= 80
                            ? "bg-warning-500"
                            : "bg-success-500"
                      )}
                      style={{
                        width: `${Math.min(row.percent_used, 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </td>
            </tr>
          ))}
          {/* Total Row */}
          <tr className="bg-slate-100/80 dark:bg-slate-800/80 border-t-2 border-slate-300 dark:border-slate-600">
            <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">
              Total
            </td>
            <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
              {fmt(totalBudget, currency)}
            </td>
            <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
              {fmt(totalActual, currency)}
            </td>
            <td
              className={cn(
                "px-4 py-3 text-right font-bold",
                totalVariance < 0
                  ? "text-danger-700 dark:text-danger-400"
                  : "text-success-700 dark:text-success-400"
              )}
            >
              {totalVariance < 0 ? "-" : ""}
              {fmt(Math.abs(totalVariance), currency)}
            </td>
            <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
              {totalBudget > 0
                ? ((totalActual / totalBudget) * 100).toFixed(0)
                : "0"}
              %
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
