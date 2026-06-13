import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
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

interface MonthlyData {
  month: string;
  income: number;
  expenses: number;
  savings: number;
  savings_rate: number;
  categories: Array<{ category: string; amount: number }>;
}

interface SavingsRateTrendProps {
  data: MonthlyData[];
  isLoading?: boolean;
}

export default function SavingsRateTrend({
  data,
  isLoading = false,
}: SavingsRateTrendProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Savings Rate Trend</CardTitle>
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
          <CardTitle>Savings Rate Trend</CardTitle>
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
              {entry.name}: {(entry.value as number).toFixed(1)}%
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
        <CardTitle>Savings Rate Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={chartHeight.lg}>
          <AreaChart
            data={data}
            margin={chartMargin.spacious}
          >
            <defs>
              <linearGradient id="colorSavingsRate" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={CHART_COLORS.primary}
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor={CHART_COLORS.primary}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid {...getGridProps(isDark)} />
            <XAxis
              dataKey="month"
              {...getAxisProps(isDark)}
            />
            <YAxis
              {...getAxisProps(isDark)}
              label={{ value: "Savings Rate (%)", angle: -90, position: "insideLeft" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="savings_rate"
              stroke={CHART_COLORS.primary}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorSavingsRate)"
              dot={{ r: 4, fill: CHART_COLORS.primary }}
              activeDot={{ r: 6 }}
              name="Savings Rate"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
