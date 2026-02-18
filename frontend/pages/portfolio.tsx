import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge, CurrencyBadge } from "@/components/ui/Badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { Select } from "@/components/ui/Select";
import { SkeletonMetricCard, SkeletonTable } from "@/components/ui/Skeleton";
import PortfolioHoldingsTable from "@/components/PortfolioHoldingsTable";
import AddAssetModal from "@/components/AddAssetModal";
import AllocationChart from "@/components/AllocationChart";
import DividendHistory from "@/components/DividendHistory";
import PerformanceChart from "@/components/PerformanceChart";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  Plus,
  RefreshCw,
  Loader2,
  BarChart3,
  Briefcase,
  Calendar,
} from "lucide-react";
import { formatCurrency } from "@/utils/currency";
import { cn } from "@/utils/cn";
import { motion } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

const EXCHANGE_RATES: Record<string, Record<string, number>> = {
  USD: { USD: 1, CAD: 1.35, BRL: 5.0, BTC: 0.000016, ETH: 0.00035 },
  CAD: { USD: 0.74, CAD: 1, BRL: 3.7, BTC: 0.000012, ETH: 0.00026 },
  BRL: { USD: 0.2, CAD: 0.27, BRL: 1, BTC: 0.0000032, ETH: 0.00007 },
};

interface PortfolioSummary {
  total_value: number | null;
  total_cost_basis: number;
  total_gain_loss: number | null;
  total_return_pct: number | null;
  total_dividends: number;
  holdings_count: number;
  holdings: any[];
}

interface Allocation {
  by_asset_type: any[];
  total_value: number;
}

interface Performance {
  period: string;
  data_points: any[];
  start_value: number | null;
  end_value: number | null;
  period_return: number | null;
  period_return_pct: number | null;
}

export default function Portfolio() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("holdings");
  const [performancePeriod, setPerformancePeriod] = useState("30d");
  const [displayCurrency, setDisplayCurrency] = useState("CAD");
  const [currencyFilter, setCurrencyFilter] = useState<string>("all");
  const queryClient = useQueryClient();

  const convertToDisplay = (value: number | string | null, fromCurrency: string): number => {
    if (value === null) return 0;
    const numValue = Number(value);
    if (fromCurrency === displayCurrency) return numValue;

    if (fromCurrency === "BTC") {
      const btcToUsd = numValue * 62000;
      return convertToDisplay(btcToUsd, "USD");
    }
    if (fromCurrency === "ETH") {
      const ethToUsd = numValue * 2400;
      return convertToDisplay(ethToUsd, "USD");
    }

    const rates = EXCHANGE_RATES[fromCurrency];
    if (!rates) return numValue;
    return numValue * (rates[displayCurrency] || 1);
  };

  const { data: summary, isLoading: summaryLoading } = useQuery<PortfolioSummary>({
    queryKey: ["portfolio-summary"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/summary`);
      if (!res.ok) throw new Error("Failed to fetch portfolio summary");
      return res.json();
    },
  });

  const { data: allocation } = useQuery<Allocation>({
    queryKey: ["portfolio-allocation"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/allocation`);
      if (!res.ok) throw new Error("Failed to fetch allocation");
      return res.json();
    },
  });

  const { data: dividends } = useQuery<any[]>({
    queryKey: ["portfolio-dividends"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/dividends`);
      if (!res.ok) throw new Error("Failed to fetch dividends");
      return res.json();
    },
  });

  const { data: performance } = useQuery<Performance>({
    queryKey: ["portfolio-performance", performancePeriod],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/performance?period=${performancePeriod}`);
      if (!res.ok) throw new Error("Failed to fetch performance");
      return res.json();
    },
  });

  const refreshPrices = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/prices/refresh`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to refresh prices");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio-allocation"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio-performance"] });
    },
  });

  const createSnapshot = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/snapshots/create`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to create snapshot");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio-performance"] });
    },
  });

  const addAsset = useMutation({
    mutationFn: async (data: any) => {
      const assetRes = await fetch(`${API_URL}/v1/portfolio/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: data.symbol,
          name: data.name,
          asset_type: data.asset_type,
          currency: data.currency,
        }),
      });

      if (!assetRes.ok) {
        const err = await assetRes.json();
        throw new Error(err.detail || "Failed to create asset");
      }

      const asset = await assetRes.json();

      const lotRes = await fetch(`${API_URL}/v1/portfolio/lots`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_id: asset.id,
          quantity: data.quantity,
          price_per_unit: data.price_per_unit,
          fees: 0,
          purchase_date: data.purchase_date,
          account: data.account,
        }),
      });

      if (!lotRes.ok) throw new Error("Failed to create lot");
      return asset;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio-allocation"] });
      setIsAddModalOpen(false);
    },
  });

  const processedHoldings = useMemo(() => {
    if (!summary?.holdings) return [];

    let holdings = summary.holdings;
    if (currencyFilter && currencyFilter !== "all") {
      holdings = holdings.filter((h: any) => h.currency === currencyFilter);
    }

    return holdings.map((h: any) => ({
      ...h,
      market_value_converted: convertToDisplay(h.market_value, h.currency),
      cost_basis_converted: convertToDisplay(h.cost_basis, h.currency),
    }));
  }, [summary?.holdings, currencyFilter, displayCurrency]);

  const totalValue = useMemo(() => {
    return processedHoldings.reduce((sum: number, h: any) => sum + (h.market_value_converted || 0), 0);
  }, [processedHoldings]);

  const availableCurrencies = useMemo(() => {
    if (!summary?.holdings) return [];
    const currencies = new Set(summary.holdings.map((h: any) => h.currency));
    return Array.from(currencies).sort();
  }, [summary?.holdings]);

  const currencyOptions = [
    { value: "all", label: "All Currencies" },
    ...availableCurrencies.map((c) => ({ value: c, label: c })),
  ];

  const displayCurrencyOptions = [
    { value: "CAD", label: "CAD" },
    { value: "USD", label: "USD" },
    { value: "BRL", label: "BRL" },
  ];

  if (summaryLoading) {
    return (
      <PageLayout title="Portfolio">
        <PageHeader title="Portfolio" description="Track your investments and assets" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonMetricCard key={i} />
          ))}
        </div>
        <SkeletonTable rows={8} columns={5} />
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Portfolio" description="Track your investments and assets">
      {/* Portfolio Value Hero */}
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
                Total Portfolio Value
                {currencyFilter !== "all" && (
                  <CurrencyBadge currency={currencyFilter} className="ml-2" />
                )}
              </p>
              <h1 className="text-4xl lg:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white mb-2">
                {formatCurrency(totalValue, displayCurrency)}
              </h1>
              <div className="flex items-center gap-3">
                <Badge variant={summary?.total_return_pct && summary.total_return_pct >= 0 ? "success" : "danger"}>
                  {summary?.total_return_pct && summary.total_return_pct >= 0 ? (
                    <TrendingUp className="w-3 h-3 mr-1" />
                  ) : (
                    <TrendingDown className="w-3 h-3 mr-1" />
                  )}
                  {summary?.total_return_pct?.toFixed(2) || 0}% all time
                </Badge>
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {processedHoldings.length} holdings
                </span>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Select
                options={currencyOptions}
                value={currencyFilter}
                onChange={setCurrencyFilter}
                className="w-36"
              />
              <Select
                options={displayCurrencyOptions}
                value={displayCurrency}
                onChange={setDisplayCurrency}
                className="w-24"
              />
              <Button
                variant="secondary"
                leftIcon={createSnapshot.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <PieChart className="w-4 h-4" />}
                onClick={() => createSnapshot.mutate()}
                disabled={createSnapshot.isPending}
              >
                Snapshot
              </Button>
              <Button
                variant="secondary"
                leftIcon={refreshPrices.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                onClick={() => refreshPrices.mutate()}
                disabled={refreshPrices.isPending}
              >
                Refresh
              </Button>
              <Button
                variant="primary"
                leftIcon={<Plus className="w-4 h-4" />}
                onClick={() => setIsAddModalOpen(true)}
              >
                Add Asset
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        <MetricCard
          title="Total Value"
          value={formatCurrency(totalValue, displayCurrency)}
          icon={<Briefcase className="w-5 h-5" />}
          iconBg="bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400"
        />
        <MetricCard
          title="Total Gain/Loss"
          value={summary?.total_gain_loss !== null ? formatCurrency(summary?.total_gain_loss || 0, displayCurrency) : "—"}
          subtitle={summary?.total_gain_loss !== null ? undefined : "No cost basis data"}
          icon={<TrendingUp className="w-5 h-5" />}
          iconBg={cn(
            summary?.total_gain_loss && summary.total_gain_loss >= 0
              ? "bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400"
              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
          )}
        />
        <MetricCard
          title="Total Dividends"
          value={formatCurrency(Number(summary?.total_dividends ?? 0), displayCurrency)}
          icon={<DollarSign className="w-5 h-5" />}
          iconBg="bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400"
        />
        <MetricCard
          title="Holdings"
          value={String(processedHoldings.length)}
          subtitle={currencyFilter !== "all" ? `${currencyFilter} assets` : "assets tracked"}
          icon={<BarChart3 className="w-5 h-5" />}
          iconBg="bg-accent-100 dark:bg-accent-900/30 text-accent-600 dark:text-accent-400"
        />
      </motion.div>

      {/* Tabbed Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <Tabs defaultValue="holdings" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="holdings">Holdings</TabsTrigger>
            <TabsTrigger value="allocation">Allocation</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="dividends">Dividends</TabsTrigger>
          </TabsList>

          <TabsContent value="holdings">
            <Card>
              <CardContent noPadding>
                <PortfolioHoldingsTable
                  holdings={processedHoldings}
                  onSelect={(holding) => console.log("Selected:", holding)}
                  currency={displayCurrency}
                  convertToDisplay={convertToDisplay}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="allocation">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Asset Allocation</CardTitle>
                </CardHeader>
                <CardContent>
                  <AllocationChart
                    data={allocation?.by_asset_type || []}
                    totalValue={totalValue}
                    currency={displayCurrency}
                  />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Allocation by Currency</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {availableCurrencies.map((currency) => {
                      const currencyHoldings = summary?.holdings?.filter((h: any) => h.currency === currency) || [];
                      const currencyTotal = currencyHoldings.reduce(
                        (sum: number, h: any) => sum + convertToDisplay(h.market_value, h.currency),
                        0
                      );
                      const percentage = totalValue > 0 ? (currencyTotal / totalValue) * 100 : 0;

                      return (
                        <div key={currency} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <CurrencyBadge currency={currency} />
                              <span className="text-slate-600 dark:text-slate-400">
                                {currencyHoldings.length} holdings
                              </span>
                            </div>
                            <span className="font-medium text-slate-900 dark:text-white">
                              {formatCurrency(currencyTotal, displayCurrency)}
                            </span>
                          </div>
                          <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary-500 rounded-full transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            {percentage.toFixed(1)}% of portfolio
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="performance">
            <Card>
              <CardContent className="p-0">
                <PerformanceChart
                  data={performance?.data_points || []}
                  onPeriodChange={(period) => setPerformancePeriod(period)}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dividends">
            <Card>
              <CardContent className="p-0">
                <DividendHistory dividends={dividends || []} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>

      <AddAssetModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={(data) => addAsset.mutate(data)}
        apiUrl={API_URL}
      />
    </PageLayout>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  iconBg: string;
}

function MetricCard({ title, value, subtitle, icon, iconBg }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className={cn("p-2 rounded-lg", iconBg)}>{icon}</div>
        </div>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">{title}</p>
        <p className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
          {value}
        </p>
        {subtitle && (
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}
