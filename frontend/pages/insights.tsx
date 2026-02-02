import React, { useState } from "react";
import Head from "next/head";
import { useQuery, useMutation } from "@tanstack/react-query";
import Sidebar from "../components/Sidebar";
import DarkModeToggle from "../components/DarkModeToggle";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  PieChart,
  Globe,
  Calendar,
  Loader2,
  Calculator,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
} from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// Types
interface NetWorth {
  total_usd: number;
  total_assets_usd: number;
  total_liabilities_usd: number;
  liquid_assets_usd: number;
  investment_assets_usd: number;
  retirement_assets_usd: number;
  real_estate_equity_usd: number;
  assets_by_currency: Record<string, number>;
  liabilities_by_currency: Record<string, number>;
  change_1d: number | null;
  change_1d_percent: number | null;
  change_1m: number | null;
  change_1m_percent: number | null;
  change_ytd: number | null;
  change_ytd_percent: number | null;
}

interface Allocation {
  by_type: Record<string, number>;
  by_currency: Record<string, number>;
  by_country: Record<string, number>;
  by_institution: Record<string, number>;
}

interface CurrencyExposure {
  exposures: Record<string, number>;
  amounts_usd: Record<string, number>;
  risk_assessment: string;
}

interface Growth {
  monthly_rate: number;
  yearly_rate: number;
  average_monthly: number;
  best_month: string | null;
  best_month_return: number | null;
  worst_month: string | null;
  worst_month_return: number | null;
}

interface InsightsSummary {
  net_worth: NetWorth;
  allocation: Allocation;
  currency_exposure: CurrencyExposure;
  growth: Growth;
}

interface FIREMetrics {
  fire_number: number;
  current_net_worth: number;
  progress_percentage: number;
  years_to_fire: number | null;
  fire_date: string | null;
  monthly_income_at_fire: number;
  annual_income_at_fire: number;
  monthly_expenses: number;
  annual_expenses: number;
  safe_withdrawal_rate: number;
  expected_return: number;
}

interface ProjectionPoint {
  year: number;
  date: string;
  net_worth: number;
  contributions: number;
  growth: number;
  passive_income: number;
}

interface Scenario {
  name: string;
  years_to_fire: number | null;
  fire_date: string | null;
  final_net_worth: number;
  difference_years: number | null;
}

interface FIRESummary {
  metrics: FIREMetrics;
  projections: ProjectionPoint[];
  scenarios: Scenario[];
}

// Helpers
function formatCurrency(
  value: number | null,
  currency: string = "USD",
): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number | null): string {
  if (value === null) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function formatYears(years: number | null): string {
  if (years === null) return "—";
  if (years < 1) return `${Math.round(years * 12)} months`;
  return `${years.toFixed(1)} years`;
}

// Colors for charts
const COLORS = [
  "#3b82f6", // blue
  "#10b981", // emerald
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#84cc16", // lime
];

const CURRENCY_FLAGS: Record<string, string> = {
  CAD: "🇨🇦",
  USD: "🇺🇸",
  BRL: "🇧🇷",
  EUR: "🇪🇺",
  Crypto: "₿",
};

export default function Insights() {
  const [baseCurrency, setBaseCurrency] = useState<
    "USD" | "CAD" | "BRL" | "EUR"
  >("USD");
  const [monthlyExpenses, setMonthlyExpenses] = useState(5000);
  const [monthlySavings, setMonthlySavings] = useState(2000);
  const [expenseCurrency, setExpenseCurrency] = useState("CAD");
  const [showFIREDetails, setShowFIREDetails] = useState(false);

  // Fetch insights summary
  const { data: insights, isLoading: insightsLoading } =
    useQuery<InsightsSummary>({
      queryKey: ["insights-summary", baseCurrency],
      queryFn: async () => {
        const res = await fetch(
          `${API_URL}/v1/insights/summary?base_currency=${baseCurrency}`,
        );
        if (!res.ok) throw new Error("Failed to fetch insights");
        return res.json();
      },
    });

  // Fetch FIRE calculations
  const { data: fire, isLoading: fireLoading } = useQuery<FIRESummary>({
    queryKey: [
      "fire-summary",
      monthlyExpenses,
      monthlySavings,
      expenseCurrency,
    ],
    queryFn: async () => {
      const res = await fetch(
        `${API_URL}/v1/insights/fire?monthly_expenses=${monthlyExpenses}&monthly_savings=${monthlySavings}&currency=${expenseCurrency}`,
      );
      if (!res.ok) throw new Error("Failed to fetch FIRE data");
      return res.json();
    },
  });

  // Fetch historical data
  const { data: historical } = useQuery<{ date: string; net_worth: number }[]>({
    queryKey: ["historical-networth"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/insights/historical?period=all`);
      if (!res.ok) throw new Error("Failed to fetch historical data");
      return res.json();
    },
  });

  // Prepare chart data
  const allocationByType = insights?.allocation.by_type
    ? Object.entries(insights.allocation.by_type).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: Number(value.toFixed(1)),
      }))
    : [];

  const currencyExposure = insights?.currency_exposure.exposures
    ? Object.entries(insights.currency_exposure.exposures).map(
        ([name, value]) => ({
          name,
          value: Number(value.toFixed(1)),
          amount: insights.currency_exposure.amounts_usd[name] || 0,
        }),
      )
    : [];

  const projectionData =
    fire?.projections.filter(
      (_, i) => i % 5 === 0 || i === fire.projections.length - 1,
    ) || [];

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
      <Head>
        <title>Insights - Canopy</title>
      </Head>
      <Sidebar />

      <main className="flex-1 p-8 ml-64">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Insights
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Financial overview, projections, and FIRE planning
            </p>
          </div>
          <div className="flex items-center gap-4">
            {/* Base Currency Selector */}
            <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg px-3 py-2 shadow-sm">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Base:
              </span>
              {(["USD", "CAD", "BRL", "EUR"] as const).map((curr) => (
                <button
                  key={curr}
                  onClick={() => setBaseCurrency(curr)}
                  className={`px-2 py-1 rounded text-sm font-medium transition-colors ${
                    baseCurrency === curr
                      ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                      : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                  }`}
                >
                  {curr}
                </button>
              ))}
            </div>
            <DarkModeToggle />
          </div>
        </div>

        {insightsLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        ) : insights ? (
          <div className="space-y-8">
            {/* Net Worth Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Total Net Worth */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600 dark:text-gray-400 text-sm">
                    Net Worth
                  </span>
                  <DollarSign className="w-5 h-5 text-blue-500" />
                </div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(insights.net_worth.total_usd, baseCurrency)}
                </div>
                {insights.net_worth.change_1m_percent !== null && (
                  <div
                    className={`flex items-center text-sm mt-1 ${
                      insights.net_worth.change_1m_percent >= 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {insights.net_worth.change_1m_percent >= 0 ? (
                      <TrendingUp className="w-4 h-4 mr-1" />
                    ) : (
                      <TrendingDown className="w-4 h-4 mr-1" />
                    )}
                    {formatPercent(insights.net_worth.change_1m_percent)} (30d)
                  </div>
                )}
              </div>

              {/* Total Assets */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600 dark:text-gray-400 text-sm">
                    Total Assets
                  </span>
                  <TrendingUp className="w-5 h-5 text-green-500" />
                </div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {formatCurrency(
                    insights.net_worth.total_assets_usd,
                    baseCurrency,
                  )}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Across{" "}
                  {Object.keys(insights.net_worth.assets_by_currency).length}{" "}
                  currencies
                </div>
              </div>

              {/* Total Liabilities */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600 dark:text-gray-400 text-sm">
                    Total Liabilities
                  </span>
                  <TrendingDown className="w-5 h-5 text-red-500" />
                </div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {formatCurrency(
                    insights.net_worth.total_liabilities_usd,
                    baseCurrency,
                  )}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {
                    Object.keys(insights.net_worth.liabilities_by_currency)
                      .length
                  }{" "}
                  accounts
                </div>
              </div>

              {/* YTD Change */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600 dark:text-gray-400 text-sm">
                    YTD Change
                  </span>
                  <Calendar className="w-5 h-5 text-purple-500" />
                </div>
                <div
                  className={`text-2xl font-bold ${
                    (insights.net_worth.change_ytd_percent || 0) >= 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {formatPercent(insights.net_worth.change_ytd_percent)}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {formatCurrency(insights.net_worth.change_ytd, baseCurrency)}
                </div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Asset Allocation Pie Chart */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <PieChart className="w-5 h-5 mr-2 text-blue-500" />
                  Asset Allocation
                </h2>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={allocationByType}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        fill="#8884d8"
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}%`}
                      >
                        {allocationByType.map((_, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={COLORS[index % COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `${value}%`} />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Currency Exposure */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <Globe className="w-5 h-5 mr-2 text-green-500" />
                  Currency Exposure
                  <span
                    className={`ml-2 px-2 py-0.5 rounded text-xs ${
                      insights.currency_exposure.risk_assessment ===
                      "diversified"
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : insights.currency_exposure.risk_assessment ===
                            "balanced"
                          ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                          : "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                    }`}
                  >
                    {insights.currency_exposure.risk_assessment}
                  </span>
                </h2>
                <div className="space-y-3">
                  {currencyExposure.map((item, index) => (
                    <div key={item.name} className="flex items-center">
                      <span className="w-8 text-lg">
                        {CURRENCY_FLAGS[item.name] || "💱"}
                      </span>
                      <span className="w-16 text-sm font-medium text-gray-700 dark:text-gray-300">
                        {item.name}
                      </span>
                      <div className="flex-1 mx-3">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${item.value}%`,
                              backgroundColor: COLORS[index % COLORS.length],
                            }}
                          />
                        </div>
                      </div>
                      <span className="w-16 text-sm text-right text-gray-600 dark:text-gray-400">
                        {item.value.toFixed(1)}%
                      </span>
                      <span className="w-24 text-sm text-right text-gray-500 dark:text-gray-500">
                        {formatCurrency(item.amount, "USD")}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* FIRE Calculator Section */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                  <Target className="w-5 h-5 mr-2 text-orange-500" />
                  FIRE Calculator
                </h2>
                <button
                  onClick={() => setShowFIREDetails(!showFIREDetails)}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
                >
                  {showFIREDetails ? "Hide" : "Show"} Details
                  {showFIREDetails ? (
                    <ChevronUp className="w-4 h-4 ml-1" />
                  ) : (
                    <ChevronDown className="w-4 h-4 ml-1" />
                  )}
                </button>
              </div>

              {/* FIRE Inputs */}
              {showFIREDetails && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Monthly Expenses
                    </label>
                    <div className="flex">
                      <input
                        type="number"
                        value={monthlyExpenses}
                        onChange={(e) =>
                          setMonthlyExpenses(Number(e.target.value))
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-l-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                      <select
                        value={expenseCurrency}
                        onChange={(e) => setExpenseCurrency(e.target.value)}
                        className="px-3 py-2 border border-l-0 border-gray-300 dark:border-gray-600 rounded-r-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      >
                        <option value="CAD">CAD</option>
                        <option value="USD">USD</option>
                        <option value="BRL">BRL</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Monthly Savings
                    </label>
                    <input
                      type="number"
                      value={monthlySavings}
                      onChange={(e) =>
                        setMonthlySavings(Number(e.target.value))
                      }
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div className="flex items-end">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <div>
                        SWR:{" "}
                        {(
                          (fire?.metrics.safe_withdrawal_rate || 0.04) * 100
                        ).toFixed(0)}
                        %
                      </div>
                      <div>
                        Return:{" "}
                        {(
                          (fire?.metrics.expected_return || 0.07) * 100
                        ).toFixed(0)}
                        %
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {fire && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                  {/* FIRE Number */}
                  <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                    <div className="text-sm text-orange-600 dark:text-orange-400 mb-1">
                      FIRE Number
                    </div>
                    <div className="text-2xl font-bold text-orange-700 dark:text-orange-300">
                      {formatCurrency(fire.metrics.fire_number, "USD")}
                    </div>
                  </div>

                  {/* Progress */}
                  <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
                      Progress
                    </div>
                    <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                      {fire.metrics.progress_percentage.toFixed(1)}%
                    </div>
                    <div className="w-full h-2 bg-blue-200 dark:bg-blue-800 rounded-full mt-2">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{
                          width: `${Math.min(fire.metrics.progress_percentage, 100)}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Years to FIRE */}
                  <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="text-sm text-green-600 dark:text-green-400 mb-1">
                      Years to FIRE
                    </div>
                    <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                      {formatYears(fire.metrics.years_to_fire)}
                    </div>
                    {fire.metrics.fire_date && (
                      <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                        Target: {new Date(fire.metrics.fire_date).getFullYear()}
                      </div>
                    )}
                  </div>

                  {/* Monthly Income at FIRE */}
                  <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                      Monthly at FIRE
                    </div>
                    <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                      {formatCurrency(
                        fire.metrics.monthly_income_at_fire,
                        "USD",
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Projection Chart */}
              {fire && projectionData.length > 0 && (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={projectionData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        className="stroke-gray-200 dark:stroke-gray-700"
                      />
                      <XAxis
                        dataKey="year"
                        tickFormatter={(year) => `${year}y`}
                        className="text-gray-600 dark:text-gray-400"
                      />
                      <YAxis
                        tickFormatter={(value) =>
                          `$${(value / 1000000).toFixed(1)}M`
                        }
                        className="text-gray-600 dark:text-gray-400"
                      />
                      <Tooltip
                        formatter={(value: number) => [
                          formatCurrency(value, "USD"),
                          "",
                        ]}
                        labelFormatter={(year) => `Year ${year}`}
                      />
                      <Area
                        type="monotone"
                        dataKey="net_worth"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.2}
                        name="Net Worth"
                      />
                      <Area
                        type="monotone"
                        dataKey="contributions"
                        stroke="#10b981"
                        fill="#10b981"
                        fillOpacity={0.1}
                        name="Contributions"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* What-If Scenarios */}
              {showFIREDetails && fire && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    What-If Scenarios
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {fire.scenarios.slice(1).map((scenario) => (
                      <div
                        key={scenario.name}
                        className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                      >
                        <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {scenario.name}
                        </div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white">
                          {formatYears(scenario.years_to_fire)}
                        </div>
                        {scenario.difference_years !== null && (
                          <div
                            className={`text-xs ${
                              scenario.difference_years < 0
                                ? "text-green-600"
                                : "text-red-600"
                            }`}
                          >
                            {scenario.difference_years < 0 ? "" : "+"}
                            {scenario.difference_years?.toFixed(1)} years vs
                            baseline
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Growth Metrics */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-blue-500" />
                Growth Metrics
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    Avg Monthly
                  </div>
                  <div
                    className={`text-xl font-bold ${
                      insights.growth.average_monthly >= 0
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {formatPercent(insights.growth.average_monthly)}
                  </div>
                </div>
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    Annualized
                  </div>
                  <div
                    className={`text-xl font-bold ${
                      insights.growth.yearly_rate >= 0
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {formatPercent(insights.growth.yearly_rate)}
                  </div>
                </div>
                <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-sm text-green-600 dark:text-green-400 mb-1">
                    Best Month
                  </div>
                  <div className="text-xl font-bold text-green-700 dark:text-green-300">
                    {formatPercent(insights.growth.best_month_return)}
                  </div>
                </div>
                <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div className="text-sm text-red-600 dark:text-red-400 mb-1">
                    Worst Month
                  </div>
                  <div className="text-xl font-bold text-red-700 dark:text-red-300">
                    {formatPercent(insights.growth.worst_month_return)}
                  </div>
                </div>
              </div>
            </div>

            {/* Asset Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* By Institution */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  By Institution
                </h2>
                <div className="space-y-2">
                  {Object.entries(insights.allocation.by_institution)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 8)
                    .map(([name, value], index) => (
                      <div key={name} className="flex items-center">
                        <span className="w-32 text-sm text-gray-700 dark:text-gray-300 truncate">
                          {name}
                        </span>
                        <div className="flex-1 mx-3">
                          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${value}%`,
                                backgroundColor: COLORS[index % COLORS.length],
                              }}
                            />
                          </div>
                        </div>
                        <span className="w-12 text-sm text-right text-gray-600 dark:text-gray-400">
                          {value.toFixed(1)}%
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {/* By Country */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  By Country
                </h2>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={Object.entries(insights.allocation.by_country).map(
                        ([name, value]) => ({
                          name:
                            name === "CA"
                              ? "🇨🇦 Canada"
                              : name === "US"
                                ? "🇺🇸 USA"
                                : name === "BR"
                                  ? "🇧🇷 Brazil"
                                  : name,
                          value: Number(value.toFixed(1)),
                        }),
                      )}
                      layout="vertical"
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        className="stroke-gray-200 dark:stroke-gray-700"
                      />
                      <XAxis type="number" tickFormatter={(v) => `${v}%`} />
                      <YAxis dataKey="name" type="category" width={100} />
                      <Tooltip formatter={(value: number) => `${value}%`} />
                      <Bar
                        dataKey="value"
                        fill="#3b82f6"
                        radius={[0, 4, 4, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500 dark:text-gray-400 py-12">
            No data available. Please seed the database first.
          </div>
        )}
      </main>
    </div>
  );
}
