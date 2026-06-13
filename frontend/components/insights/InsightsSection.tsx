import React from "react";
import { useContextualInsights } from "@/hooks/useContextualInsights";
import { Card, CardContent, CardHeader, CardTitle, InsightCard } from "@/components/ui";
import { SkeletonMetricCard } from "@/components/ui/Skeleton";
import { AlertCircle, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/utils/cn";
import { formatCurrency } from "@/utils/currency";

export function InsightsSection() {
  const { data: insights, isLoading, error } = useContextualInsights();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonMetricCard key={i} />
        ))}
      </div>
    );
  }

  if (error || !insights) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Budget Warnings */}
      {insights.budget_warnings.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Budget Alerts
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {insights.budget_warnings.slice(0, 4).map((warning, idx) => (
              <InsightCard
                key={`budget-${idx}`}
                title={warning.category_name}
                type={
                  warning.type === "critical"
                    ? "warning"
                    : warning.type === "warning"
                      ? "info"
                      : "success"
                }
                metric={`${warning.percent_used.toFixed(0)}%`}
                metricLabel="of budget used"
                description={warning.message}
                subtext={`${formatCurrency(warning.actual_spent, "CAD")} / ${formatCurrency(warning.budget_limit, "CAD")}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Month-over-Month Comparisons */}
      {insights.mom_comparisons.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Month-over-Month Changes
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {insights.mom_comparisons.slice(0, 4).map((comp, idx) => (
              <InsightCard
                key={`mom-${idx}`}
                title={comp.category_name}
                type={
                  comp.change_percent > 5
                    ? "warning"
                    : comp.change_percent < -5
                      ? "success"
                      : "neutral"
                }
                metric={`${comp.change_percent >= 0 ? "+" : ""}${comp.change_percent.toFixed(1)}%`}
                metricLabel="vs previous month"
                description={comp.message}
                subtext={`This month: ${formatCurrency(comp.current_month_amount, "CAD")}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Transaction Anomalies */}
      {insights.anomalies.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Unusual Transactions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {insights.anomalies.slice(0, 4).map((anomaly, idx) => (
              <InsightCard
                key={`anomaly-${idx}`}
                title={anomaly.merchant}
                type="warning"
                metric={`${anomaly.deviation_percent.toFixed(0)}%`}
                metricLabel="above average"
                description={anomaly.message}
                subtext={`${anomaly.category} • ${formatCurrency(Math.abs(anomaly.amount), "CAD")}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Recurring Predictions */}
      {insights.recurring_predictions.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Predicted Recurring
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {insights.recurring_predictions.slice(0, 4).map((pred, idx) => (
              <InsightCard
                key={`pred-${idx}`}
                title={pred.merchant}
                type="info"
                metric={`${(pred.confidence * 100).toFixed(0)}%`}
                metricLabel="confidence"
                description={`Expected on ${new Date(pred.expected_date).toLocaleDateString()}`}
                subtext={`${pred.category} • ${formatCurrency(pred.expected_amount, "CAD")}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {insights.budget_warnings.length === 0 &&
        insights.mom_comparisons.length === 0 &&
        insights.anomalies.length === 0 &&
        insights.recurring_predictions.length === 0 && (
          <Card>
            <CardContent className="py-8 text-center text-slate-500 dark:text-slate-400">
              <p>No contextual insights yet. Add transactions to get started.</p>
            </CardContent>
          </Card>
        )}
    </div>
  );
}
