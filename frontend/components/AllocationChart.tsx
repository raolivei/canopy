import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

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

const COLORS = [
  "#3b82f6", // blue - stocks
  "#10b981", // green - etf
  "#f59e0b", // amber - crypto
  "#8b5cf6", // purple - bonds
  "#6b7280", // gray - other
  "#ec4899", // pink
];

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

export default function AllocationChart({ data, totalValue, currency = "USD" }: AllocationChartProps) {
  if (data.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Asset Allocation
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
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
    color: COLORS[index % COLORS.length],
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-medium text-gray-900 dark:text-white">{data.name}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {formatCurrency(data.value, currency)} ({data.percentage.toFixed(1)}%)
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data.count} {data.count === 1 ? "holding" : "holdings"}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Asset Allocation
      </h3>
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
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {value} ({entry.payload.percentage.toFixed(1)}%)
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400">Total Value</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {formatCurrency(totalValue, currency)}
        </p>
      </div>
    </div>
  );
}
