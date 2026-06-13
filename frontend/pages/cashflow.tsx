import React, { useState, useMemo } from "react";
import Head from "next/head";
import { useQuery } from "@tanstack/react-query";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/Button";
import CashflowSummary from "@/components/CashflowSummary";
import IncomeExpenseTrend from "@/components/IncomeExpenseTrend";
import SavingsRateTrend from "@/components/SavingsRateTrend";
import CategoryBreakdown from "@/components/CategoryBreakdown";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { Calendar, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";
import { subMonths, endOfToday } from "date-fns";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

interface MonthlyData {
  month: string;
  income: number;
  expenses: number;
  savings: number;
  savings_rate: number;
  categories: Array<{ category: string; amount: number }>;
}

interface CashflowSummaryData {
  total_income: number;
  total_expenses: number;
  total_savings: number;
  average_monthly_savings: number;
  trend: "up" | "down" | "stable";
}

export default function CashflowPage() {
  const [monthsToDisplay, setMonthsToDisplay] = useState(12);
  const displayCurrency = "CAD";

  // Calculate date range for summary
  const endDate = endOfToday();
  const startDate = subMonths(endDate, monthsToDisplay);

  // Fetch cashflow trend
  const {
    data: trendData,
    isLoading: trendLoading,
    error: trendError,
  } = useQuery({
    queryKey: ["cashflow-trend", monthsToDisplay],
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/v1/cashflow/trend?months=${monthsToDisplay}`
      );
      if (!response.ok) throw new Error("Failed to fetch cashflow trend");
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch summary data
  const {
    data: summaryData,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({
    queryKey: ["cashflow-summary", startDate, endDate],
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/v1/cashflow/summary?start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}`
      );
      if (!response.ok) throw new Error("Failed to fetch cashflow summary");
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Prepare chart data
  const monthlyData = useMemo(() => {
    if (!trendData?.months) return [];
    return trendData.months;
  }, [trendData]);

  // Get top categories from the latest month
  const latestCategories = useMemo(() => {
    if (!monthlyData || monthlyData.length === 0) return [];
    return monthlyData[monthlyData.length - 1]?.categories || [];
  }, [monthlyData]);

  // Error states
  const hasError = trendError || summaryError;

  const handleMonthsChange = (months: number) => {
    setMonthsToDisplay(months);
  };

  return (
    <>
      <Head>
        <title>Cashflow — Canopy</title>
      </Head>
      <PageLayout>
        <PageHeader
          title="Cashflow Analysis"
          description="Track your income, expenses, and savings trends"
        />

        {hasError && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3"
          >
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-800 dark:text-red-200">
              Failed to load cashflow data. Please try again.
            </p>
          </motion.div>
        )}

        {/* Summary Cards */}
        {summaryData && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-6"
          >
            <CashflowSummary
              data={summaryData}
              isLoading={summaryLoading}
              currency={displayCurrency}
            />
          </motion.div>
        )}

        {/* Period Controls */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6 flex items-center gap-2 flex-wrap"
        >
          <Calendar className="h-5 w-5 text-slate-500" />
          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
            Time Period:
          </span>
          <div className="flex gap-2">
            {[3, 6, 12, 24].map((months) => (
              <Button
                key={months}
                variant={monthsToDisplay === months ? "primary" : "ghost"}
                size="sm"
                onClick={() => handleMonthsChange(months)}
              >
                {months}M
              </Button>
            ))}
          </div>
        </motion.div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Income vs Expenses */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            {trendLoading ? (
              <SkeletonChart />
            ) : (
              <IncomeExpenseTrend
                data={monthlyData}
                isLoading={trendLoading}
                currency={displayCurrency}
              />
            )}
          </motion.div>

          {/* Savings Rate */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {trendLoading ? (
              <SkeletonChart />
            ) : (
              <SavingsRateTrend
                data={monthlyData}
                isLoading={trendLoading}
              />
            )}
          </motion.div>
        </div>

        {/* Category Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          {trendLoading ? (
            <SkeletonChart />
          ) : (
            <CategoryBreakdown
              data={latestCategories}
              isLoading={trendLoading}
              currency={displayCurrency}
              title="Current Month - Top Expense Categories"
            />
          )}
        </motion.div>
      </PageLayout>
    </>
  );
}
