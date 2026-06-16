import React from "react";
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency, formatCurrencyCompact } from "@/utils/currency";
import {
  CHART_PALETTE,
  CHART_COLORS,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

export interface CashflowSummaryData {
  date: string;
  income: number;
  expenses: number;
  net: number;
  cumulative: number;
}

interface CashflowSummaryProps {
  data: CashflowSummaryData[];
  currency?: string;
}

/**
 * CashflowSummary
 *
 * Composed chart showing income (area), expenses (area), net (line), and cumulative savings.
 * Useful for visualizing cashflow trends over time.
 */
export function CashflowSummary({
  data,
  currency = "CAD",
}: CashflowSummaryProps) {
  const dark = checkDarkMode();

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
        >
          <CartesianGrid {...getGridProps(dark)} />
          <XAxis dataKey="date" {...getAxisProps(dark)} />
          <YAxis
            yAxisId="left"
            {...getAxisProps(dark)}
            tickFormatter={(v) => formatCurrencyCompact(v, currency)}
            width={56}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            {...getAxisProps(dark)}
            tickFormatter={(v) => formatCurrencyCompact(v, currency)}
            width={56}
          />
          <Tooltip
            contentStyle={getTooltipStyle(dark)}
            formatter={(v: number, name: string) => [
              formatCurrency(v, currency),
              name,
            ]}
          />
          <Legend />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="income"
            name="Income"
            stackId="cashflow"
            stroke={CHART_PALETTE[1]}
            fill={CHART_PALETTE[1]}
            fillOpacity={0.55}
          />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="expenses"
            name="Expenses"
            stackId="cashflow"
            stroke={CHART_PALETTE[4]}
            fill={CHART_PALETTE[4]}
            fillOpacity={0.5}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="net"
            name="Net"
            stroke={CHART_COLORS.accent}
            strokeWidth={2.5}
            dot={{ r: 3 }}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="cumulative"
            name="Cumulative"
            stroke={CHART_COLORS.primary}
            strokeWidth={2}
            dot={false}
            strokeDasharray="5 5"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
