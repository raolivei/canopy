import React, { useState } from "react";
import Head from "next/head";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Sidebar from "../components/Sidebar";
import DarkModeToggle from "../components/DarkModeToggle";
import PortfolioHoldingsTable from "../components/PortfolioHoldingsTable";
import AddAssetModal from "../components/AddAssetModal";
import AllocationChart from "../components/AllocationChart";
import DividendHistory from "../components/DividendHistory";
import PerformanceChart from "../components/PerformanceChart";
import { TrendingUp, TrendingDown, DollarSign, PieChart, Plus, RefreshCw, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

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

function formatCurrency(value: number | null, currency: string = "USD"): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number | null): string {
  if (value === null) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export default function Portfolio() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [performancePeriod, setPerformancePeriod] = useState("30d");
  const queryClient = useQueryClient();

  // Fetch portfolio summary
  const { data: summary, isLoading: summaryLoading } = useQuery<PortfolioSummary>({
    queryKey: ["portfolio-summary"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/summary`);
      if (!res.ok) throw new Error("Failed to fetch portfolio summary");
      return res.json();
    },
  });

  // Fetch allocation
  const { data: allocation } = useQuery<Allocation>({
    queryKey: ["portfolio-allocation"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/allocation`);
      if (!res.ok) throw new Error("Failed to fetch allocation");
      return res.json();
    },
  });

  // Fetch dividends
  const { data: dividends } = useQuery<any[]>({
    queryKey: ["portfolio-dividends"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/dividends`);
      if (!res.ok) throw new Error("Failed to fetch dividends");
      return res.json();
    },
  });

  // Fetch performance data
  const { data: performance } = useQuery<Performance>({
    queryKey: ["portfolio-performance", performancePeriod],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/performance?period=${performancePeriod}`);
      if (!res.ok) throw new Error("Failed to fetch performance");
      return res.json();
    },
  });

  // Refresh prices mutation
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

  // Create snapshot mutation
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

  // Add asset mutation
  const addAsset = useMutation({
    mutationFn: async (data: any) => {
      // First create the asset
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
      
      // Then create the lot
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

  const isPositive = summary?.total_gain_loss !== null && (summary?.total_gain_loss ?? 0) > 0;
  const isNegative = summary?.total_gain_loss !== null && (summary?.total_gain_loss ?? 0) < 0;

  return (
    <>
      <Head>
        <title>Portfolio - Canopy</title>
      </Head>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950">
        <Sidebar />
        <div className="ml-64 flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  Portfolio
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                  Track your investments and assets
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => createSnapshot.mutate()}
                  disabled={createSnapshot.isPending}
                  className="flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                  title="Create a snapshot of current portfolio value"
                >
                  {createSnapshot.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <PieChart className="w-4 h-4" />
                  )}
                  Snapshot
                </button>
                <button
                  onClick={() => refreshPrices.mutate()}
                  disabled={refreshPrices.isPending}
                  className="flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                >
                  {refreshPrices.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  Refresh Prices
                </button>
                <button
                  onClick={() => setIsAddModalOpen(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Add Asset
                </button>
                <DarkModeToggle />
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Total Portfolio Value
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                      {summaryLoading ? "..." : formatCurrency(summary?.total_value ?? null)}
                    </p>
                  </div>
                  <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-xl">
                    <TrendingUp className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Total Gain/Loss
                    </p>
                    <p className={`text-2xl font-bold mt-2 ${
                      isPositive ? "text-green-600 dark:text-green-400" :
                      isNegative ? "text-red-600 dark:text-red-400" :
                      "text-gray-900 dark:text-white"
                    }`}>
                      {summaryLoading ? "..." : formatCurrency(summary?.total_gain_loss ?? null)}
                    </p>
                    <p className={`text-sm ${
                      isPositive ? "text-green-600 dark:text-green-400" :
                      isNegative ? "text-red-600 dark:text-red-400" :
                      "text-gray-500"
                    }`}>
                      {formatPercent(summary?.total_return_pct ?? null)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-xl ${
                    isPositive ? "bg-green-100 dark:bg-green-900/30" :
                    isNegative ? "bg-red-100 dark:bg-red-900/30" :
                    "bg-gray-100 dark:bg-gray-800"
                  }`}>
                    {isPositive ? (
                      <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
                    ) : isNegative ? (
                      <TrendingDown className="w-6 h-6 text-red-600 dark:text-red-400" />
                    ) : (
                      <TrendingUp className="w-6 h-6 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Total Dividends
                    </p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
                      {summaryLoading ? "..." : formatCurrency(summary?.total_dividends ?? 0)}
                    </p>
                  </div>
                  <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-xl">
                    <DollarSign className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Holdings
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                      {summaryLoading ? "..." : summary?.holdings_count ?? 0}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      assets tracked
                    </p>
                  </div>
                  <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
                    <PieChart className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Holdings Table - spans 2 columns */}
              <div className="lg:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Holdings
                  </h2>
                </div>
                <PortfolioHoldingsTable
                  holdings={summary?.holdings || []}
                  onSelect={(holding) => console.log("Selected:", holding)}
                />
              </div>

              {/* Allocation Chart */}
              <div>
                <AllocationChart
                  data={allocation?.by_asset_type || []}
                  totalValue={allocation?.total_value || 0}
                />
              </div>
            </div>

            {/* Performance and Dividends */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PerformanceChart
                data={performance?.data_points || []}
                onPeriodChange={(period) => setPerformancePeriod(period)}
              />
              <DividendHistory dividends={dividends || []} />
            </div>
          </div>
        </div>
      </div>

      {/* Add Asset Modal */}
      <AddAssetModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={(data) => addAsset.mutate(data)}
        apiUrl={API_URL}
      />
    </>
  );
}
