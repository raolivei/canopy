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
} from "recharts";
import { formatCurrencyCompact, formatCurrency } from "@/utils/currency";
import {
  CHART_PALETTE,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

export interface IncomeExpenseTrendData {
  month: number;
  month_name: string;
  income: number;
  expenses: number;
  investments: number;
  net: number;
}

interface IncomeExpenseTrendProps {
  data: IncomeExpenseTrendData[];
  currency?: string;
}

/**
 * IncomeExpenseTrend
 *
 * Bar chart showing monthly income vs spending vs investments.
 * Used in dashboards and reports to visualize cash flow patterns.
 */
export function IncomeExpenseTrend({
  data,
  currency = "CAD",
}: IncomeExpenseTrendProps) {
  const dark = checkDarkMode();

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barGap={2}>
          <CartesianGrid {...getGridProps(dark)} />
          <XAxis dataKey="month_name" {...getAxisProps(dark)} />
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
            dataKey="income"
            name="Income"
            fill={CHART_PALETTE[1]}
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="expenses"
            name="Spending"
            fill={CHART_PALETTE[4]}
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="investments"
            name="Invested"
            fill={CHART_PALETTE[2]}
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
