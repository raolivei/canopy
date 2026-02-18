import { useState, useEffect, useRef } from "react";
import {
  ChevronDown,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";
import { cn } from "@/utils/cn";

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
  const containerRef = useRef<HTMLDivElement>(null);

  const selected =
    CURRENCIES.find((c) => c.code === selectedCurrency) || CURRENCIES[0];

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

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const refreshRates = async () => {
    setIsRefreshing(true);
    try {
      await fetch("/v1/currency/refresh", { method: "POST" });
      await new Promise((r) => setTimeout(r, 2000));
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
    <div className="relative" ref={containerRef}>
      {showLabel && (
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Display Currency
        </label>
      )}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-4 py-2",
          "bg-white dark:bg-slate-900",
          "border border-slate-300 dark:border-slate-700 rounded-md",
          "hover:border-primary-500 dark:hover:border-primary-400",
          "transition-colors w-full md:w-auto"
        )}
      >
        <span className="text-lg">{selected.flag}</span>
        <span className="font-medium text-slate-900 dark:text-white">
          {selected.code}
        </span>
        {rateStatus && (
          <span
            className={cn(
              "w-2 h-2 rounded-full",
              rateStatus.is_live ? "bg-success-500" : "bg-warning-500"
            )}
            title={rateStatus.is_live ? "Live rates" : "Cached rates"}
          />
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-slate-400 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50 min-w-[280px] animate-fade-in">
          <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {rateStatus?.is_live ? (
                  <Wifi className="w-3.5 h-3.5 text-success-500" />
                ) : (
                  <WifiOff className="w-3.5 h-3.5 text-warning-500" />
                )}
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {rateStatus?.is_live ? "Live rates" : "Cached rates"} · Updated{" "}
                  {formatLastUpdate(rateStatus?.last_update || null)}
                </span>
              </div>
              <button
                onClick={refreshRates}
                disabled={isRefreshing}
                className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors"
                title="Refresh rates"
              >
                <RefreshCw
                  className={cn("w-3.5 h-3.5 text-slate-400", isRefreshing && "animate-spin")}
                />
              </button>
            </div>
            <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
              Source: ECB via frankfurter.app
            </div>
          </div>

          {CURRENCIES.map((currency) => (
            <button
              key={currency.code}
              onClick={() => {
                onCurrencyChange(currency.code);
                setIsOpen(false);
              }}
              className={cn(
                "w-full text-left px-4 py-3 transition-colors last:rounded-b-lg",
                selectedCurrency === currency.code
                  ? "bg-primary-50 dark:bg-primary-950/50 text-primary-700 dark:text-primary-300"
                  : "text-slate-900 dark:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-lg">{currency.flag}</span>
                  <div>
                    <div className="font-medium">{currency.code}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {currency.name}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm font-medium">{currency.symbol}</span>
                  {rateStatus?.rates &&
                    currency.code !== selectedCurrency && (
                      <div className="text-xs text-slate-400 dark:text-slate-500">
                        1 {selectedCurrency} ={" "}
                        {rateStatus.rates[currency.code]?.toFixed(4) || "—"}
                      </div>
                    )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
