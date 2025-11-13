import { useEffect, useState, Suspense, useMemo, useCallback } from "react";
import Head from "next/head";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import StatCard from "@/components/StatCard";
import CurrencySelector from "@/components/CurrencySelector";
import DarkModeToggle from "@/components/DarkModeToggle";
import AnimatedCard from "@/components/AnimatedCard";
import { StatCardSkeleton, ChartSkeleton, TransactionSkeleton } from "@/components/SkeletonLoader";
import LoadingSpinner from "@/components/LoadingSpinner";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  Calendar,
  Clock,
  Target,
  BarChart3,
} from "lucide-react";
import {
  LineChart,
  Line,
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
  BarChart,
  Bar,
  Legend,
} from "recharts";
import {
  format,
  subDays,
  subMonths,
  startOfMonth,
  endOfMonth,
  isSameMonth,
  isSameYear,
  startOfYear,
} from "date-fns";
import {
  formatCurrency,
  convertCurrency,
  formatCurrencyCompact,
} from "@/utils/currency";

interface Transaction {
  id: number;
  description: string;
  amount: number;
  currency: string;
  type: "income" | "expense" | "transfer";
  category?: string;
  date: string;
}

type TimeRange = "7d" | "30d" | "90d" | "1y" | "all";

export default function Home() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [displayCurrency, setDisplayCurrency] = useState("USD");
  const [showConverted, setShowConverted] = useState(true);
  const [convertedAmounts, setConvertedAmounts] = useState<
    Record<number, number>
  >({});
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [cashFlowRange, setCashFlowRange] = useState<TimeRange>("30d");
  const [spendingRange, setSpendingRange] = useState<TimeRange>("30d");

  useEffect(() => {
    fetchTransactions();
    // Check dark mode status
    const checkDarkMode = () => {
      if (typeof window !== "undefined") {
        setIsDarkMode(document.documentElement.classList.contains("dark"));
      }
    };
    checkDarkMode();
    // Watch for dark mode changes
    const observer = new MutationObserver(checkDarkMode);
    if (typeof window !== "undefined") {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["class"],
      });
    }
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (transactions.length > 0 && showConverted) {
      convertAllAmounts();
    }
  }, [transactions, displayCurrency, showConverted]);

  const fetchTransactions = async () => {
    try {
      const res = await fetch("http://localhost:8000/v1/transactions/");
      const data = await res.json();
      setTransactions(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch transactions:", err);
      setLoading(false);
    }
  };

  const convertAllAmounts = async () => {
    const converted: Record<number, number> = {};
    await Promise.all(
      transactions.map(async (tx) => {
        if (tx.currency === displayCurrency) {
          converted[tx.id] = tx.amount;
        } else {
          const convertedAmount = await convertCurrency(
            tx.amount,
            tx.currency,
            displayCurrency
          );
          converted[tx.id] = convertedAmount;
        }
      })
    );
    setConvertedAmounts(converted);
  };

  const getConvertedAmount = useCallback((tx: Transaction): number | null => {
    if (!showConverted || tx.currency === displayCurrency) return null;
    return convertedAmounts[tx.id] || null;
  }, [showConverted, displayCurrency, convertedAmounts]);

  // Calculate totals - convert all to display currency for summary (memoized)
  const { totalIncome, totalExpenses, net } = useMemo(() => {
    const income = transactions
      .filter((t) => t.type === "income")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    const expenses = transactions
      .filter((t) => t.type === "expense")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    return {
      totalIncome: income,
      totalExpenses: expenses,
      net: income - expenses,
    };
  }, [transactions, displayCurrency, convertedAmounts]);

  // Calculate month-over-month and year-over-year comparisons (memoized)
  const now = useMemo(() => new Date(), []);
  const currentMonthStart = useMemo(() => startOfMonth(now), [now]);
  const lastMonthStart = useMemo(() => startOfMonth(subMonths(now, 1)), [now]);
  const lastMonthEnd = useMemo(() => endOfMonth(subMonths(now, 1)), [now]);

  const { currentMonthTransactions, lastMonthTransactions, lastYearMonthTransactions } = useMemo(() => {
    const current = transactions.filter((t) => {
      const txDate = new Date(t.date);
      return txDate >= currentMonthStart;
    });

    const last = transactions.filter((t) => {
      const txDate = new Date(t.date);
      return txDate >= lastMonthStart && txDate <= lastMonthEnd;
    });

    const lastYear = transactions.filter((t) => {
      const txDate = new Date(t.date);
      return (
        isSameMonth(txDate, subMonths(now, 12)) &&
        isSameYear(txDate, subMonths(now, 12))
      );
    });

    return {
      currentMonthTransactions: current,
      lastMonthTransactions: last,
      lastYearMonthTransactions: lastYear,
    };
  }, [transactions, currentMonthStart, lastMonthStart, lastMonthEnd, now]);

  const {
    currentMonthIncome,
    currentMonthExpenses,
    lastMonthIncome,
    lastMonthExpenses,
    lastYearMonthIncome,
    lastYearMonthExpenses,
  } = useMemo(() => {
    const currentIncome = currentMonthTransactions
      .filter((t) => t.type === "income")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    const currentExpenses = currentMonthTransactions
      .filter((t) => t.type === "expense")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    const lastIncome = lastMonthTransactions
      .filter((t) => t.type === "income")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    const lastExpenses = lastMonthTransactions
      .filter((t) => t.type === "expense")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    const lastYearIncome = lastYearMonthTransactions
      .filter((t) => t.type === "income")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    const lastYearExpenses = lastYearMonthTransactions
      .filter((t) => t.type === "expense")
      .reduce((sum, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        return sum + amount;
      }, 0);

    return {
      currentMonthIncome: currentIncome,
      currentMonthExpenses: currentExpenses,
      lastMonthIncome: lastIncome,
      lastMonthExpenses: lastExpenses,
      lastYearMonthIncome: lastYearIncome,
      lastYearMonthExpenses: lastYearExpenses,
    };
  }, [
    currentMonthTransactions,
    lastMonthTransactions,
    lastYearMonthTransactions,
    displayCurrency,
    convertedAmounts,
  ]);

  const incomeChangeMoM =
    lastMonthIncome > 0
      ? ((currentMonthIncome - lastMonthIncome) / lastMonthIncome) * 100
      : 0;
  const expensesChangeMoM =
    lastMonthExpenses > 0
      ? ((currentMonthExpenses - lastMonthExpenses) / lastMonthExpenses) * 100
      : 0;
  const netChangeMoM =
    currentMonthIncome -
    currentMonthExpenses -
    (lastMonthIncome - lastMonthExpenses);

  // Generate chart data based on selected range
  const getDaysForRange = (range: TimeRange): number => {
    switch (range) {
      case "7d":
        return 7;
      case "30d":
        return 30;
      case "90d":
        return 90;
      case "1y":
        return 365;
      case "all":
        if (transactions.length === 0) return 30;
        const oldestTx = Math.min(
          ...transactions.map((t) => new Date(t.date).getTime())
        );
        const daysDiff = Math.ceil(
          (now.getTime() - oldestTx) / (1000 * 60 * 60 * 24)
        );
        return Math.min(365, daysDiff);
      default:
        return 30;
    }
  };

  const getChartData = useCallback((range: TimeRange) => {
    const days = getDaysForRange(range);
    const isDaily = days <= 30;
    const interval = isDaily ? 1 : Math.ceil(days / 30);

    return Array.from({ length: Math.ceil(days / interval) }, (_, i) => {
      const date = subDays(now, days - i * interval - 1);
      const dayStart = new Date(date);
      dayStart.setHours(0, 0, 0, 0);
      const dayEnd = new Date(date);
      dayEnd.setHours(23, 59, 59, 999);

      const dayTransactions = transactions.filter((t) => {
        const txDate = new Date(t.date);
        return txDate >= dayStart && txDate <= dayEnd;
      });

      const income = dayTransactions
        .filter((t) => t.type === "income")
        .reduce((sum, t) => {
          const amount =
            t.currency === displayCurrency
              ? t.amount
              : convertedAmounts[t.id] || 0;
          return sum + amount;
        }, 0);
      const expenses = dayTransactions
        .filter((t) => t.type === "expense")
        .reduce((sum, t) => {
          const amount =
            t.currency === displayCurrency
              ? t.amount
              : convertedAmounts[t.id] || 0;
          return sum + amount;
        }, 0);

      return {
        date: isDaily ? format(date, "MMM dd") : format(date, "MMM dd"),
        fullDate: date,
        income,
        expenses,
        net: income - expenses,
      };
    }).filter((d) => d.fullDate <= now);
  }, [transactions, displayCurrency, convertedAmounts, now]);

  const cashFlowData = useMemo(
    () => getChartData(cashFlowRange),
    [getChartData, cashFlowRange]
  );

  // Category breakdown (using converted amounts) - memoized
  const { categoryData, totalExpensesForChart, pieData } = useMemo(() => {
    const catData = transactions
      .filter((t) => t.type === "expense" && t.category)
      .reduce((acc, t) => {
        const amount =
          t.currency === displayCurrency ? t.amount : convertedAmounts[t.id] || 0;
        acc[t.category!] = (acc[t.category!] || 0) + amount;
        return acc;
      }, {} as Record<string, number>);

    const total = Object.values(catData).reduce((sum, val) => sum + val, 0);
    const threshold = total * 0.05; // 5% threshold

    const pie = Object.entries(catData)
      .sort(([, a], [, b]) => b - a) // Sort by value descending
      .reduce((acc, [name, value]) => {
        if (value >= threshold) {
          acc.push({ name, value });
        } else {
          // Add to "Others" category
          const othersIndex = acc.findIndex((item) => item.name === "Others");
          if (othersIndex >= 0) {
            acc[othersIndex].value += value;
          } else {
            acc.push({ name: "Others", value });
          }
        }
        return acc;
      }, [] as Array<{ name: string; value: number }>);

    return {
      categoryData: catData,
      totalExpensesForChart: total,
      pieData: pie,
    };
  }, [transactions, displayCurrency, convertedAmounts]);

  // Warm golden color palette for charts
  const COLORS = [
    "#D4AF37", // Primary gold
    "#F4D03F", // Light gold
    "#C9A961", // Muted gold
    "#B8941F", // Dark gold
    "#f59e0b", // Amber
    "#10b981", // Green
    "#ef4444", // Red
    "#9C9580", // Warm gray
  ];

  // Calculate net worth change percentage
  const netWorthChangePercent =
    lastMonthIncome + lastMonthExpenses > 0
      ? ((net - (lastMonthIncome - lastMonthExpenses)) /
          Math.abs(lastMonthIncome - lastMonthExpenses)) *
        100
      : 0;

  // Get recurring-like transactions (same merchant, similar amount, regular intervals) - memoized
  const recurringTransactions = useMemo(() => {
    const merchantGroups = transactions.reduce((acc, tx) => {
      if (!tx.category) return acc;
      const key = `${tx.description.toLowerCase().substring(0, 20)}`;
      if (!acc[key]) acc[key] = [];
      acc[key].push(tx);
      return acc;
    }, {} as Record<string, Transaction[]>);

    return Object.entries(merchantGroups)
      .filter(([_, txs]) => txs.length >= 2)
      .map(([_, txs]) => {
        const sorted = txs.sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        );
        return sorted[0];
      })
      .slice(0, 3);
  }, [transactions]);

  // Budget simulation (based on average spending) - memoized
  const budgetCategories = useMemo(() => {
    return Object.entries(categoryData)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([name, spent]) => ({
        name,
        spent,
        budget: Math.max(spent * 1.2, spent + 100), // Simulated budget (20% buffer)
      }));
  }, [categoryData]);

  return (
    <>
      <Head>
        <title>Dashboard - Canopy</title>
        <meta
          name="description"
          content="Privacy-first personal finance dashboard"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div className="flex min-h-screen bg-warm-gray-50 dark:bg-warm-gray-900">
        <Sidebar />
        <main className="flex-1 ml-64 p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <AnimatedCard delay={0}>
              <div className="mb-8 flex items-center justify-between">
                <div>
                  <h1 className="text-4xl font-bold text-warm-gray-900 dark:text-warm-gray-50 mb-2">
                    Dashboard
                  </h1>
                  <p className="text-warm-gray-600 dark:text-warm-gray-400">
                    Welcome back! Here's your financial overview.
                  </p>
                </div>
              <div className="flex items-center gap-4">
                <DarkModeToggle />
                <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2">
                  <input
                    type="checkbox"
                    id="showConvertedDashboard"
                    checked={showConverted}
                    onChange={(e) => setShowConverted(e.target.checked)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500 dark:focus:ring-primary-400"
                  />
                  <label
                    htmlFor="showConvertedDashboard"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer"
                  >
                    Show converted
                  </label>
                </div>
                {showConverted && (
                  <CurrencySelector
                    selectedCurrency={displayCurrency}
                    onCurrencyChange={setDisplayCurrency}
                    showLabel={false}
                  />
                )}
              </div>
            </AnimatedCard>

            {/* Stats Grid - Enhanced with trends */}
            <Suspense fallback={
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {[0, 1, 2].map((i) => (
                  <StatCardSkeleton key={i} />
                ))}
              </div>
            }>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <StatCard
                title="Net Worth"
                value={formatCurrency(net, displayCurrency)}
                change={
                  netChangeMoM !== 0
                    ? `${netChangeMoM >= 0 ? "+" : ""}${formatCurrency(
                        netChangeMoM,
                        displayCurrency
                      )} (${
                        netWorthChangePercent >= 0 ? "+" : ""
                      }${netWorthChangePercent.toFixed(1)}%)`
                    : undefined
                }
                changeType={netChangeMoM >= 0 ? "positive" : "negative"}
                icon={TrendingUp}
                gradient="bg-gradient-to-br from-green-400 to-emerald-500"
              />
              <StatCard
                title="Total Income"
                value={formatCurrency(currentMonthIncome, displayCurrency)}
                change={
                  incomeChangeMoM !== 0
                    ? `${
                        incomeChangeMoM >= 0 ? "+" : ""
                      }${incomeChangeMoM.toFixed(1)}% vs last month`
                    : undefined
                }
                changeType={incomeChangeMoM >= 0 ? "positive" : "negative"}
                icon={DollarSign}
                gradient="bg-gradient-to-br from-blue-400 to-cyan-500"
              />
              <StatCard
                title="Total Expenses"
                value={formatCurrency(currentMonthExpenses, displayCurrency)}
                change={
                  expensesChangeMoM !== 0
                    ? `${
                        expensesChangeMoM >= 0 ? "+" : ""
                      }${expensesChangeMoM.toFixed(1)}% vs last month`
                    : undefined
                }
                changeType={expensesChangeMoM <= 0 ? "positive" : "negative"}
                icon={TrendingDown}
                gradient="bg-gradient-to-br from-red-400 to-rose-500"
              />
              </div>
            </Suspense>

            {/* Budget Overview Section */}
            {budgetCategories.length > 0 && (
              <AnimatedCard delay={0.1}>
                <div className="card p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-warm-gray-900 dark:text-warm-gray-50">
                      Budget {format(now, "MMMM yyyy")}
                    </h2>
                    <p className="text-sm text-warm-gray-500 dark:text-warm-gray-400 mt-1">
                      Track your spending by category
                    </p>
                  </div>
                </div>
                <div className="space-y-4">
                  {budgetCategories.map((category) => {
                    const percentage = (category.spent / category.budget) * 100;
                    const isOverBudget = percentage > 100;
                    return (
                      <div key={category.name} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium text-warm-gray-700 dark:text-warm-gray-300">
                            {category.name}
                          </span>
                          <div className="flex items-center gap-3">
                            <span
                              className={`font-semibold ${
                                isOverBudget
                                  ? "text-red-600 dark:text-red-400"
                                  : "text-warm-gray-700 dark:text-warm-gray-300"
                              }`}
                            >
                              {formatCurrency(category.spent, displayCurrency)}
                            </span>
                            <span className="text-warm-gray-400 dark:text-warm-gray-500">
                              of
                            </span>
                            <span className="text-warm-gray-600 dark:text-warm-gray-400">
                              {formatCurrency(category.budget, displayCurrency)}
                            </span>
                          </div>
                        </div>
                        <div className="relative h-2 bg-warm-gray-200 dark:bg-warm-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              isOverBudget
                                ? "bg-red-500"
                                : percentage > 80
                                ? "bg-yellow-500"
                                : "bg-green-500"
                            }`}
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                        <div className="flex items-center justify-between text-xs text-warm-gray-500 dark:text-warm-gray-400">
                          <span>{percentage.toFixed(0)}% used</span>
                          <span>
                            {isOverBudget
                              ? `${formatCurrency(
                                  category.spent - category.budget,
                                  displayCurrency
                                )} over budget`
                              : `${formatCurrency(
                                  category.budget - category.spent,
                                  displayCurrency
                                )} remaining`}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </AnimatedCard>
            )}

            {/* Charts Grid - Enhanced */}
            <Suspense fallback={
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <ChartSkeleton />
                <ChartSkeleton />
              </div>
            }>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Cash Flow Chart with Time Range Selector */}
                <AnimatedCard delay={0.15}>
                  <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-warm-gray-900 dark:text-warm-gray-50">
                      Cash Flow
                    </h2>
                    <p className="text-sm text-warm-gray-500 dark:text-warm-gray-400 mt-1">
                      {formatCurrency(
                        currentMonthIncome - currentMonthExpenses,
                        displayCurrency
                      )}{" "}
                      this month
                    </p>
                  </div>
                  <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                    {(["7d", "30d", "90d", "1y"] as TimeRange[]).map(
                      (range) => (
                        <button
                          key={range}
                          onClick={() => setCashFlowRange(range)}
                        className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                          cashFlowRange === range
                            ? "bg-white dark:bg-warm-gray-700 text-warm-gray-900 dark:text-warm-gray-50 shadow-sm"
                            : "text-warm-gray-600 dark:text-warm-gray-400 hover:text-warm-gray-900 dark:hover:text-warm-gray-50"
                        }`}
                        >
                          {range === "7d"
                            ? "7D"
                            : range === "30d"
                            ? "30D"
                            : range === "90d"
                            ? "90D"
                            : "1Y"}
                        </button>
                      )
                    )}
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={cashFlowData}>
                    <defs>
                      <linearGradient
                        id="colorIncome"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#10b981"
                          stopOpacity={0.4}
                        />
                        <stop
                          offset="95%"
                          stopColor="#10b981"
                          stopOpacity={0}
                        />
                      </linearGradient>
                      <linearGradient
                        id="colorExpenses"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#ef4444"
                          stopOpacity={0.4}
                        />
                        <stop
                          offset="95%"
                          stopColor="#ef4444"
                          stopOpacity={0}
                        />
                      </linearGradient>
                      <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                        <stop
                          offset="5%"
                          stopColor="#D4AF37"
                          stopOpacity={0.4}
                        />
                        <stop
                          offset="95%"
                          stopColor="#D4AF37"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#E8E4D8"
                      className="dark:stroke-warm-gray-700"
                    />
                    <XAxis
                      dataKey="date"
                      stroke="#9C9580"
                      className="dark:stroke-warm-gray-400"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis
                      stroke="#9C9580"
                      className="dark:stroke-warm-gray-400"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) =>
                        formatCurrencyCompact(value, displayCurrency)
                      }
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDarkMode ? "#1C1810" : "#FAF9F6",
                        border: `1px solid ${
                          isDarkMode ? "#3E3A30" : "#E8E4D8"
                        }`,
                        borderRadius: "12px",
                        boxShadow: "0 4px 6px -1px rgba(212, 175, 55, 0.1)",
                        color: isDarkMode ? "#F5F3ED" : "#1C1810",
                      }}
                      formatter={(value: number, name: string) => [
                        formatCurrency(value, displayCurrency),
                        name === "income"
                          ? "Income"
                          : name === "expenses"
                          ? "Expenses"
                          : "Net",
                      ]}
                    />
                    <Legend
                      wrapperStyle={{ paddingTop: "20px" }}
                      iconType="circle"
                      formatter={(value) =>
                        value === "income"
                          ? "Income"
                          : value === "expenses"
                          ? "Expenses"
                          : "Net"
                      }
                    />
                    <Area
                      type="monotone"
                      dataKey="income"
                      stroke="#10b981"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorIncome)"
                      name="income"
                    />
                    <Area
                      type="monotone"
                      dataKey="expenses"
                      stroke="#ef4444"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorExpenses)"
                      name="expenses"
                    />
                    <Line
                      type="monotone"
                      dataKey="net"
                      stroke="#D4AF37"
                      strokeWidth={2}
                      dot={false}
                      name="net"
                    />
                  </AreaChart>
                </ResponsiveContainer>
                </div>
              </AnimatedCard>

              {/* Spending by Category - Enhanced */}
              <AnimatedCard delay={0.2}>
                <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-warm-gray-900 dark:text-warm-gray-50">
                      Spending by Category
                    </h2>
                    <p className="text-sm text-warm-gray-500 dark:text-warm-gray-400 mt-1">
                      {formatCurrency(currentMonthExpenses, displayCurrency)}{" "}
                      this month
                    </p>
                  </div>
                </div>
                {pieData.length > 0 ? (
                  <div className="flex flex-col lg:flex-row gap-6">
                    <div className="flex-1">
                      <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                          <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {pieData.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={
                                  entry.name === "Others"
                                    ? "#6b7280"
                                    : COLORS[index % (COLORS.length - 1)]
                                }
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(value: number) =>
                              formatCurrency(value, displayCurrency)
                            }
                            contentStyle={{
                              backgroundColor: isDarkMode ? "#1f2937" : "white",
                              border: `1px solid ${
                                isDarkMode ? "#374151" : "#e5e7eb"
                              }`,
                              borderRadius: "12px",
                              color: isDarkMode ? "#f3f4f6" : "#111827",
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex-1 space-y-3">
                      {pieData.slice(0, 5).map((entry, index) => {
                        const percentage =
                          (entry.value / totalExpensesForChart) * 100;
                        return (
                          <div
                            key={entry.name}
                            className="flex items-center justify-between"
                          >
                            <div className="flex items-center gap-3">
                              <div
                                className="w-3 h-3 rounded-full"
                                style={{
                                  backgroundColor:
                                    entry.name === "Others"
                                      ? "#6b7280"
                                      : COLORS[index % (COLORS.length - 1)],
                                }}
                              />
                              <span className="text-sm font-medium text-warm-gray-700 dark:text-warm-gray-300">
                                {entry.name}
                              </span>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="w-24 h-2 bg-warm-gray-200 dark:bg-warm-gray-700 rounded-full overflow-hidden">
                                <div
                                  className="h-full rounded-full"
                                  style={{
                                    width: `${percentage}%`,
                                    backgroundColor:
                                      entry.name === "Others"
                                        ? "#6b7280"
                                        : COLORS[index % (COLORS.length - 1)],
                                  }}
                                />
                              </div>
                              <div className="text-right min-w-[100px]">
                                <div className="text-sm font-semibold text-warm-gray-900 dark:text-warm-gray-50">
                                  {formatCurrency(entry.value, displayCurrency)}
                                </div>
                                <div className="text-xs text-warm-gray-500 dark:text-warm-gray-400">
                                  {percentage.toFixed(1)}%
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-gray-400 dark:text-gray-500">
                    No category data yet
                  </div>
                )}
              </div>
            </div>

            {/* Additional Sections Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Spending Comparison Chart */}
              <AnimatedCard delay={0.25}>
                <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-warm-gray-900 dark:text-warm-gray-50">
                      Spending Comparison
                    </h2>
                    <p className="text-sm text-warm-gray-500 dark:text-warm-gray-400 mt-1">
                      This month vs last month
                    </p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart
                    data={[
                      {
                        name: "This Month",
                        income: currentMonthIncome,
                        expenses: currentMonthExpenses,
                      },
                      {
                        name: "Last Month",
                        income: lastMonthIncome,
                        expenses: lastMonthExpenses,
                      },
                    ]}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#E8E4D8"
                      className="dark:stroke-warm-gray-700"
                    />
                    <XAxis
                      dataKey="name"
                      stroke="#9C9580"
                      className="dark:stroke-warm-gray-400"
                    />
                    <YAxis
                      stroke="#9C9580"
                      className="dark:stroke-warm-gray-400"
                      tickFormatter={(value) =>
                        formatCurrencyCompact(value, displayCurrency)
                      }
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDarkMode ? "#1C1810" : "#FAF9F6",
                        border: `1px solid ${
                          isDarkMode ? "#3E3A30" : "#E8E4D8"
                        }`,
                        borderRadius: "12px",
                        color: isDarkMode ? "#F5F3ED" : "#1C1810",
                      }}
                      formatter={(value: number) =>
                        formatCurrency(value, displayCurrency)
                      }
                    />
                    <Legend />
                    <Bar
                      dataKey="income"
                      fill="#10b981"
                      name="Income"
                      radius={[8, 8, 0, 0]}
                    />
                    <Bar
                      dataKey="expenses"
                      fill="#ef4444"
                      name="Expenses"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
                </div>
              </AnimatedCard>

              {/* Recurring Transactions Preview */}
              <AnimatedCard delay={0.3}>
                <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-warm-gray-900 dark:text-warm-gray-50">
                      Recurring Transactions
                    </h2>
                    <p className="text-sm text-warm-gray-500 dark:text-warm-gray-400 mt-1">
                      Upcoming recurring payments
                    </p>
                  </div>
                  <Clock className="w-5 h-5 text-warm-gray-400 dark:text-warm-gray-500" />
                </div>
                {recurringTransactions.length > 0 ? (
                  <div className="space-y-4">
                    {recurringTransactions.map((tx) => {
                      const convertedAmount = getConvertedAmount(tx);
                      return (
                        <div
                          key={tx.id}
                          className="flex items-center justify-between p-3 bg-warm-gray-50 dark:bg-warm-gray-800/50 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                                tx.type === "expense"
                                  ? "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
                                  : "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                              }`}
                            >
                              {tx.type === "expense" ? (
                                <TrendingDown size={18} />
                              ) : (
                                <TrendingUp size={18} />
                              )}
                            </div>
                            <div>
                              <p className="font-medium text-warm-gray-900 dark:text-warm-gray-50 text-sm">
                                {tx.description.length > 30
                                  ? `${tx.description.substring(0, 30)}...`
                                  : tx.description}
                              </p>
                              <p className="text-xs text-warm-gray-500 dark:text-warm-gray-400">
                                {tx.category || "Uncategorized"} • Monthly
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p
                              className={`font-semibold text-sm ${
                                tx.type === "expense"
                                  ? "text-red-600 dark:text-red-400"
                                  : "text-green-600 dark:text-green-400"
                              }`}
                            >
                              {tx.type === "expense" ? "-" : "+"}
                              {formatCurrency(Math.abs(tx.amount), tx.currency)}
                            </p>
                            {showConverted &&
                              convertedAmount &&
                              tx.currency !== displayCurrency && (
                              <p className="text-xs text-warm-gray-500 dark:text-warm-gray-400">
                                ≈{" "}
                                {formatCurrency(
                                  Math.abs(convertedAmount),
                                  displayCurrency
                                )}
                              </p>
                              )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="h-[200px] flex items-center justify-center text-gray-400 dark:text-gray-500">
                    <div className="text-center">
                      <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">
                        No recurring transactions detected
                      </p>
                    </div>
                  </div>
                )}
                </div>
              </AnimatedCard>
            </div>

            {/* Recent Transactions */}
            <AnimatedCard delay={0.35}>
              <div className="card">
              <div className="p-6 border-b border-warm-gray-100 dark:border-warm-gray-700 flex items-center justify-between">
                <h2 className="text-xl font-bold text-warm-gray-900 dark:text-warm-gray-50">
                  Recent Transactions
                </h2>
                <Link
                  href="/transactions"
                  className="btn-secondary text-sm flex items-center gap-2"
                >
                  View All
                  <ArrowUpRight size={16} />
                </Link>
              </div>
              {loading ? (
                <Suspense fallback={<TransactionSkeleton />}>
                  <div className="p-12 text-center text-warm-gray-400 dark:text-warm-gray-500">
                    <LoadingSpinner size="lg" className="mx-auto mb-4" />
                    <p>Loading transactions...</p>
                  </div>
                </Suspense>
              ) : transactions.length === 0 ? (
                <div className="p-12 text-center">
                  <p className="text-warm-gray-400 dark:text-warm-gray-500 mb-4">
                    No transactions yet
                  </p>
                  <Link
                    href="/transactions"
                    className="btn-primary inline-block"
                  >
                    Add Your First Transaction
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-warm-gray-100 dark:divide-warm-gray-700">
                  {transactions
                    .sort(
                      (a, b) =>
                        new Date(b.date).getTime() - new Date(a.date).getTime()
                    )
                    .slice(0, 5)
                    .map((tx) => {
                      const convertedAmount = getConvertedAmount(tx);
                      return (
                        <div
                          key={tx.id}
                          className="p-6 hover:bg-warm-gray-50 dark:hover:bg-warm-gray-700/50 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div
                                className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                                  tx.type === "income"
                                    ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                                    : tx.type === "expense"
                                    ? "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
                                    : "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
                                }`}
                              >
                                {tx.type === "income" ? (
                                  <TrendingUp size={20} />
                                ) : tx.type === "expense" ? (
                                  <TrendingDown size={20} />
                                ) : (
                                  <DollarSign size={20} />
                                )}
                              </div>
                              <div>
                                <h3 className="font-semibold text-warm-gray-900 dark:text-warm-gray-50">
                                  {tx.description}
                                </h3>
                                <p className="text-sm text-warm-gray-500 dark:text-warm-gray-400">
                                  {format(new Date(tx.date), "MMM dd, yyyy")}
                                  {tx.category && ` • ${tx.category}`}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="flex items-baseline gap-2">
                                <p
                                  className={`text-lg font-bold ${
                                    tx.type === "income"
                                      ? "text-green-600 dark:text-green-400"
                                      : "text-red-600 dark:text-red-400"
                                  }`}
                                >
                                  {tx.type === "expense" ? "-" : "+"}
                                  {formatCurrency(
                                    Math.abs(tx.amount),
                                    tx.currency
                                  )}
                                </p>
                                {showConverted &&
                                  convertedAmount &&
                                  tx.currency !== displayCurrency && (
                                    <>
                                    <span className="text-warm-gray-400 dark:text-warm-gray-500">
                                      ≈
                                    </span>
                                    <p
                                      className={`text-base font-semibold text-warm-gray-600 dark:text-warm-gray-300 ${
                                          tx.type === "income"
                                            ? "text-green-600 dark:text-green-400"
                                            : "text-red-600 dark:text-red-400"
                                        }`}
                                      >
                                        {formatCurrency(
                                          Math.abs(convertedAmount),
                                          displayCurrency
                                        )}
                                      </p>
                                    </>
                                  )}
                              </div>
                              <p className="text-xs text-warm-gray-400 dark:text-warm-gray-500 mt-1">
                                {tx.currency}
                                {showConverted &&
                                  convertedAmount &&
                                  tx.currency !== displayCurrency && (
                                    <span className="ml-1">
                                      → {displayCurrency}
                                    </span>
                                  )}
                              </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                </div>
              )}
              </div>
            </AnimatedCard>
          </div>
        </main>
      </div>
    </>
  );
}
