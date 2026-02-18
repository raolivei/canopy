import { useEffect, useState, useMemo, useCallback } from "react";
import { useRouter } from "next/router";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { Select, MultiSelect } from "@/components/ui/Select";
import { Badge, CurrencyBadge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { SkeletonList } from "@/components/ui/Skeleton";
import {
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  ArrowLeftRight,
  Calendar,
  Tag,
  Wallet,
  Search,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  X,
} from "lucide-react";
import { format, isToday, isYesterday, isThisWeek, isThisMonth, parseISO } from "date-fns";
import { formatCurrency, convertCurrency } from "@/utils/currency";
import { cn } from "@/utils/cn";
import { motion, AnimatePresence } from "framer-motion";

interface Transaction {
  id: number;
  description: string;
  amount: number;
  currency: string;
  type: "income" | "expense" | "transfer";
  category?: string;
  date: string;
  account?: string;
  merchant?: string;
  original_statement?: string;
  notes?: string;
  tags?: string[];
  import_source?: string;
}

const CATEGORIES = [
  "Food & Dining",
  "Shopping",
  "Transportation",
  "Entertainment",
  "Bills & Utilities",
  "Healthcare",
  "Travel",
  "Education",
  "Income",
  "Investment",
  "Transfer",
  "Other",
];

const ACCOUNTS = ["Checking", "Savings", "Credit Card", "Investment", "Cash"];

export default function Transactions() {
  const router = useRouter();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [displayCurrency, setDisplayCurrency] = useState("CAD");
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [accountFilter, setAccountFilter] = useState<string>("all");
  const [formData, setFormData] = useState({
    description: "",
    amount: "",
    currency: "CAD",
    type: "expense" as "income" | "expense" | "transfer",
    category: "",
    account: "",
    date: format(new Date(), "yyyy-MM-dd"),
  });

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.set("search", searchQuery);
      if (typeFilter !== "all") params.set("type", typeFilter);
      if (categoryFilter.length === 1) params.set("category", categoryFilter[0]);
      if (startDate) params.set("start_date", new Date(startDate).toISOString());
      if (endDate) params.set("end_date", new Date(endDate + "T23:59:59").toISOString());
      if (minAmount) params.set("min_amount", minAmount);
      if (maxAmount) params.set("max_amount", maxAmount);
      if (accountFilter !== "all") params.set("account", accountFilter);
      if (displayCurrency) params.set("currency", displayCurrency);
      params.set("limit", "2000");

      const res = await fetch(`/v1/transactions/?${params.toString()}`);
      const data = await res.json();
      setTransactions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch transactions:", err);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, typeFilter, categoryFilter, startDate, endDate, minAmount, maxAmount, accountFilter, displayCurrency]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  useEffect(() => {
    if (router.query.action === "add") {
      setIsAddModalOpen(true);
      router.replace("/transactions", undefined, { shallow: true });
    }
    if (router.query.category && typeof router.query.category === "string") {
      setCategoryFilter([router.query.category]);
      setShowAdvanced(true);
    }
  }, [router.query]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/v1/transactions/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          amount: parseFloat(formData.amount),
          date: new Date(formData.date).toISOString(),
        }),
      });
      if (res.ok) {
        await fetchTransactions();
        setIsAddModalOpen(false);
        resetForm();
      }
    } catch (err) {
      console.error("Failed to create transaction:", err);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      const res = await fetch(`/v1/transactions/${id}`, { method: "DELETE" });
      if (res.ok) {
        await fetchTransactions();
      }
    } catch (err) {
      console.error("Failed to delete transaction:", err);
    }
  };

  const resetForm = () => {
    setFormData({
      description: "",
      amount: "",
      currency: "CAD",
      type: "expense",
      category: "",
      account: "",
      date: format(new Date(), "yyyy-MM-dd"),
    });
  };

  const { totalIncome, totalExpenses, net } = useMemo(() => {
    const income = transactions.filter((t) => t.type === "income").reduce((sum, t) => sum + t.amount, 0);
    const expenses = transactions.filter((t) => t.type === "expense").reduce((sum, t) => sum + t.amount, 0);
    return { totalIncome: income, totalExpenses: expenses, net: income - expenses };
  }, [transactions]);

  const filteredTransactions = useMemo(() => {
    let result = [...transactions];
    if (categoryFilter.length > 1) {
      result = result.filter((t) => categoryFilter.includes(t.category || ""));
    }
    return result.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [transactions, categoryFilter]);

  const groupedTransactions = useMemo(() => {
    const groups: Record<string, Transaction[]> = {};

    filteredTransactions.forEach((tx) => {
      const date = parseISO(tx.date);
      let label: string;

      if (isToday(date)) {
        label = "Today";
      } else if (isYesterday(date)) {
        label = "Yesterday";
      } else if (isThisWeek(date)) {
        label = "This Week";
      } else if (isThisMonth(date)) {
        label = "This Month";
      } else {
        label = format(date, "MMMM yyyy");
      }

      if (!groups[label]) groups[label] = [];
      groups[label].push(tx);
    });

    return groups;
  }, [filteredTransactions]);

  const uniqueCategories = useMemo(() => {
    const cats = new Set(transactions.map((t) => t.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [transactions]);

  const uniqueAccounts = useMemo(() => {
    const accs = new Set(transactions.map((t) => t.account).filter(Boolean));
    return Array.from(accs).sort();
  }, [transactions]);

  const typeOptions = [
    { value: "all", label: "All Types" },
    { value: "income", label: "Income" },
    { value: "expense", label: "Expense" },
    { value: "transfer", label: "Transfer" },
  ];

  const categoryOptions = uniqueCategories.map((c) => ({ value: c as string, label: c as string }));

  const accountOptions = [
    { value: "all", label: "All Accounts" },
    ...uniqueAccounts.map((a) => ({ value: a as string, label: a as string })),
  ];

  const currencyOptions = [
    { value: "CAD", label: "CAD" },
    { value: "USD", label: "USD" },
    { value: "BRL", label: "BRL" },
    { value: "EUR", label: "EUR" },
    { value: "GBP", label: "GBP" },
  ];

  const hasActiveFilters = typeFilter !== "all" || categoryFilter.length > 0 || searchQuery || startDate || endDate || minAmount || maxAmount || accountFilter !== "all";

  const advancedFilterCount = [startDate, endDate, minAmount, maxAmount, accountFilter !== "all" ? accountFilter : ""].filter(Boolean).length;

  const clearAllFilters = () => {
    setTypeFilter("all");
    setCategoryFilter([]);
    setSearchQuery("");
    setStartDate("");
    setEndDate("");
    setMinAmount("");
    setMaxAmount("");
    setAccountFilter("all");
  };

  return (
    <PageLayout title="Transactions" description="Manage your income and expenses">
      <PageHeader
        title="Transactions"
        description="Track and manage your financial activity"
        actions={
          <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setIsAddModalOpen(true)}>
            Add Transaction
          </Button>
        }
      />

      {/* Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6"
      >
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Income</p>
                <p className="text-2xl font-semibold text-success-600 dark:text-success-400 mt-1">
                  {formatCurrency(totalIncome, displayCurrency)}
                </p>
              </div>
              <div className="p-2 bg-success-100 dark:bg-success-900/30 rounded-lg">
                <TrendingUp className="w-5 h-5 text-success-600 dark:text-success-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Expenses</p>
                <p className="text-2xl font-semibold text-danger-600 dark:text-danger-400 mt-1">
                  {formatCurrency(totalExpenses, displayCurrency)}
                </p>
              </div>
              <div className="p-2 bg-danger-100 dark:bg-danger-900/30 rounded-lg">
                <TrendingDown className="w-5 h-5 text-danger-600 dark:text-danger-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Net</p>
                <p className={cn("text-2xl font-semibold mt-1", net >= 0 ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400")}>
                  {formatCurrency(net, displayCurrency)}
                </p>
              </div>
              <div className={cn("p-2 rounded-lg", net >= 0 ? "bg-success-100 dark:bg-success-900/30" : "bg-danger-100 dark:bg-danger-900/30")}>
                {net >= 0 ? (
                  <TrendingUp className="w-5 h-5 text-success-600 dark:text-success-400" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-danger-600 dark:text-danger-400" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="mb-6"
      >
        <Card>
          <CardContent className="p-4 space-y-3">
            {/* Primary filter row */}
            <div className="flex flex-col lg:flex-row gap-3">
              <div className="flex-1">
                <Input
                  placeholder="Search description, merchant, notes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  leftIcon={<Search className="w-4 h-4" />}
                  rightIcon={
                    searchQuery ? (
                      <button onClick={() => setSearchQuery("")}>
                        <X className="w-4 h-4" />
                      </button>
                    ) : undefined
                  }
                />
              </div>
              <div className="flex flex-wrap gap-2 items-center">
                <Select options={typeOptions} value={typeFilter} onChange={setTypeFilter} className="w-32" />
                <MultiSelect
                  options={categoryOptions}
                  value={categoryFilter}
                  onChange={setCategoryFilter}
                  placeholder="Categories"
                  className="w-40"
                />
                <Select options={currencyOptions} value={displayCurrency} onChange={setDisplayCurrency} className="w-24" />
                <Button
                  variant="ghost"
                  size="sm"
                  leftIcon={<Filter className="w-4 h-4" />}
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className={cn(advancedFilterCount > 0 && "text-primary-600 dark:text-primary-400")}
                >
                  More{advancedFilterCount > 0 ? ` (${advancedFilterCount})` : ""}
                </Button>
                {hasActiveFilters && (
                  <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                    Clear all
                  </Button>
                )}
              </div>
            </div>

            {/* Advanced filters */}
            <AnimatePresence>
              {showAdvanced && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                          <Calendar className="w-3 h-3 inline mr-1" />From
                        </label>
                        <Input
                          type="date"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                          <Calendar className="w-3 h-3 inline mr-1" />To
                        </label>
                        <Input
                          type="date"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                          Min Amount
                        </label>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="0.00"
                          value={minAmount}
                          onChange={(e) => setMinAmount(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                          Max Amount
                        </label>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="∞"
                          value={maxAmount}
                          onChange={(e) => setMaxAmount(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                          <Wallet className="w-3 h-3 inline mr-1" />Account
                        </label>
                        <Select options={accountOptions} value={accountFilter} onChange={setAccountFilter} />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Active filter count */}
            {hasActiveFilters && (
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Showing {filteredTransactions.length} transaction{filteredTransactions.length !== 1 ? "s" : ""}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Transactions List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        {loading ? (
          <SkeletonList items={8} />
        ) : filteredTransactions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <ArrowLeftRight className="w-6 h-6 text-slate-400" />
              </div>
              <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-1">
                {hasActiveFilters ? "No matching transactions" : "No transactions yet"}
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                {hasActiveFilters ? "Try adjusting your filters" : "Add your first transaction to get started"}
              </p>
              {!hasActiveFilters && (
                <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setIsAddModalOpen(true)}>
                  Add Transaction
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedTransactions).map(([dateLabel, txs]) => (
              <div key={dateLabel}>
                <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-3 sticky top-0 bg-slate-50 dark:bg-slate-950 py-2 z-10">
                  {dateLabel}
                </h3>
                <Card>
                  <CardContent noPadding>
                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                      {txs.map((tx) => (
                        <TransactionRow key={tx.id} transaction={tx} onDelete={handleDelete} displayCurrency={displayCurrency} />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Add Transaction Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => {
          setIsAddModalOpen(false);
          resetForm();
        }}
        title="Add Transaction"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSubmit}>
              Add Transaction
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Description"
            required
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="e.g., Grocery shopping"
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Amount"
              type="number"
              step="0.01"
              required
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              placeholder="0.00"
            />
            <Select
              label="Currency"
              options={currencyOptions}
              value={formData.currency}
              onChange={(v) => setFormData({ ...formData, currency: v })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Type"
              options={[
                { value: "expense", label: "Expense" },
                { value: "income", label: "Income" },
                { value: "transfer", label: "Transfer" },
              ]}
              value={formData.type}
              onChange={(v) => setFormData({ ...formData, type: v as any })}
            />
            <Input
              label="Date"
              type="date"
              required
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Category"
              options={CATEGORIES.map((c) => ({ value: c, label: c }))}
              value={formData.category}
              onChange={(v) => setFormData({ ...formData, category: v })}
              searchable
              placeholder="Select category"
            />
            <Select
              label="Account"
              options={ACCOUNTS.map((a) => ({ value: a, label: a }))}
              value={formData.account}
              onChange={(v) => setFormData({ ...formData, account: v })}
              placeholder="Select account"
            />
          </div>
        </form>
      </Modal>
    </PageLayout>
  );
}

interface TransactionRowProps {
  transaction: Transaction;
  onDelete: (id: number) => void;
  displayCurrency: string;
}

function TransactionRow({ transaction: tx, onDelete, displayCurrency }: TransactionRowProps) {
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);

  return (
    <div className="flex items-center justify-between px-5 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <div
          className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center shrink-0",
            tx.type === "income"
              ? "bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400"
              : tx.type === "expense"
              ? "bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400"
              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
          )}
        >
          {tx.type === "income" ? (
            <ArrowUpRight className="w-5 h-5" />
          ) : tx.type === "expense" ? (
            <ArrowDownRight className="w-5 h-5" />
          ) : (
            <ArrowLeftRight className="w-5 h-5" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-slate-900 dark:text-white truncate">{tx.description}</p>
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex-wrap">
            <span>{format(parseISO(tx.date), "MMM d, yyyy")}</span>
            {tx.merchant && tx.merchant !== tx.description && (
              <span className="truncate max-w-[150px]" title={tx.merchant}>{tx.merchant}</span>
            )}
            {tx.category && (
              <Badge variant="default" size="sm">
                {tx.category}
              </Badge>
            )}
            {tx.account && <span className="hidden sm:inline">{tx.account}</span>}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p
            className={cn(
              "font-semibold",
              tx.type === "income"
                ? "text-success-600 dark:text-success-400"
                : tx.type === "expense"
                ? "text-danger-600 dark:text-danger-400"
                : "text-slate-700 dark:text-slate-300"
            )}
          >
            {tx.type === "expense" ? "-" : tx.type === "income" ? "+" : ""}
            {formatCurrency(Math.abs(tx.amount), tx.currency)}
          </p>
          <CurrencyBadge currency={tx.currency} className="mt-0.5" />
        </div>
        <button
          onClick={() => setShowConfirmDelete(true)}
          className="p-2 text-slate-400 hover:text-danger-600 dark:hover:text-danger-400 opacity-0 group-hover:opacity-100 transition-opacity rounded-md hover:bg-danger-50 dark:hover:bg-danger-900/30"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <AnimatePresence>
        {showConfirmDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
            onClick={() => setShowConfirmDelete(false)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="bg-white dark:bg-slate-900 rounded-xl p-6 max-w-sm w-full shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Delete Transaction</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                Are you sure you want to delete this transaction? This action cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <Button variant="secondary" size="sm" onClick={() => setShowConfirmDelete(false)}>
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => {
                    onDelete(tx.id);
                    setShowConfirmDelete(false);
                  }}
                >
                  Delete
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
