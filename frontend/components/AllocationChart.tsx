import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import {
  ALLOCATION_PALETTE,
  getTooltipStyle,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

interface AllocationItem {
  asset_type: string;
  value: number;
  percentage: number;
  count: number;
}

interface AllocationChartProps {
  data: AllocationItem[];
  totalValue: number;
  currency?: string;
}

const TYPE_LABELS: Record<string, string> = {
  stock: "Stocks",
  etf: "ETFs",
  crypto: "Crypto",
  bond: "Bonds",
  cash: "Cash",
  other: "Other",
};

function formatCurrency(value: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default function AllocationChart({
  data,
  totalValue,
  currency = "USD",
}: AllocationChartProps) {
  if (data.length === 0) {
    return (
      <div className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Asset Allocation
        </h3>
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">
          No data to display
        </p>
      </div>
    );
  }

  const chartData = data.map((item, index) => ({
    name: TYPE_LABELS[item.asset_type] || item.asset_type,
    value: Number(item.value),
    percentage: Number(item.percentage),
    count: item.count,
    color: ALLOCATION_PALETTE[index % ALLOCATION_PALETTE.length],
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const entry = payload[0].payload;
      return (
        <div
          className="rounded-lg shadow-lg border p-3"
          style={getTooltipStyle(checkDarkMode())}
        >
          <p className="font-medium text-slate-900 dark:text-white">
            {entry.name}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {formatCurrency(entry.value, currency)} (
            {Number(entry.percentage).toFixed(1)}%)
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {entry.count} {entry.count === 1 ? "holding" : "holdings"}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value, entry: any) => (
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {value} ({Number(entry.payload.percentage).toFixed(1)}%)
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-center">
        <p className="text-sm text-slate-500 dark:text-slate-400">Total Value</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">
          {formatCurrency(totalValue, currency)}
        </p>
      </div>
    </div>
  );
}
