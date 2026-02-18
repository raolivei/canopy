import React, { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { cn } from "@/utils/cn";
import {
  CHART_COLORS,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

interface PerformancePoint {
  date: string;
  total_value: number;
  total_cost_basis: number;
  gain_loss: number;
  return_pct: number | null;
}

interface PerformanceChartProps {
  data: PerformancePoint[];
  currency?: string;
  onPeriodChange?: (period: string) => void;
}

const PERIODS = [
  { value: "7d", label: "7D" },
  { value: "30d", label: "1M" },
  { value: "90d", label: "3M" },
  { value: "1y", label: "1Y" },
  { value: "all", label: "All" },
];

function formatCurrency(value: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function PerformanceChart({ data, currency = "USD", onPeriodChange }: PerformanceChartProps) {
  const [selectedPeriod, setSelectedPeriod] = useState("30d");

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
    onPeriodChange?.(period);
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload;
      const isPositive = point.gain_loss >= 0;

      return (
        <div
          className="rounded-lg shadow-lg border p-3"
          style={getTooltipStyle(checkDarkMode())}
        >
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
            {new Date(point.date).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
          <p className="font-semibold text-slate-900 dark:text-white">
            {formatCurrency(point.total_value, currency)}
          </p>
          <p className={cn("text-sm", isPositive ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400")}>
            {isPositive ? "+" : ""}{formatCurrency(point.gain_loss, currency)}
            {point.return_pct !== null && ` (${point.return_pct.toFixed(2)}%)`}
          </p>
        </div>
      );
    }
    return null;
  };

  const PeriodSelector = () => (
    <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
      {PERIODS.map((period) => (
        <button
          key={period.value}
          onClick={() => handlePeriodChange(period.value)}
          className={cn(
            "px-3 py-1 text-sm font-medium rounded-md transition-colors",
            selectedPeriod === period.value
              ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
              : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
          )}
        >
          {period.label}
        </button>
      ))}
    </div>
  );

  if (data.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            Portfolio Performance
          </h3>
          <PeriodSelector />
        </div>
        <p className="text-slate-500 dark:text-slate-400 text-center py-12">
          Not enough data to display performance chart
        </p>
      </div>
    );
  }

  const latestValue = data[data.length - 1]?.total_value || 0;
  const latestGainLoss = data[data.length - 1]?.gain_loss || 0;
  const isPositive = latestGainLoss >= 0;
  const chartColor = isPositive ? CHART_COLORS.success : CHART_COLORS.danger;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            Portfolio Performance
          </h3>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {formatCurrency(latestValue, currency)}
            </span>
            <span className={cn("text-sm font-medium", isPositive ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400")}>
              {isPositive ? "+" : ""}{formatCurrency(latestGainLoss, currency)}
            </span>
          </div>
        </div>
        <PeriodSelector />
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...getGridProps(checkDarkMode())} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              {...getAxisProps(checkDarkMode())}
            />
            <YAxis
              tickFormatter={(value) => formatCurrency(value, currency)}
              {...getAxisProps(checkDarkMode())}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="total_value"
              stroke={chartColor}
              strokeWidth={2}
              fill="url(#colorValue)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
