import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { SkeletonMetricCard, SkeletonChart } from "@/components/ui/Skeleton";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import { formatCurrency, formatCurrencyCompact } from "@/utils/currency";
import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  PiggyBank,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Info,
} from "lucide-react";
import {
  CHART_PALETTE,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface AnnualReport {
  year: number;
  available_years: number[];
  summary: {
    real_income: number;
    real_expenses: number;
    investments: number;
    net_savings: number;
    savings_rate: number;
  };
  by_month: {
    month: number;
    month_name: string;
    income: number;
    expenses: number;
    investments: number;
    net: number;
  }[];
  by_category: { category: string; amount: number; pct: number }[];
  income_sources: { category: string; amount: number; pct: number }[];
  top_merchants: { description: string; category: string; total: number; count: number }[];
}

function MetricCard({
  title,
  value,
  subtitle,
  icon,
  iconBg,
  highlight,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  iconBg: string;
  highlight?: boolean;
}) {
  return (
    <Card variant={highlight ? "highlight" : "default"}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className={cn("p-2 rounded-lg", iconBg)}>{icon}</div>
        </div>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">{title}</p>
        <p className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{value}</p>
        {subtitle && <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

const RADIAN = Math.PI / 180;
function CustomPieLabel({
  cx, cy, midAngle, innerRadius, outerRadius, pct, category,
}: any) {
  if (pct < 4) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" className="text-xs font-semibold" style={{ fontSize: 11, fontWeight: 600 }}>
      {`${pct.toFixed(0)}%`}
    </text>
  );
}

export default function AnnualReport() {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const currency = "CAD";
  const dark = checkDarkMode();

  const { data, isLoading } = useQuery<AnnualReport>({
    queryKey: ["annual-report", selectedYear],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/transactions/annual-report?year=${selectedYear}`);
      if (!res.ok) throw new Error("Failed to load report");
      return res.json();
    },
  });

  const yearOptions = useMemo(
    () => (data?.available_years || [selectedYear]).map((y) => ({ value: String(y), label: String(y) })),
    [data, selectedYear]
  );

  if (isLoading || !data) {
    return (
      <PageLayout title="Annual Report">
        <PageHeader title="Annual Report" description="Real income, spending, and investments by year" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => <SkeletonMetricCard key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonChart />
          <SkeletonChart />
        </div>
      </PageLayout>
    );
  }

  const { summary, by_month, by_category, income_sources, top_merchants } = data;

  return (
    <PageLayout title="Annual Report" description={`${selectedYear} financial summary`}>
      <PageHeader
        title="Annual Report"
        description="Real income, spending & investments — transfers and internal movements excluded"
        actions={
          <Select
            options={yearOptions}
            value={String(selectedYear)}
            onChange={(v) => setSelectedYear(Number(v))}
            className="w-28"
          />
        }
      />

      {/* Disclaimer banner */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <div className="flex items-start gap-2 p-3 bg-primary-50 dark:bg-primary-950/30 border border-primary-200 dark:border-primary-800 rounded-lg text-sm text-primary-700 dark:text-primary-300">
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          <span>Transfers, credit card payments, and loan repayments between your own accounts are excluded. Investment purchases (Buy) are tracked separately.</span>
        </div>
      </motion.div>

      {/* Summary cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        <MetricCard
          title="Real Income"
          value={formatCurrency(summary.real_income, currency)}
          subtitle="Paychecks, dividends, other"
          icon={<TrendingUp className="w-5 h-5" />}
          iconBg="bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400"
        />
        <MetricCard
          title="Real Spending"
          value={formatCurrency(summary.real_expenses, currency)}
          subtitle="Day-to-day expenses"
          icon={<TrendingDown className="w-5 h-5" />}
          iconBg="bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400"
        />
        <MetricCard
          title="Invested"
          value={formatCurrency(summary.investments, currency)}
          subtitle="Stocks, ETFs, etc."
          icon={<Wallet className="w-5 h-5" />}
          iconBg="bg-accent-100 dark:bg-accent-900/30 text-accent-600 dark:text-accent-400"
        />
        <MetricCard
          title="Net Savings"
          value={formatCurrency(summary.net_savings, currency)}
          subtitle={`${summary.savings_rate}% savings rate`}
          icon={summary.net_savings >= 0 ? <PiggyBank className="w-5 h-5" /> : <ArrowDownRight className="w-5 h-5" />}
          iconBg={summary.net_savings >= 0
            ? "bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400"
            : "bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400"}
          highlight={summary.net_savings >= 0}
        />
      </motion.div>

      {/* Charts row: Monthly bar + Spending pie */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
        {/* Monthly bar chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="lg:col-span-3"
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Monthly Overview</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Income vs spending by month</p>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={by_month} barGap={2}>
                    <CartesianGrid {...getGridProps(dark)} />
                    <XAxis dataKey="month_name" {...getAxisProps(dark)} />
                    <YAxis {...getAxisProps(dark)} tickFormatter={(v) => formatCurrencyCompact(v, currency)} />
                    <Tooltip
                      contentStyle={getTooltipStyle(dark)}
                      formatter={(v: number, name: string) => [formatCurrency(v, currency), name.charAt(0).toUpperCase() + name.slice(1)]}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="income" name="Income" fill={CHART_PALETTE[1]} radius={[3, 3, 0, 0]} />
                    <Bar dataKey="expenses" name="Spending" fill={CHART_PALETTE[4]} radius={[3, 3, 0, 0]} />
                    <Bar dataKey="investments" name="Invested" fill={CHART_PALETTE[2]} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Spending pie ("pizza") */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Spending Breakdown</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Where your money went</p>
            </CardHeader>
            <CardContent>
              <div className="h-60">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={by_category}
                      dataKey="amount"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={95}
                      labelLine={false}
                      label={CustomPieLabel}
                    >
                      {by_category.map((_, i) => (
                        <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
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
              <div className="mt-2 space-y-1.5 max-h-40 overflow-y-auto">
                {by_category.map((cat, i) => (
                  <div key={cat.category} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: CHART_PALETTE[i % CHART_PALETTE.length] }} />
                      <span className="text-slate-600 dark:text-slate-400 truncate">{cat.category}</span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      <span className="font-medium text-slate-900 dark:text-white">{formatCurrencyCompact(cat.amount, currency)}</span>
                      <span className="text-slate-400 w-8 text-right">{cat.pct}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Income sources + Top Merchants */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Income pie */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Income Sources</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Where your money came from</p>
            </CardHeader>
            <CardContent>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={income_sources}
                      dataKey="amount"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={90}
                      labelLine={false}
                      label={CustomPieLabel}
                    >
                      {income_sources.map((_, i) => (
                        <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={getTooltipStyle(dark)}
                      formatter={(v: number) => [formatCurrency(v, currency)]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-2 space-y-1.5">
                {income_sources.map((src, i) => (
                  <div key={src.category} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: CHART_PALETTE[i % CHART_PALETTE.length] }} />
                      <span className="text-slate-600 dark:text-slate-400 truncate">{src.category || "Uncategorized"}</span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      <span className="font-medium text-slate-900 dark:text-white">{formatCurrencyCompact(src.amount, currency)}</span>
                      <span className="text-slate-400 w-8 text-right">{src.pct}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Top Merchants */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Top Merchants</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Highest spending destinations</p>
            </CardHeader>
            <CardContent noPadding>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {top_merchants.map((m, i) => (
                  <div key={i} className="flex items-center justify-between px-5 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="w-6 text-xs font-medium text-slate-400 shrink-0">#{i + 1}</span>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{m.description}</p>
                        {m.category && (
                          <Badge variant="default" size="sm" className="mt-0.5">{m.category}</Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                      <p className="text-sm font-semibold text-danger-600 dark:text-danger-400">
                        {formatCurrency(m.total, currency)}
                      </p>
                      <p className="text-xs text-slate-400">{m.count} txn{m.count !== 1 ? "s" : ""}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Monthly detail table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Monthly Detail</CardTitle>
          </CardHeader>
          <CardContent noPadding>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800">
                    <th className="text-left px-5 py-3 font-medium text-slate-500 dark:text-slate-400">Month</th>
                    <th className="text-right px-5 py-3 font-medium text-slate-500 dark:text-slate-400">Income</th>
                    <th className="text-right px-5 py-3 font-medium text-slate-500 dark:text-slate-400">Spending</th>
                    <th className="text-right px-5 py-3 font-medium text-slate-500 dark:text-slate-400">Invested</th>
                    <th className="text-right px-5 py-3 font-medium text-slate-500 dark:text-slate-400">Net</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {by_month.filter((m) => m.income > 0 || m.expenses > 0 || m.investments > 0).map((m) => (
                    <tr key={m.month} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                      <td className="px-5 py-3 font-medium text-slate-900 dark:text-white">{m.month_name}</td>
                      <td className="px-5 py-3 text-right text-success-600 dark:text-success-400">
                        {m.income > 0 ? formatCurrency(m.income, currency) : "—"}
                      </td>
                      <td className="px-5 py-3 text-right text-danger-600 dark:text-danger-400">
                        {m.expenses > 0 ? formatCurrency(m.expenses, currency) : "—"}
                      </td>
                      <td className="px-5 py-3 text-right text-accent-600 dark:text-accent-400">
                        {m.investments > 0 ? formatCurrency(m.investments, currency) : "—"}
                      </td>
                      <td className={cn("px-5 py-3 text-right font-semibold",
                        m.net >= 0 ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400"
                      )}>
                        {m.net !== 0 ? (m.net >= 0 ? "+" : "") + formatCurrency(m.net, currency) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 font-semibold">
                    <td className="px-5 py-3 text-slate-900 dark:text-white">Total</td>
                    <td className="px-5 py-3 text-right text-success-600 dark:text-success-400">{formatCurrency(summary.real_income, currency)}</td>
                    <td className="px-5 py-3 text-right text-danger-600 dark:text-danger-400">{formatCurrency(summary.real_expenses, currency)}</td>
                    <td className="px-5 py-3 text-right text-accent-600 dark:text-accent-400">{formatCurrency(summary.investments, currency)}</td>
                    <td className={cn("px-5 py-3 text-right",
                      summary.net_savings >= 0 ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400"
                    )}>
                      {(summary.net_savings >= 0 ? "+" : "") + formatCurrency(summary.net_savings, currency)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </PageLayout>
  );
}
