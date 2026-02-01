import React, { useState } from "react";
import { X, Search, Loader2, Plus } from "lucide-react";

interface Quote {
  symbol: string;
  name: string;
  price: number;
  currency: string;
}

interface AddAssetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (data: {
    symbol: string;
    name: string;
    asset_type: string;
    currency: string;
    quantity: number;
    price_per_unit: number;
    purchase_date: string;
    account?: string;
  }) => void;
  apiUrl: string;
}

const ASSET_TYPES = [
  { value: "stock", label: "Stock" },
  { value: "etf", label: "ETF" },
  { value: "crypto", label: "Crypto" },
  { value: "bond", label: "Bond" },
  { value: "other", label: "Other" },
];

export default function AddAssetModal({ isOpen, onClose, onAdd, apiUrl }: AddAssetModalProps) {
  const [symbol, setSymbol] = useState("");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Form fields
  const [assetType, setAssetType] = useState("stock");
  const [quantity, setQuantity] = useState("");
  const [pricePerUnit, setPricePerUnit] = useState("");
  const [purchaseDate, setPurchaseDate] = useState(new Date().toISOString().split("T")[0]);
  const [account, setAccount] = useState("");

  const lookupSymbol = async () => {
    if (!symbol.trim()) return;
    
    setLoading(true);
    setError("");
    setQuote(null);
    
    try {
      const response = await fetch(`${apiUrl}/v1/portfolio/quote/${symbol.toUpperCase()}`);
      if (!response.ok) {
        throw new Error("Symbol not found");
      }
      const data = await response.json();
      setQuote(data);
      setPricePerUnit(data.price.toString());
    } catch (err) {
      setError("Could not find symbol. Please check and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!quote && !symbol.trim()) {
      setError("Please enter a symbol");
      return;
    }
    
    onAdd({
      symbol: symbol.toUpperCase(),
      name: quote?.name || symbol.toUpperCase(),
      asset_type: assetType,
      currency: quote?.currency || "USD",
      quantity: parseFloat(quantity),
      price_per_unit: parseFloat(pricePerUnit),
      purchase_date: purchaseDate,
      account: account || undefined,
    });
    
    // Reset form
    setSymbol("");
    setQuote(null);
    setQuantity("");
    setPricePerUnit("");
    setAccount("");
    setAssetType("stock");
    setPurchaseDate(new Date().toISOString().split("T")[0]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-xl w-full max-w-lg mx-4 p-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <X className="w-5 h-5" />
        </button>
        
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
          Add New Asset
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Symbol Lookup */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Symbol
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="AAPL, BTC-USD, VOO..."
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={lookupSymbol}
                disabled={loading || !symbol.trim()}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Lookup
              </button>
            </div>
            {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
            {quote && (
              <div className="mt-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="font-medium text-green-800 dark:text-green-300">{quote.name}</p>
                <p className="text-sm text-green-600 dark:text-green-400">
                  Current price: {new Intl.NumberFormat("en-US", { style: "currency", currency: quote.currency }).format(quote.price)}
                </p>
              </div>
            )}
          </div>
          
          {/* Asset Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Asset Type
            </label>
            <select
              value={assetType}
              onChange={(e) => setAssetType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            >
              {ASSET_TYPES.map((type) => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
          
          {/* Quantity and Price */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Quantity
              </label>
              <input
                type="number"
                step="any"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="10"
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Price per Share
              </label>
              <input
                type="number"
                step="any"
                value={pricePerUnit}
                onChange={(e) => setPricePerUnit(e.target.value)}
                placeholder="150.00"
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
          
          {/* Purchase Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Purchase Date
            </label>
            <input
              type="date"
              value={purchaseDate}
              onChange={(e) => setPurchaseDate(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          {/* Account (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Account (optional)
            </label>
            <input
              type="text"
              value={account}
              onChange={(e) => setAccount(e.target.value)}
              placeholder="Fidelity, Robinhood..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          {/* Total */}
          {quantity && pricePerUnit && (
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Cost</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
                  parseFloat(quantity) * parseFloat(pricePerUnit)
                )}
              </p>
            </div>
          )}
          
          {/* Submit */}
          <button
            type="submit"
            disabled={!symbol.trim() || !quantity || !pricePerUnit}
            className="w-full py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Asset
          </button>
        </form>
      </div>
    </div>
  );
}
