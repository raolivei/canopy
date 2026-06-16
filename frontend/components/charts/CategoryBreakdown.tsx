import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency, formatCurrencyCompact } from "@/utils/currency";
import {
  CHART_PALETTE,
  getTooltipStyle,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";
import { cn } from "@/utils/cn";

const RADIAN = Math.PI / 180;

export interface CategoryBreakdownData {
  category: string;
  amount: number;
  pct: number;
}

interface CategoryBreakdownProps {
  data: CategoryBreakdownData[];
  currency?: string;
  title?: string;
  showLegend?: boolean;
  maxLegendHeight?: string;
}

/**
 * Custom label renderer for pie chart.
 * Only shows percentage if slice is large enough (>4%).
 */
function CustomPieLabel({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  pct,
}: any) {
  if (pct < 4) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      className="text-xs font-semibold"
      style={{ fontSize: 11, fontWeight: 600 }}
    >
      {`${pct.toFixed(0)}%`}
    </text>
  );
}

/**
 * CategoryBreakdown
 *
 * Donut/pie chart showing spending or income breakdown by category.
 * Includes colored legend with amounts and percentages.
 */
export function CategoryBreakdown({
  data,
  currency = "CAD",
  title,
  showLegend = true,
  maxLegendHeight = "max-h-40",
}: CategoryBreakdownProps) {
  const dark = checkDarkMode();

  return (
    <>
      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="amount"
              nameKey="category"
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={95}
              labelLine={false}
              label={CustomPieLabel}
            >
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={CHART_PALETTE[i % CHART_PALETTE.length]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={getTooltipStyle(dark)}
              formatter={(v: number) => [formatCurrency(v, currency)]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      {showLegend && (
        <div
          className={cn(
            "mt-2 space-y-1.5 overflow-y-auto",
            maxLegendHeight
          )}
        >
          {data.map((cat, i) => (
            <div
              key={cat.category}
              className="flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{
                    backgroundColor:
                      CHART_PALETTE[i % CHART_PALETTE.length],
                  }}
                />
                <span className="text-slate-600 dark:text-slate-400 truncate">
                  {cat.category}
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                <span className="font-medium text-slate-900 dark:text-white">
                  {formatCurrencyCompact(cat.amount, currency)}
                </span>
                <span className="text-slate-400 w-8 text-right">
                  {cat.pct}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
