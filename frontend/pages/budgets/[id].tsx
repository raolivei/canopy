import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import Link from "next/link";
import PageLayout from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { SkeletonChart, SkeletonList } from "@/components/ui/Skeleton";
import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { format, addMonths, subMonths, startOfMonth, endOfMonth } from "date-fns";
import BudgetSummary from "@/components/BudgetSummary";
import BudgetVsActualsChart from "@/components/BudgetVsActualsChart";
import BudgetVsActualsTable from "@/components/BudgetVsActualsTable";
import { motion } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface BudgetMetadata {
  id: number;
  name: string;
  currency: string;
  description: string | null;
  is_active: boolean;
}

interface BudgetCategory {
  id: number;
  category_name: string;
  limit_amount: number;
  actual_spent: number;
  variance: number;
  variance_pct: number;
  percent_used: number;
  is_over_budget: boolean;
}

interface BudgetSummaryData {
  total_limit: number;
  total_actual: number;
  total_variance: number;
  variance_pct: number;
  percent_used: number;
  is_over_budget: boolean;
}

interface BudgetTrackingData {
  budget: BudgetMetadata;
  period_start: string;
  period_end: string;
  categories: BudgetCategory[];
  summary: BudgetSummaryData;
}

export default function BudgetDetailPage() {
  const router = useRouter();
  const { id } = router.query;

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<BudgetTrackingData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const startDate = useMemo(() => startOfMonth(currentMonth), [currentMonth]);
  const endDate = useMemo(() => endOfMonth(currentMonth), [currentMonth]);

  useEffect(() => {
    if (!id) return;

    const fetchBudgetTracking = async () => {
      setLoading(true);
      setError(null);
      try {
        const start = startDate.toISOString().split("T")[0];
        const end = endDate.toISOString().split("T")[0];
        const url = `${API_URL}/v1/budgets/${id}/tracking?start_date=${start}T00:00:00Z&end_date=${end}T23:59:59Z`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to load budget: ${response.statusText}`);
        }

        const trackingData: BudgetTrackingData = await response.json();
        setData(trackingData);
      } catch (e) {
        console.error(e);
        setError(e instanceof Error ? e.message : "Failed to load budget tracking data");
      } finally {
        setLoading(false);
      }
    };

    fetchBudgetTracking();
  }, [id, startDate, endDate]);

  const handlePreviousMonth = () => {
    setCurrentMonth((prev) => subMonths(prev, 1));
  };

  const handleNextMonth = () => {
    setCurrentMonth((prev) => addMonths(prev, 1));
  };

  const handleToday = () => {
    setCurrentMonth(new Date());
  };

  if (!id) {
    return (
      <PageLayout title="Loading...">
        <SkeletonList />
      </PageLayout>
    );
  }

  return (
    <>
      <Head>
        <title>{data?.budget.name || "Budget"} — Canopy</title>
      </Head>
      <PageLayout title="Budget Tracking">
        {/* Header with navigation */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-4">
            <Link href="/budgets">
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<ArrowLeft className="w-4 h-4" />}
              >
                Back to budgets
              </Button>
            </Link>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-semibold text-slate-900 dark:text-white">
                {data?.budget.name || "Budget"}
              </h1>
              {data?.budget.description && (
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {data.budget.description}
                </p>
              )}
            </div>
          </div>
        </motion.div>

        {/* Month Selector */}
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="mb-8"
        >
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center justify-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handlePreviousMonth}
                  leftIcon={<ChevronLeft className="w-4 h-4" />}
                  aria-label="Previous month"
                >
                  <span className="sr-only">Previous</span>
                </Button>

                <div className="text-center min-w-[200px]">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    {format(currentMonth, "MMMM yyyy")}
                  </h3>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNextMonth}
                  rightIcon={<ChevronRight className="w-4 h-4" />}
                  aria-label="Next month"
                >
                  <span className="sr-only">Next</span>
                </Button>

                <Button variant="secondary" size="sm" onClick={handleToday}>
                  Today
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-danger-50 dark:bg-danger-950/30 border border-danger-200 dark:border-danger-800 rounded-lg text-sm text-danger-700 dark:text-danger-400"
          >
            {error}
          </motion.div>
        )}

        {loading ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <SkeletonChart />
              <SkeletonChart />
              <SkeletonChart />
              <SkeletonChart />
            </div>
            <div className="mb-8">
              <SkeletonChart />
            </div>
            <SkeletonList />
          </>
        ) : data ? (
          <>
            {/* Summary Cards */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mb-8"
            >
              <BudgetSummary
                totalBudget={data.summary.total_limit}
                totalActual={data.summary.total_actual}
                variance={data.summary.total_variance}
                percentUsed={data.summary.percent_used}
                isOverBudget={data.summary.is_over_budget}
                currency={data.budget.currency}
              />
            </motion.div>

            {/* Chart */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="mb-8"
            >
              <Card>
                <CardHeader>
                  <CardTitle>Budget vs Actual by Category</CardTitle>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Blue bars show budget limits, green bars show actual spending
                  </p>
                </CardHeader>
                <CardContent>
                  <BudgetVsActualsChart
                    data={data.categories}
                    currency={data.budget.currency}
                  />
                </CardContent>
              </Card>
            </motion.div>

            {/* Table */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Category Details</CardTitle>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Detailed breakdown of each category vs its budget limit
                  </p>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                  <BudgetVsActualsTable
                    data={data.categories}
                    totalBudget={data.summary.total_limit}
                    totalActual={data.summary.total_actual}
                    totalVariance={data.summary.total_variance}
                    currency={data.budget.currency}
                  />
                </CardContent>
              </Card>
            </motion.div>
          </>
        ) : null}
      </PageLayout>
    </>
  );
}
