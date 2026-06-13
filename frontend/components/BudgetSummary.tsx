import { useMoney } from "@/hooks/useMoney";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import {
  TrendingDown,
  TrendingUp,
  Wallet,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface BudgetSummaryProps {
  totalBudget: number;
  totalActual: number;
  variance: number;
  percentUsed: number;
  isOverBudget: boolean;
  currency?: string;
}

export default function BudgetSummary({
  totalBudget,
  totalActual,
  variance,
  percentUsed,
  isOverBudget,
  currency = "CAD",
}: BudgetSummaryProps) {
  const { fmt } = useMoney();

  const progressBarColor = isOverBudget
    ? "bg-danger-500"
    : percentUsed >= 80
      ? "bg-warning-500"
      : "bg-success-500";

  const progressBarBgColor = isOverBudget
    ? "bg-danger-100 dark:bg-danger-900/30"
    : percentUsed >= 80
      ? "bg-warning-100 dark:bg-warning-900/30"
      : "bg-success-100 dark:bg-success-900/30";

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Total Budget */}
      <Card>
        <CardContent className="py-5">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2">
            <Wallet className="w-4 h-4" />
            <span>Total Budget</span>
          </div>
          <div className="text-2xl font-semibold text-slate-900 dark:text-white">
            {fmt(totalBudget, currency)}
          </div>
        </CardContent>
      </Card>

      {/* Total Actual */}
      <Card>
        <CardContent className="py-5">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2">
            <TrendingDown className="w-4 h-4" />
            <span>Spent</span>
          </div>
          <div className="text-2xl font-semibold text-slate-900 dark:text-white">
            {fmt(totalActual, currency)}
          </div>
        </CardContent>
      </Card>

      {/* Variance */}
      <Card>
        <CardContent className="py-5">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2">
            {isOverBudget ? (
              <AlertCircle className="w-4 h-4 text-danger-600 dark:text-danger-400" />
            ) : (
              <CheckCircle className="w-4 h-4 text-success-600 dark:text-success-400" />
            )}
            <span>Variance</span>
          </div>
          <div
            className={`text-2xl font-semibold ${
              isOverBudget
                ? "text-danger-700 dark:text-danger-400"
                : "text-success-700 dark:text-success-400"
            }`}
          >
            {isOverBudget ? "-" : ""}
            {fmt(Math.abs(variance), currency)}
          </div>
          {isOverBudget && (
            <p className="text-xs text-danger-600 dark:text-danger-400 mt-1">
              Over budget
            </p>
          )}
        </CardContent>
      </Card>

      {/* Percent Used */}
      <Card>
        <CardContent className="py-5">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2">
            <span>Usage</span>
          </div>
          <div className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">
            {percentUsed.toFixed(0)}%
          </div>
          <div className={`w-full h-2 rounded-full ${progressBarBgColor} overflow-hidden`}>
            <div
              className={`h-full ${progressBarColor} transition-all`}
              style={{ width: `${Math.min(percentUsed, 100)}%` }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
