import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PiggyBank,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { formatCurrency } from "@/utils/currency";
import { cn } from "@/utils/cn";

interface CashflowSummaryData {
  total_income: number;
  total_expenses: number;
  total_savings: number;
  average_monthly_savings: number;
  trend: "up" | "down" | "stable";
}

interface CashflowSummaryProps {
  data: CashflowSummaryData;
  isLoading?: boolean;
  currency?: string;
}

export default function CashflowSummary({
  data,
  isLoading = false,
  currency = "CAD",
}: CashflowSummaryProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse h-8 bg-slate-200 dark:bg-slate-700 rounded mb-2"></div>
              <div className="animate-pulse h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const savingsRate =
    data.total_income > 0
      ? ((data.total_savings / data.total_income) * 100).toFixed(1)
      : 0;

  const isSavingsPositive = data.total_savings >= 0;
  const isTrendUp = data.trend === "up";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* Total Income */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Total Income
            </CardTitle>
            <ArrowUpRight className="h-4 w-4 text-green-500" />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {formatCurrency(data.total_income, currency)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            All-time total
          </p>
        </CardContent>
      </Card>

      {/* Total Expenses */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Total Expenses
            </CardTitle>
            <ArrowDownRight className="h-4 w-4 text-red-500" />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {formatCurrency(data.total_expenses, currency)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            All-time total
          </p>
        </CardContent>
      </Card>

      {/* Total Savings */}
      <Card
        className={cn(
          isSavingsPositive
            ? "border-green-500/50 dark:border-green-500/50"
            : "border-red-500/50 dark:border-red-500/50"
        )}
      >
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Total Savings
            </CardTitle>
            <PiggyBank
              className={cn(
                "h-4 w-4",
                isSavingsPositive ? "text-green-500" : "text-red-500"
              )}
            />
          </div>
        </CardHeader>
        <CardContent>
          <p
            className={cn(
              "text-2xl font-bold",
              isSavingsPositive
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            )}
          >
            {formatCurrency(data.total_savings, currency)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            {savingsRate}% of income
          </p>
        </CardContent>
      </Card>

      {/* Average Monthly Savings */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Monthly Avg.
            </CardTitle>
            <DollarSign className="h-4 w-4 text-slate-400" />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {formatCurrency(data.average_monthly_savings, currency)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            Average per month
          </p>
        </CardContent>
      </Card>

      {/* Trend Indicator */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Savings Trend
            </CardTitle>
            {isTrendUp ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : data.trend === "down" ? (
              <TrendingDown className="h-4 w-4 text-red-500" />
            ) : (
              <div className="h-4 w-4 text-slate-400">→</div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <p
            className={cn(
              "text-2xl font-bold capitalize",
              isTrendUp
                ? "text-green-600 dark:text-green-400"
                : data.trend === "down"
                  ? "text-red-600 dark:text-red-400"
                  : "text-slate-600 dark:text-slate-400"
            )}
          >
            {data.trend}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            vs. previous period
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
