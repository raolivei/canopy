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
import { useMoney } from "@/hooks/useMoney";
import {
  CHART_COLORS,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

interface ChartDataPoint {
  category_name: string;
  limit_amount: number;
  actual_spent: number;
}

interface BudgetVsActualsChartProps {
  data: ChartDataPoint[];
  currency?: string;
}

export default function BudgetVsActualsChart({
  data,
  currency = "CAD",
}: BudgetVsActualsChartProps) {
  const { fmt } = useMoney();
  const isDark = checkDarkMode();

  if (!data || data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center text-slate-500 dark:text-slate-400">
        No budget data available
      </div>
    );
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
          <CartesianGrid {...getGridProps(isDark)} />
          <XAxis
            dataKey="category_name"
            {...getAxisProps(isDark)}
            angle={-45}
            textAnchor="end"
            height={100}
          />
          <YAxis
            {...getAxisProps(isDark)}
            tickFormatter={(v) => fmt(v as number, currency)}
            width={56}
          />
          <Tooltip
            contentStyle={getTooltipStyle(isDark)}
            formatter={(v: number, name: string) => {
              const label = name === "limit_amount" ? "Budget" : "Actual";
              return [fmt(v, currency), label];
            }}
            labelFormatter={(label) => `${label}`}
          />
          <Legend />
          <Bar
            dataKey="limit_amount"
            name="Budget"
            fill={CHART_COLORS.primary}
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="actual_spent"
            name="Actual"
            fill={CHART_COLORS.success}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
