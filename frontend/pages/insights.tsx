import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { SkeletonMetricCard, SkeletonChart } from "@/components/ui/Skeleton";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  PieChart,
  Globe,
  Calendar,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
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
  BarChart,
  Bar,
} from "recharts";
import { motion } from "framer-motion";
import { cn } from "@/utils/cn";
import {
  CHART_PALETTE,
  CHART_COLORS,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

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

function formatCurrency(value: number | null, currency: string = "USD"): string {
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

const COLORS = [...CHART_PALETTE];

const CURRENCY_FLAGS: Record<string, string> = {
  CAD: "🇨🇦",
  USD: "🇺🇸",
  BRL: "🇧🇷",
  EUR: "🇪🇺",
  Crypto: "₿",
};

export default function Insights() {
  const [baseCurrency, setBaseCurrency] = useState<"USD" | "CAD" | "BRL" | "EUR">("USD");
  const [monthlyExpenses, setMonthlyExpenses] = useState(5000);
  const [monthlySavings, setMonthlySavings] = useState(2000);
  const [expenseCurrency, setExpenseCurrency] = useState("CAD");
  const [showFIREDetails, setShowFIREDetails] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  const { data: insights, isLoading: insightsLoading } = useQuery<InsightsSummary>({
    queryKey: ["insights-summary", baseCurrency],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/insights/summary?base_currency=${baseCurrency}`);
      if (!res.ok) throw new Error("Failed to fetch insights");
      return res.json();
    },
  });

  const { data: fire, isLoading: fireLoading } = useQuery<FIRESummary>({
    queryKey: ["fire-summary", monthlyExpenses, monthlySavings, expenseCurrency],
    queryFn: async () => {
      const res = await fetch(
        `${API_URL}/v1/insights/fire?monthly_expenses=${monthlyExpenses}&monthly_savings=${monthlySavings}&currency=${expenseCurrency}`
      );
      if (!res.ok) throw new Error("Failed to fetch FIRE data");
      return res.json();
    },
  });

  const allocationByType = insights?.allocation.by_type
    ? Object.entries(insights.allocation.by_type).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: Number(value.toFixed(1)),
      }))
    : [];

  const currencyExposure = insights?.currency_exposure.exposures
    ? Object.entries(insights.currency_exposure.exposures).map(([name, value]) => ({
        name,
        value: Number(value.toFixed(1)),
        amount: insights.currency_exposure.amounts_usd[name] || 0,
      }))
    : [];

  const projectionData =
    fire?.projections.filter((_, i) => i % 5 === 0 || i === fire.projections.length - 1) || [];

  const currencyOptions = [
    { value: "USD", label: "USD" },
    { value: "CAD", label: "CAD" },
    { value: "BRL", label: "BRL" },
    { value: "EUR", label: "EUR" },
  ];

  if (insightsLoading) {
    return (
      <PageLayout title="Insights">
        <PageHeader title="Insights" description="Financial overview, projections, and FIRE planning" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonMetricCard key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonChart className="h-80" />
          <SkeletonChart className="h-80" />
        </div>
      </PageLayout>
    );
  }

  if (!insights) {
    return (
      <PageLayout title="Insights">
        <PageHeader title="Insights" description="Financial overview, projections, and FIRE planning" />
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-slate-500 dark:text-slate-400">
              No data available. Please add some transactions or portfolio holdings first.
            </p>
          </CardContent>
        </Card>
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Insights" description="Financial overview, projections, and FIRE planning">
      <PageHeader
        title="Insights"
        description="Financial overview, projections, and FIRE planning"
        actions={
          <div className="flex items-center gap-2">
            {(["USD", "CAD", "BRL", "EUR"] as const).map((curr) => (
              <button
                key={curr}
                onClick={() => setBaseCurrency(curr)}
                className={cn(
                  "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  baseCurrency === curr
                    ? "bg-primary-100 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                )}
              >
                {curr}
              </button>
            ))}
          </div>
        }
      />

      {/* Net Worth Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <Card variant="highlight" className="overflow-hidden">
          <div className="relative p-8">
            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary-500/10 to-transparent rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="relative">
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 mb-2">
                <Sparkles className="w-4 h-4" />
                Net Worth
              </div>
              <div className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
                {formatCurrency(insights.net_worth.total_usd, baseCurrency)}
              </div>
              <div className="flex items-center gap-6">
                {insights.net_worth.change_1m_percent !== null && (
                  <div
                    className={cn(
                      "flex items-center text-sm",
                      insights.net_worth.change_1m_percent >= 0
                        ? "text-success-600 dark:text-success-400"
                        : "text-danger-600 dark:text-danger-400"
                    )}
                  >
                    {insights.net_worth.change_1m_percent >= 0 ? (
                      <ArrowUpRight className="w-4 h-4 mr-1" />
                    ) : (
                      <ArrowDownRight className="w-4 h-4 mr-1" />
                    )}
                    {formatPercent(insights.net_worth.change_1m_percent)} (30d)
                  </div>
                )}
                {insights.net_worth.change_ytd_percent !== null && (
                  <div
                    className={cn(
                      "flex items-center text-sm",
                      insights.net_worth.change_ytd_percent >= 0
                        ? "text-success-600 dark:text-success-400"
                        : "text-danger-600 dark:text-danger-400"
                    )}
                  >
                    {insights.net_worth.change_ytd_percent >= 0 ? (
                      <ArrowUpRight className="w-4 h-4 mr-1" />
                    ) : (
                      <ArrowDownRight className="w-4 h-4 mr-1" />
                    )}
                    {formatPercent(insights.net_worth.change_ytd_percent)} YTD
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Quick Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
      >
        <MetricCard
          title="Total Assets"
          value={formatCurrency(insights.net_worth.total_assets_usd, baseCurrency)}
          icon={TrendingUp}
          iconColor="text-success-500"
          subtitle={`${Object.keys(insights.net_worth.assets_by_currency).length} currencies`}
        />
        <MetricCard
          title="Total Liabilities"
          value={formatCurrency(insights.net_worth.total_liabilities_usd, baseCurrency)}
          icon={TrendingDown}
          iconColor="text-danger-500"
          subtitle={`${Object.keys(insights.net_worth.liabilities_by_currency).length} accounts`}
        />
        <MetricCard
          title="YTD Change"
          value={formatPercent(insights.net_worth.change_ytd_percent)}
          valueColor={
            (insights.net_worth.change_ytd_percent || 0) >= 0 ? "text-success-600" : "text-danger-600"
          }
          icon={Calendar}
          iconColor="text-accent-500"
          subtitle={formatCurrency(insights.net_worth.change_ytd, baseCurrency)}
        />
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="fire">FIRE Calculator</TabsTrigger>
            <TabsTrigger value="growth">Growth</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Asset Allocation */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <PieChart className="w-5 h-5 text-primary-500" />
                    <CardTitle>Asset Allocation</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Pie
                          data={allocationByType}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value}%`}
                        >
                          {allocationByType.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={getTooltipStyle(checkDarkMode())}
                          formatter={(value: number) => `${value}%`}
                        />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Currency Exposure */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-5 h-5 text-success-500" />
                      <CardTitle>Currency Exposure</CardTitle>
                    </div>
                    <Badge
                      variant={
                        insights.currency_exposure.risk_assessment === "diversified"
                          ? "success"
                          : insights.currency_exposure.risk_assessment === "balanced"
                            ? "warning"
                            : "danger"
                      }
                    >
                      {insights.currency_exposure.risk_assessment}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {currencyExposure.map((item, index) => (
                      <div key={item.name} className="flex items-center gap-3">
                        <span className="w-8 text-lg">{CURRENCY_FLAGS[item.name] || "💱"}</span>
                        <span className="w-12 text-sm font-medium text-slate-700 dark:text-slate-300">
                          {item.name}
                        </span>
                        <div className="flex-1">
                          <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all"
                              style={{
                                width: `${item.value}%`,
                                backgroundColor: COLORS[index % COLORS.length],
                              }}
                            />
                          </div>
                        </div>
                        <span className="w-12 text-sm text-right font-medium text-slate-600 dark:text-slate-400">
                          {item.value.toFixed(1)}%
                        </span>
                        <span className="w-20 text-sm text-right text-slate-500 dark:text-slate-500">
                          {formatCurrency(item.amount, "USD")}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* By Institution */}
              <Card>
                <CardHeader>
                  <CardTitle>By Institution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(insights.allocation.by_institution)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 8)
                      .map(([name, value], index) => (
                        <div key={name} className="flex items-center gap-3">
                          <span className="w-28 text-sm text-slate-700 dark:text-slate-300 truncate">
                            {name}
                          </span>
                          <div className="flex-1">
                            <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${value}%`,
                                  backgroundColor: COLORS[index % COLORS.length],
                                }}
                              />
                            </div>
                          </div>
                          <span className="w-12 text-sm text-right font-medium text-slate-600 dark:text-slate-400">
                            {value.toFixed(1)}%
                          </span>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>

              {/* By Country */}
              <Card>
                <CardHeader>
                  <CardTitle>By Country</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={Object.entries(insights.allocation.by_country).map(([name, value]) => ({
                          name:
                            name === "CA"
                              ? "🇨🇦 Canada"
                              : name === "US"
                                ? "🇺🇸 USA"
                                : name === "BR"
                                  ? "🇧🇷 Brazil"
                                  : name,
                          value: Number(value.toFixed(1)),
                        }))}
                        layout="vertical"
                      >
                        <CartesianGrid {...getGridProps(checkDarkMode())} />
                        <XAxis type="number" tickFormatter={(v) => `${v}%`} {...getAxisProps(checkDarkMode())} />
                        <YAxis dataKey="name" type="category" width={100} {...getAxisProps(checkDarkMode())} />
                        <Tooltip
                          contentStyle={getTooltipStyle(checkDarkMode())}
                          formatter={(value: number) => `${value}%`}
                        />
                        <Bar dataKey="value" fill={CHART_COLORS.primary} radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="fire">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-warning-500" />
                    <CardTitle>FIRE Calculator</CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowFIREDetails(!showFIREDetails)}
                  >
                    {showFIREDetails ? "Hide" : "Show"} Details
                    {showFIREDetails ? (
                      <ChevronUp className="w-4 h-4 ml-1" />
                    ) : (
                      <ChevronDown className="w-4 h-4 ml-1" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {showFIREDetails && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Monthly Expenses
                      </label>
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          value={monthlyExpenses}
                          onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                          className="flex-1"
                        />
                        <Select
                          options={[
                            { value: "CAD", label: "CAD" },
                            { value: "USD", label: "USD" },
                            { value: "BRL", label: "BRL" },
                          ]}
                          value={expenseCurrency}
                          onChange={setExpenseCurrency}
                          className="w-24"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Monthly Savings
                      </label>
                      <Input
                        type="number"
                        value={monthlySavings}
                        onChange={(e) => setMonthlySavings(Number(e.target.value))}
                      />
                    </div>
                    <div className="flex items-end">
                      <div className="text-sm text-slate-600 dark:text-slate-400">
                        <div>SWR: {((fire?.metrics.safe_withdrawal_rate || 0.04) * 100).toFixed(0)}%</div>
                        <div>Return: {((fire?.metrics.expected_return || 0.07) * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </div>
                )}

                {fire && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-4 bg-warning-50 dark:bg-warning-900/20 rounded-lg">
                        <div className="text-sm text-warning-600 dark:text-warning-400 mb-1">
                          FIRE Number
                        </div>
                        <div className="text-2xl font-bold text-warning-700 dark:text-warning-300">
                          {formatCurrency(fire.metrics.fire_number, "USD")}
                        </div>
                      </div>
                      <div className="text-center p-4 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                        <div className="text-sm text-primary-600 dark:text-primary-400 mb-1">Progress</div>
                        <div className="text-2xl font-bold text-primary-700 dark:text-primary-300">
                          {fire.metrics.progress_percentage.toFixed(1)}%
                        </div>
                        <div className="w-full h-2 bg-primary-200 dark:bg-primary-800 rounded-full mt-2">
                          <div
                            className="h-full bg-primary-500 rounded-full"
                            style={{
                              width: `${Math.min(fire.metrics.progress_percentage, 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                      <div className="text-center p-4 bg-success-50 dark:bg-success-900/20 rounded-lg">
                        <div className="text-sm text-success-600 dark:text-success-400 mb-1">
                          Years to FIRE
                        </div>
                        <div className="text-2xl font-bold text-success-700 dark:text-success-300">
                          {formatYears(fire.metrics.years_to_fire)}
                        </div>
                        {fire.metrics.fire_date && (
                          <div className="text-xs text-success-600 dark:text-success-400 mt-1">
                            Target: {new Date(fire.metrics.fire_date).getFullYear()}
                          </div>
                        )}
                      </div>
                      <div className="text-center p-4 bg-accent-50 dark:bg-accent-900/20 rounded-lg">
                        <div className="text-sm text-accent-600 dark:text-accent-400 mb-1">
                          Monthly at FIRE
                        </div>
                        <div className="text-2xl font-bold text-accent-700 dark:text-accent-300">
                          {formatCurrency(fire.metrics.monthly_income_at_fire, "USD")}
                        </div>
                      </div>
                    </div>

                    {projectionData.length > 0 && (
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={projectionData}>
                            <CartesianGrid {...getGridProps(checkDarkMode())} />
                            <XAxis
                              dataKey="year"
                              tickFormatter={(year) => `${year}y`}
                              {...getAxisProps(checkDarkMode())}
                            />
                            <YAxis
                              tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
                              {...getAxisProps(checkDarkMode())}
                            />
                            <Tooltip
                              contentStyle={getTooltipStyle(checkDarkMode())}
                              formatter={(value: number) => [formatCurrency(value, "USD"), ""]}
                              labelFormatter={(year) => `Year ${year}`}
                            />
                            <Area
                              type="monotone"
                              dataKey="net_worth"
                              stroke={CHART_COLORS.primary}
                              fill={CHART_COLORS.primary}
                              fillOpacity={0.2}
                              name="Net Worth"
                            />
                            <Area
                              type="monotone"
                              dataKey="contributions"
                              stroke={CHART_COLORS.success}
                              fill={CHART_COLORS.success}
                              fillOpacity={0.1}
                              name="Contributions"
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {showFIREDetails && (
                      <div className="mt-6">
                        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                          What-If Scenarios
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {fire.scenarios.slice(1).map((scenario) => (
                            <div
                              key={scenario.name}
                              className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg"
                            >
                              <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                {scenario.name}
                              </div>
                              <div className="text-lg font-bold text-slate-900 dark:text-white">
                                {formatYears(scenario.years_to_fire)}
                              </div>
                              {scenario.difference_years !== null && (
                                <div
                                  className={cn(
                                    "text-xs",
                                    scenario.difference_years < 0
                                      ? "text-success-600"
                                      : "text-danger-600"
                                  )}
                                >
                                  {scenario.difference_years < 0 ? "" : "+"}
                                  {scenario.difference_years?.toFixed(1)} years vs baseline
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="growth">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary-500" />
                  <CardTitle>Growth Metrics</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                    <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Avg Monthly</div>
                    <div
                      className={cn(
                        "text-xl font-bold",
                        insights.growth.average_monthly >= 0
                          ? "text-success-600 dark:text-success-400"
                          : "text-danger-600 dark:text-danger-400"
                      )}
                    >
                      {formatPercent(insights.growth.average_monthly)}
                    </div>
                  </div>
                  <div className="text-center p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                    <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Annualized</div>
                    <div
                      className={cn(
                        "text-xl font-bold",
                        insights.growth.yearly_rate >= 0
                          ? "text-success-600 dark:text-success-400"
                          : "text-danger-600 dark:text-danger-400"
                      )}
                    >
                      {formatPercent(insights.growth.yearly_rate)}
                    </div>
                  </div>
                  <div className="text-center p-4 bg-success-50 dark:bg-success-900/20 rounded-lg">
                    <div className="text-sm text-success-600 dark:text-success-400 mb-1">Best Month</div>
                    <div className="text-xl font-bold text-success-700 dark:text-success-300">
                      {formatPercent(insights.growth.best_month_return)}
                    </div>
                  </div>
                  <div className="text-center p-4 bg-danger-50 dark:bg-danger-900/20 rounded-lg">
                    <div className="text-sm text-danger-600 dark:text-danger-400 mb-1">Worst Month</div>
                    <div className="text-xl font-bold text-danger-700 dark:text-danger-300">
                      {formatPercent(insights.growth.worst_month_return)}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </PageLayout>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  iconColor?: string;
  valueColor?: string;
  subtitle?: string;
}

function MetricCard({
  title,
  value,
  icon: Icon,
  iconColor = "text-slate-500",
  valueColor = "text-slate-900 dark:text-white",
  subtitle,
}: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-slate-500 dark:text-slate-400">{title}</span>
          <Icon className={cn("w-5 h-5", iconColor)} />
        </div>
        <div className={cn("text-2xl font-bold", valueColor)}>{value}</div>
        {subtitle && (
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}
