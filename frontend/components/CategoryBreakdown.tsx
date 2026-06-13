import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { formatCurrency } from "@/utils/currency";
import { CHART_PALETTE } from "@/utils/chartTheme";

interface CategoryItem {
  category: string;
  amount: number;
}

interface CategoryBreakdownProps {
  data: CategoryItem[];
  isLoading?: boolean;
  currency?: string;
  title?: string;
  limit?: number;
}

export default function CategoryBreakdown({
  data,
  isLoading = false,
  currency = "CAD",
  title = "Top Expense Categories",
  limit = 10,
}: CategoryBreakdownProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i}>
                <div className="animate-pulse h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/4 mb-2"></div>
                <div className="animate-pulse h-2 bg-slate-200 dark:bg-slate-700 rounded"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-500 dark:text-slate-400 text-center py-8">
            No data to display
          </p>
        </CardContent>
      </Card>
    );
  }

  const displayData = data.slice(0, limit);
  const total = displayData.reduce((sum, item) => sum + item.amount, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {displayData.map((item, index) => {
            const percentage = (item.amount / total) * 100;
            const color = CHART_PALETTE[index % CHART_PALETTE.length];

            return (
              <div key={item.category}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    ></div>
                    <span className="text-sm font-medium text-slate-900 dark:text-white">
                      {item.category}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      {formatCurrency(item.amount, currency)}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {percentage.toFixed(1)}%
                    </p>
                  </div>
                </div>
                <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: color,
                      opacity: 0.8,
                    }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>

        {data.length > limit && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
            Showing top {limit} of {data.length} categories
          </p>
        )}
      </CardContent>
    </Card>
  );
}
