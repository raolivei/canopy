import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import {
  CHART_COLORS,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
  chartHeight,
  chartMargin,
} from "@/utils/chartTheme";
import { formatCurrency } from "@/utils/currency";

interface MonthlyData {
  month: string;
  income: number;
  expenses: number;
  savings: number;
  savings_rate: number;
  categories: Array<{ category: string; amount: number }>;
}

interface IncomeExpenseTrendProps {
  data: MonthlyData[];
  isLoading?: boolean;
  currency?: string;
}

export default function IncomeExpenseTrend({
  data,
  isLoading = false,
  currency = "CAD",
}: IncomeExpenseTrendProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Income vs Expenses Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse h-80 bg-slate-200 dark:bg-slate-700 rounded"></div>
        </CardContent>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Income vs Expenses Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-500 dark:text-slate-400 text-center py-16">
            No data to display
          </p>
        </CardContent>
      </Card>
    );
  }

  const isDark = checkDarkMode();

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div
          className="rounded-lg shadow-lg border p-3"
          style={getTooltipStyle(isDark)}
        >
          <p className="font-semibold text-sm mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {formatCurrency(entry.value, currency)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Income vs Expenses Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={chartHeight.lg}>
          <LineChart
            data={data}
            margin={chartMargin.spacious}
          >
            <CartesianGrid {...getGridProps(isDark)} />
            <XAxis
              dataKey="month"
              {...getAxisProps(isDark)}
            />
            <YAxis {...getAxisProps(isDark)} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{
                paddingTop: "20px",
                color: isDark ? "#e2e8f0" : "#475569",
              }}
            />
            <Line
              type="monotone"
              dataKey="income"
              stroke={CHART_COLORS.success}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Income"
            />
            <Line
              type="monotone"
              dataKey="expenses"
              stroke={CHART_COLORS.danger}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Expenses"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
