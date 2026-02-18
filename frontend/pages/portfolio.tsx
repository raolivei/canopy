import React, { useState, useMemo } from "react";
import Head from "next/head";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Sidebar from "../components/Sidebar";
import DarkModeToggle from "../components/DarkModeToggle";
import CurrencySelector from "../components/CurrencySelector";
import PortfolioHoldingsTable from "../components/PortfolioHoldingsTable";
import AddAssetModal from "../components/AddAssetModal";
import AllocationChart from "../components/AllocationChart";
import DividendHistory from "../components/DividendHistory";
import PerformanceChart from "../components/PerformanceChart";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  Plus,
  RefreshCw,
  Loader2,
  Filter,
} from "lucide-react";
import { convertCurrency } from "../utils/currency";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

// Exchange rates (approximate - should come from API in production)
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

function formatCurrencyValue(
  value: number | null,
  currency: string = "USD",
): string {
  if (value === null) return "—";
  // Handle non-standard currencies
  if (currency === "BTC" || currency === "ETH") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number | null): string {
  if (value === null) return "—";
  const num = Number(value);
  return `${num >= 0 ? "+" : ""}${num.toFixed(2)}%`;
}

export default function Portfolio() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [performancePeriod, setPerformancePeriod] = useState("30d");
  const [displayCurrency, setDisplayCurrency] = useState("CAD");
  const [currencyFilter, setCurrencyFilter] = useState<string | null>(null);
  const [showCurrencyFilter, setShowCurrencyFilter] = useState(false);
  const queryClient = useQueryClient();

  // Convert value from one currency to display currency
  const convertToDisplay = (
    value: number | string | null,
    fromCurrency: string,
  ): number => {
    if (value === null) return 0;
    const numValue = Number(value);
    if (fromCurrency === displayCurrency) return numValue;

    // Handle crypto
    if (fromCurrency === "BTC") {
      // BTC to USD then to display
      const btcToUsd = numValue * 62000; // Approximate BTC price
      return convertToDisplay(btcToUsd, "USD");
    }
    if (fromCurrency === "ETH") {
      const ethToUsd = numValue * 2400; // Approximate ETH price
      return convertToDisplay(ethToUsd, "USD");
    }

    const rates = EXCHANGE_RATES[fromCurrency];
    if (!rates) return numValue;
    return numValue * (rates[displayCurrency] || 1);
  };

  // Fetch portfolio summary
  const { data: summary, isLoading: summaryLoading } =
    useQuery<PortfolioSummary>({
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
      const res = await fetch(
        `${API_URL}/v1/portfolio/performance?period=${performancePeriod}`,
      );
      if (!res.ok) throw new Error("Failed to fetch performance");
      return res.json();
    },
  });

  // Refresh prices mutation
  const refreshPrices = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_URL}/v1/portfolio/prices/refresh`, {
        method: "POST",
      });
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
      const res = await fetch(`${API_URL}/v1/portfolio/snapshots/create`, {
        method: "POST",
      });
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

  // Filter and convert holdings
  const processedHoldings = useMemo(() => {
    if (!summary?.holdings) return [];

    let holdings = summary.holdings;

    // Apply currency filter
    if (currencyFilter) {
      holdings = holdings.filter((h: any) => h.currency === currencyFilter);
    }

    // Convert values to display currency
    return holdings.map((h: any) => ({
      ...h,
      market_value_converted: convertToDisplay(h.market_value, h.currency),
      cost_basis_converted: convertToDisplay(h.cost_basis, h.currency),
    }));
  }, [summary?.holdings, currencyFilter, displayCurrency]);

  // Calculate totals in display currency
  const totalValue = useMemo(() => {
    return processedHoldings.reduce(
      (sum: number, h: any) => sum + (h.market_value_converted || 0),
      0,
    );
  }, [processedHoldings]);

  // Get unique currencies from holdings
  const availableCurrencies = useMemo(() => {
    if (!summary?.holdings) return [];
    const currencies = new Set(summary.holdings.map((h: any) => h.currency));
    return Array.from(currencies).sort();
  }, [summary?.holdings]);

  const isPositive = totalValue > 0;
  const isNegative = totalValue < 0;

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
                {/* Currency Filter */}
                <div className="relative">
                  <button
                    onClick={() => setShowCurrencyFilter(!showCurrencyFilter)}
                    className={`flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      currencyFilter
                        ? "border-primary-500"
                        : "border-gray-200 dark:border-gray-700"
                    }`}
                  >
                    <Filter className="w-4 h-4" />
                    {currencyFilter || "All"}
                  </button>
                  {showCurrencyFilter && (
                    <>
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setShowCurrencyFilter(false)}
                      />
                      <div className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-50 min-w-[120px]">
                        <button
                          onClick={() => {
                            setCurrencyFilter(null);
                            setShowCurrencyFilter(false);
                          }}
                          className={`w-full text-left px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-t-xl ${
                            !currencyFilter
                              ? "bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400"
                              : ""
                          }`}
                        >
                          All Currencies
                        </button>
                        {availableCurrencies.map((currency) => (
                          <button
                            key={currency}
                            onClick={() => {
                              setCurrencyFilter(currency);
                              setShowCurrencyFilter(false);
                            }}
                            className={`w-full text-left px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 last:rounded-b-xl ${
                              currencyFilter === currency
                                ? "bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400"
                                : ""
                            }`}
                          >
                            {currency}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>

                {/* Display Currency */}
                <CurrencySelector
                  selectedCurrency={displayCurrency}
                  onCurrencyChange={setDisplayCurrency}
                  showLabel={false}
                />

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
                  Refresh
                </button>
                <button
                  onClick={() => setIsAddModalOpen(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Add
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
                      {currencyFilter && (
                        <span className="ml-1 text-primary-500">
                          ({currencyFilter})
                        </span>
                      )}
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                      {summaryLoading
                        ? "..."
                        : formatCurrencyValue(totalValue, displayCurrency)}
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
                    <p className="text-2xl font-bold mt-2 text-gray-500">
                      {summaryLoading ? "..." : "—"}
                    </p>
                    <p className="text-sm text-gray-500">(no cost basis)</p>
                  </div>
                  <div className="p-3 rounded-xl bg-gray-100 dark:bg-gray-800">
                    <TrendingUp className="w-6 h-6 text-gray-400" />
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
                      {summaryLoading
                        ? "..."
                        : formatCurrencyValue(
                            Number(summary?.total_dividends ?? 0),
                            displayCurrency,
                          )}
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
                      {summaryLoading ? "..." : processedHoldings.length}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {currencyFilter
                        ? `${currencyFilter} assets`
                        : "assets tracked"}
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
                    {currencyFilter && (
                      <span className="ml-2 text-sm font-normal text-primary-500">
                        ({currencyFilter} only)
                      </span>
                    )}
                  </h2>
                </div>
                <PortfolioHoldingsTable
                  holdings={processedHoldings}
                  onSelect={(holding) => console.log("Selected:", holding)}
                  currency={displayCurrency}
                  convertToDisplay={convertToDisplay}
                />
              </div>

              {/* Allocation Chart */}
              <div>
                <AllocationChart
                  data={allocation?.by_asset_type || []}
                  totalValue={totalValue}
                  currency={displayCurrency}
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
