import { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonMetricCard, SkeletonChart, SkeletonList } from "@/components/ui/Skeleton";
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  PiggyBank,
  CreditCard,
  Plus,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { format, subDays, startOfMonth, endOfMonth, subMonths } from "date-fns";
import { formatCurrency, formatCurrencyCompact } from "@/utils/currency";
import { cn } from "@/utils/cn";
import { motion } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface Transaction {
  id: number;
  description: string;
  amount: number;
  currency: string;
  type: "income" | "expense" | "transfer";
  category?: string;
  date: string;
}

interface PortfolioSummary {
  total_value: number | null;
  total_cost_basis: number | null;
  total_gain_loss: number | null;
  total_gain_loss_pct: number | null;
  holdings_count: number;
}

type TimeRange = "7d" | "30d" | "90d";

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [displayCurrency, setDisplayCurrency] = useState("CAD");
  const [timeRange, setTimeRange] = useState<TimeRange>("30d");

  useEffect(() => {
    Promise.all([fetchTransactions(), fetchPortfolio()]).finally(() =>
      setLoading(false)
    );
  }, []);

  const fetchTransactions = async () => {
    try {
      const res = await fetch(`${API_URL}/v1/transactions/?currency=${displayCurrency}`);
      const data = await res.json();
      setTransactions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch transactions:", err);
      setTransactions([]);
    }
  };

  const fetchPortfolio = async () => {
    try {
      const res = await fetch(`${API_URL}/v1/portfolio/summary?currency=${displayCurrency}`);
      const data = await res.json();
      setPortfolio(data);
    } catch (err) {
      console.error("Failed to fetch portfolio:", err);
    }
  };

  const now = useMemo(() => new Date(), []);
  const currentMonthStart = useMemo(() => startOfMonth(now), [now]);
  const lastMonthStart = useMemo(() => startOfMonth(subMonths(now, 1)), [now]);
  const lastMonthEnd = useMemo(() => endOfMonth(subMonths(now, 1)), [now]);

  const { currentMonthIncome, currentMonthExpenses, lastMonthIncome, lastMonthExpenses } =
    useMemo(() => {
      const currentMonth = transactions.filter(
        (t) => new Date(t.date) >= currentMonthStart
      );
      const lastMonth = transactions.filter((t) => {
        const d = new Date(t.date);
        return d >= lastMonthStart && d <= lastMonthEnd;
      });

      return {
        currentMonthIncome: currentMonth
          .filter((t) => t.type === "income")
          .reduce((sum, t) => sum + t.amount, 0),
        currentMonthExpenses: currentMonth
          .filter((t) => t.type === "expense")
          .reduce((sum, t) => sum + t.amount, 0),
        lastMonthIncome: lastMonth
          .filter((t) => t.type === "income")
          .reduce((sum, t) => sum + t.amount, 0),
        lastMonthExpenses: lastMonth
          .filter((t) => t.type === "expense")
          .reduce((sum, t) => sum + t.amount, 0),
      };
    }, [transactions, currentMonthStart, lastMonthStart, lastMonthEnd]);

  const netWorth = useMemo(() => {
    const portfolioValue = portfolio?.total_value || 0;
    const cashFlow = currentMonthIncome - currentMonthExpenses;
    return portfolioValue + cashFlow;
  }, [portfolio, currentMonthIncome, currentMonthExpenses]);

  const incomeChange = lastMonthIncome > 0
    ? ((currentMonthIncome - lastMonthIncome) / lastMonthIncome) * 100
    : 0;
  const expenseChange = lastMonthExpenses > 0
    ? ((currentMonthExpenses - lastMonthExpenses) / lastMonthExpenses) * 100
    : 0;

  const chartData = useMemo(() => {
    const days = timeRange === "7d" ? 7 : timeRange === "30d" ? 30 : 90;
    return Array.from({ length: days }, (_, i) => {
      const date = subDays(now, days - i - 1);
      const dayStart = new Date(date.setHours(0, 0, 0, 0));
      const dayEnd = new Date(date.setHours(23, 59, 59, 999));

      const dayTx = transactions.filter((t) => {
        const d = new Date(t.date);
        return d >= dayStart && d <= dayEnd;
      });

      const income = dayTx
        .filter((t) => t.type === "income")
        .reduce((sum, t) => sum + t.amount, 0);
      const expenses = dayTx
        .filter((t) => t.type === "expense")
        .reduce((sum, t) => sum + t.amount, 0);

      return {
        date: format(date, days <= 7 ? "EEE" : "MMM d"),
        income,
        expenses,
        net: income - expenses,
      };
    });
  }, [transactions, timeRange, now]);

  const categoryData = useMemo(() => {
    const cats = transactions
      .filter((t) => t.type === "expense" && t.category)
      .reduce((acc, t) => {
        acc[t.category!] = (acc[t.category!] || 0) + t.amount;
        return acc;
      }, {} as Record<string, number>);

    return Object.entries(cats)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([name, value]) => ({ name, value }));
  }, [transactions]);

  const COLORS = ["#14b8a6", "#0d9488", "#10b981", "#059669", "#6366f1"];

  const recentTransactions = useMemo(
    () =>
      [...transactions]
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
        .slice(0, 5),
    [transactions]
  );

  if (loading) {
    return (
      <PageLayout title="Dashboard">
        <PageHeader title="Dashboard" description="Your financial overview" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonMetricCard key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SkeletonChart />
          </div>
          <SkeletonList items={5} />
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Dashboard" description="Your financial overview at a glance">
      {/* Net Worth Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mb-8"
      >
        <Card variant="highlight" className="p-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <p className="text-sm font-medium text-primary-700 dark:text-primary-300 mb-1">
                Net Worth
              </p>
              <h1 className="text-4xl lg:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white mb-2">
                {formatCurrency(netWorth, displayCurrency)}
              </h1>
              <div className="flex items-center gap-2">
                <Badge
                  variant={portfolio?.total_gain_loss_pct && portfolio.total_gain_loss_pct >= 0 ? "success" : "danger"}
                  className="text-sm"
                >
                  {portfolio?.total_gain_loss_pct && portfolio.total_gain_loss_pct >= 0 ? (
                    <TrendingUp className="w-3 h-3 mr-1" />
                  ) : (
                    <TrendingDown className="w-3 h-3 mr-1" />
                  )}
                  {portfolio?.total_gain_loss_pct?.toFixed(1) || 0}% all time
                </Badge>
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {format(now, "MMMM yyyy")}
                </span>
              </div>
            </div>
            <div className="flex gap-3">
              <Button
                variant="primary"
                leftIcon={<Plus className="w-4 h-4" />}
                onClick={() => window.location.href = "/transactions?action=add"}
              >
                Add Transaction
              </Button>
              <Button
                variant="secondary"
                leftIcon={<RefreshCw className="w-4 h-4" />}
                onClick={() => {
                  setLoading(true);
                  Promise.all([fetchTransactions(), fetchPortfolio()]).finally(() =>
                    setLoading(false)
                  );
                }}
              >
                Refresh
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        <MetricCard
          title="Income"
          value={formatCurrency(currentMonthIncome, displayCurrency)}
          change={incomeChange}
          changeLabel="vs last month"
          icon={<TrendingUp className="w-5 h-5" />}
          iconBg="bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400"
        />
        <MetricCard
          title="Expenses"
          value={formatCurrency(currentMonthExpenses, displayCurrency)}
          change={expenseChange}
          changeLabel="vs last month"
          invertChange
          icon={<CreditCard className="w-5 h-5" />}
          iconBg="bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400"
        />
        <MetricCard
          title="Savings"
          value={formatCurrency(currentMonthIncome - currentMonthExpenses, displayCurrency)}
          subtitle={`${((currentMonthIncome - currentMonthExpenses) / (currentMonthIncome || 1) * 100).toFixed(0)}% savings rate`}
          icon={<PiggyBank className="w-5 h-5" />}
          iconBg="bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400"
        />
        <MetricCard
          title="Investments"
          value={formatCurrency(portfolio?.total_value || 0, displayCurrency)}
          change={portfolio?.total_gain_loss_pct || 0}
          changeLabel="all time"
          icon={<Wallet className="w-5 h-5" />}
          iconBg="bg-accent-100 dark:bg-accent-900/30 text-accent-600 dark:text-accent-400"
        />
      </motion.div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Cash Flow Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Cash Flow</CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  Income vs expenses over time
                </p>
              </div>
              <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
                {(["7d", "30d", "90d"] as TimeRange[]).map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={cn(
                      "px-3 py-1 text-xs font-medium rounded-md transition-colors",
                      timeRange === range
                        ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                    )}
                  >
                    {range.toUpperCase()}
                  </button>
                ))}
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="incomeGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="expenseGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
                    <XAxis
                      dataKey="date"
                      className="text-xs"
                      tick={{ fill: "currentColor" }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      className="text-xs"
                      tick={{ fill: "currentColor" }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => formatCurrencyCompact(v, displayCurrency)}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "var(--tooltip-bg, #fff)",
                        border: "1px solid var(--tooltip-border, #e2e8f0)",
                        borderRadius: "8px",
                        boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                      }}
                      formatter={(value: number, name: string) => [
                        formatCurrency(value, displayCurrency),
                        name.charAt(0).toUpperCase() + name.slice(1),
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="income"
                      stroke="#10b981"
                      strokeWidth={2}
                      fill="url(#incomeGradient)"
                    />
                    <Area
                      type="monotone"
                      dataKey="expenses"
                      stroke="#ef4444"
                      strokeWidth={2}
                      fill="url(#expenseGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Spending by Category */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Top Categories</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Where your money goes
              </p>
            </CardHeader>
            <CardContent>
              {categoryData.length > 0 ? (
                <div className="space-y-4">
                  {categoryData.map((cat, i) => {
                    const total = categoryData.reduce((s, c) => s + c.value, 0);
                    const pct = (cat.value / total) * 100;
                    return (
                      <div key={cat.name} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: COLORS[i] }}
                            />
                            <span className="text-slate-700 dark:text-slate-300">
                              {cat.name}
                            </span>
                          </div>
                          <span className="font-medium text-slate-900 dark:text-white">
                            {formatCurrency(cat.value, displayCurrency)}
                          </span>
                        </div>
                        <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{ width: `${pct}%`, backgroundColor: COLORS[i] }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="h-48 flex items-center justify-center text-slate-400">
                  No spending data yet
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recent Transactions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.4 }}
      >
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Transactions</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Your latest activity
              </p>
            </div>
            <Link href="/transactions">
              <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                View All
              </Button>
            </Link>
          </CardHeader>
          <CardContent noPadding>
            {recentTransactions.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {recentTransactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-lg flex items-center justify-center",
                          tx.type === "income"
                            ? "bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400"
                            : tx.type === "expense"
                            ? "bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                        )}
                      >
                        {tx.type === "income" ? (
                          <ArrowUpRight className="w-5 h-5" />
                        ) : (
                          <ArrowDownRight className="w-5 h-5" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-white">
                          {tx.description}
                        </p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {format(new Date(tx.date), "MMM d, yyyy")}
                          {tx.category && ` · ${tx.category}`}
                        </p>
                      </div>
                    </div>
                    <p
                      className={cn(
                        "font-semibold",
                        tx.type === "income"
                          ? "text-success-600 dark:text-success-400"
                          : "text-danger-600 dark:text-danger-400"
                      )}
                    >
                      {tx.type === "expense" ? "-" : "+"}
                      {formatCurrency(Math.abs(tx.amount), tx.currency)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center">
                <p className="text-slate-500 dark:text-slate-400 mb-4">
                  No transactions yet
                </p>
                <Button
                  variant="primary"
                  leftIcon={<Plus className="w-4 h-4" />}
                  onClick={() => window.location.href = "/transactions?action=add"}
                >
                  Add Your First Transaction
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </PageLayout>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  change?: number;
  changeLabel?: string;
  subtitle?: string;
  icon: React.ReactNode;
  iconBg: string;
  invertChange?: boolean;
}

function MetricCard({
  title,
  value,
  change,
  changeLabel,
  subtitle,
  icon,
  iconBg,
  invertChange = false,
}: MetricCardProps) {
  const isPositive = invertChange ? (change || 0) <= 0 : (change || 0) >= 0;

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className={cn("p-2 rounded-lg", iconBg)}>{icon}</div>
          {change !== undefined && (
            <Badge variant={isPositive ? "success" : "danger"} size="sm">
              {change >= 0 ? "+" : ""}
              {change.toFixed(1)}%
            </Badge>
          )}
        </div>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">
          {title}
        </p>
        <p className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
          {value}
        </p>
        {(changeLabel || subtitle) && (
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            {subtitle || changeLabel}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
