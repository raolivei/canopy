import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { formatCurrency, formatCurrencyCompact } from "@/utils/currency";
import {
  CHART_PALETTE,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

export interface BudgetVsActualsData {
  category: string;
  budget: number;
  actual: number;
  variance: number;
  variancePct: number;
}

interface BudgetVsActualsChartProps {
  data: BudgetVsActualsData[];
  currency?: string;
}

/**
 * BudgetVsActualsChart
 *
 * Grouped bar chart comparing budgeted vs actual spending by category.
 * Useful for monitoring whether spending aligns with budget targets.
 */
export function BudgetVsActualsChart({
  data,
  currency = "CAD",
}: BudgetVsActualsChartProps) {
  const dark = checkDarkMode();

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barGap={2}>
          <CartesianGrid {...getGridProps(dark)} />
          <XAxis dataKey="category" {...getAxisProps(dark)} />
          <YAxis
            {...getAxisProps(dark)}
            tickFormatter={(v) => formatCurrencyCompact(v, currency)}
          />
          <Tooltip
            contentStyle={getTooltipStyle(dark)}
            formatter={(v: number, name: string) => [
              formatCurrency(v, currency),
              name.charAt(0).toUpperCase() + name.slice(1),
            ]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar
            dataKey="budget"
            name="Budget"
            fill={CHART_PALETTE[0]}
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="actual"
            name="Actual"
            fill={CHART_PALETTE[1]}
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
