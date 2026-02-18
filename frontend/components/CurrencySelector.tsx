import { useState, useEffect } from "react";
import {
  DollarSign,
  ChevronDown,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";

interface Currency {
  code: string;
  symbol: string;
  name: string;
  flag: string;
}

const CURRENCIES: Currency[] = [
  { code: "USD", symbol: "$", name: "US Dollar", flag: "🇺🇸" },
  { code: "CAD", symbol: "C$", name: "Canadian Dollar", flag: "🇨🇦" },
  { code: "BRL", symbol: "R$", name: "Brazilian Real", flag: "🇧🇷" },
  { code: "EUR", symbol: "€", name: "Euro", flag: "🇪🇺" },
  { code: "GBP", symbol: "£", name: "British Pound", flag: "🇬🇧" },
];

interface RateStatus {
  is_live: boolean;
  last_update: string | null;
  rates: Record<string, number>;
}

interface CurrencySelectorProps {
  selectedCurrency: string;
  onCurrencyChange: (currency: string) => void;
  showLabel?: boolean;
}

export default function CurrencySelector({
  selectedCurrency,
  onCurrencyChange,
  showLabel = true,
}: CurrencySelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [rateStatus, setRateStatus] = useState<RateStatus | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const selected =
    CURRENCIES.find((c) => c.code === selectedCurrency) || CURRENCIES[0];

  // Fetch rate status
  useEffect(() => {
    const fetchRates = async () => {
      try {
        const res = await fetch(
          `/v1/currency/rates?base_currency=${selectedCurrency}`,
        );
        if (res.ok) {
          const data = await res.json();
          setRateStatus({
            is_live: data.is_live,
            last_update: data.last_update,
            rates: data.rates,
          });
        }
      } catch (err) {
        console.error("Failed to fetch rates:", err);
      }
    };
    fetchRates();
  }, [selectedCurrency]);

  const refreshRates = async () => {
    setIsRefreshing(true);
    try {
      await fetch("/v1/currency/refresh", { method: "POST" });
      // Wait a bit for refresh to complete
      await new Promise((r) => setTimeout(r, 2000));
      // Re-fetch rates
      const res = await fetch(
        `/v1/currency/rates?base_currency=${selectedCurrency}`,
      );
      if (res.ok) {
        const data = await res.json();
        setRateStatus({
          is_live: data.is_live,
          last_update: data.last_update,
          rates: data.rates,
        });
      }
    } catch (err) {
      console.error("Failed to refresh rates:", err);
    }
    setIsRefreshing(false);
  };

  const formatLastUpdate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative">
      {showLabel && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Display Currency
        </label>
      )}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-primary-500 dark:hover:border-primary-400 transition-colors w-full md:w-auto"
      >
        <span className="text-lg">{selected.flag}</span>
        <span className="font-medium text-gray-900 dark:text-white">
          {selected.code}
        </span>
        {rateStatus && (
          <span
            className={`w-2 h-2 rounded-full ${rateStatus.is_live ? "bg-green-500" : "bg-yellow-500"}`}
            title={rateStatus.is_live ? "Live rates" : "Cached rates"}
          />
        )}
        <ChevronDown
          size={16}
          className={`text-gray-400 dark:text-gray-500 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-50 min-w-[280px]">
            {/* Rate status header */}
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {rateStatus?.is_live ? (
                    <Wifi size={14} className="text-green-500" />
                  ) : (
                    <WifiOff size={14} className="text-yellow-500" />
                  )}
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {rateStatus?.is_live ? "Live rates" : "Cached rates"} •
                    Updated {formatLastUpdate(rateStatus?.last_update || null)}
                  </span>
                </div>
                <button
                  onClick={refreshRates}
                  disabled={isRefreshing}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  title="Refresh rates"
                >
                  <RefreshCw
                    size={14}
                    className={`text-gray-400 ${isRefreshing ? "animate-spin" : ""}`}
                  />
                </button>
              </div>
              <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">
                Source: ECB via frankfurter.app
              </div>
            </div>

            {/* Currency options */}
            {CURRENCIES.map((currency) => (
              <button
                key={currency.code}
                onClick={() => {
                  onCurrencyChange(currency.code);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors last:rounded-b-xl ${
                  selectedCurrency === currency.code
                    ? "bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400"
                    : "text-gray-900 dark:text-gray-100"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{currency.flag}</span>
                    <div>
                      <div className="font-medium">{currency.code}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {currency.name}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium">
                      {currency.symbol}
                    </span>
                    {rateStatus?.rates &&
                      currency.code !== selectedCurrency && (
                        <div className="text-xs text-gray-400">
                          1 {selectedCurrency} ={" "}
                          {rateStatus.rates[currency.code]?.toFixed(4) || "—"}
                        </div>
                      )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
