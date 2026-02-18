import React, { useState } from "react";
import { Search, Loader2, Plus } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { cn } from "@/utils/cn";

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
      if (!response.ok) throw new Error("Symbol not found");
      const data = await response.json();
      setQuote(data);
      setPricePerUnit(data.price.toString());
    } catch {
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

    resetForm();
  };

  const resetForm = () => {
    setSymbol("");
    setQuote(null);
    setQuantity("");
    setPricePerUnit("");
    setAccount("");
    setAssetType("stock");
    setPurchaseDate(new Date().toISOString().split("T")[0]);
    setError("");
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add New Asset"
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={!symbol.trim() || !quantity || !pricePerUnit}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Asset
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            Symbol
          </label>
          <div className="flex gap-2">
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="AAPL, BTC-USD, VOO..."
              leftIcon={<Search className="w-4 h-4" />}
              error={error || undefined}
            />
            <Button
              type="button"
              variant="primary"
              onClick={lookupSymbol}
              disabled={loading || !symbol.trim()}
              loading={loading}
            >
              Lookup
            </Button>
          </div>
          {quote && (
            <div className="mt-2 p-3 bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 rounded-lg">
              <p className="font-medium text-success-800 dark:text-success-300">{quote.name}</p>
              <p className="text-sm text-success-600 dark:text-success-400">
                Current price:{" "}
                {new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: quote.currency,
                }).format(quote.price)}
              </p>
            </div>
          )}
        </div>

        <Select
          label="Asset Type"
          options={ASSET_TYPES}
          value={assetType}
          onChange={setAssetType}
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Quantity"
            type="number"
            step="any"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="10"
            required
          />
          <Input
            label="Price per Share"
            type="number"
            step="any"
            value={pricePerUnit}
            onChange={(e) => setPricePerUnit(e.target.value)}
            placeholder="150.00"
            required
          />
        </div>

        <Input
          label="Purchase Date"
          type="date"
          value={purchaseDate}
          onChange={(e) => setPurchaseDate(e.target.value)}
          required
        />

        <Input
          label="Account (optional)"
          value={account}
          onChange={(e) => setAccount(e.target.value)}
          placeholder="Fidelity, Robinhood..."
        />

        {quantity && pricePerUnit && (
          <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <p className="text-sm text-slate-500 dark:text-slate-400">Total Cost</p>
            <p className="text-xl font-bold text-slate-900 dark:text-white">
              {new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: quote?.currency || "USD",
              }).format(parseFloat(quantity) * parseFloat(pricePerUnit))}
            </p>
          </div>
        )}
      </form>
    </Modal>
  );
}
