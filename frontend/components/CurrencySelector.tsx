import { useState, useEffect } from "react";
import { DollarSign, ChevronDown } from "lucide-react";

interface Currency {
  code: string;
  symbol: string;
  name: string;
}

const CURRENCIES: Currency[] = [
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "CAD", symbol: "C$", name: "Canadian Dollar" },
  { code: "BRL", symbol: "R$", name: "Brazilian Real" },
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "GBP", symbol: "£", name: "British Pound" },
];

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

  const selected =
    CURRENCIES.find((c) => c.code === selectedCurrency) || CURRENCIES[0];

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
        <DollarSign size={18} className="text-gray-500 dark:text-gray-400" />
        <span className="font-medium text-gray-900 dark:text-white">
          {selected.code}
        </span>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          ({selected.symbol})
        </span>
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
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-20 min-w-[200px]">
            {CURRENCIES.map((currency) => (
              <button
                key={currency.code}
                onClick={() => {
                  onCurrencyChange(currency.code);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors first:rounded-t-xl last:rounded-b-xl ${
                  selectedCurrency === currency.code
                    ? "bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400"
                    : "text-gray-900 dark:text-gray-100"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{currency.code}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {currency.name}
                    </div>
                  </div>
                  <span className="text-sm font-medium">{currency.symbol}</span>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
