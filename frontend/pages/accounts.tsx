import React, { useState } from "react";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import {
  Wallet,
  Plus,
  CreditCard,
  Building2,
  PiggyBank,
  TrendingUp,
  AlertCircle,
  MoreHorizontal,
  ArrowUpRight,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/utils/cn";

interface Account {
  id: string;
  name: string;
  type: "checking" | "savings" | "credit" | "investment" | "loan";
  balance: number;
  currency: string;
  institution?: string;
}

const sampleAccounts: Account[] = [
  {
    id: "1",
    name: "Primary Checking",
    type: "checking",
    balance: 0,
    currency: "CAD",
    institution: "TD Bank",
  },
  {
    id: "2",
    name: "Credit Card",
    type: "credit",
    balance: 0,
    currency: "CAD",
    institution: "Capital One",
  },
  {
    id: "3",
    name: "Savings Account",
    type: "savings",
    balance: 0,
    currency: "CAD",
    institution: "EQ Bank",
  },
];

const accountTypeConfig = {
  checking: {
    icon: Building2,
    bgColor: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
  },
  savings: {
    icon: PiggyBank,
    bgColor: "bg-success-100 dark:bg-success-900/30",
    iconColor: "text-success-600 dark:text-success-400",
  },
  credit: {
    icon: CreditCard,
    bgColor: "bg-purple-100 dark:bg-purple-900/30",
    iconColor: "text-purple-600 dark:text-purple-400",
  },
  investment: {
    icon: TrendingUp,
    bgColor: "bg-primary-100 dark:bg-primary-900/30",
    iconColor: "text-primary-600 dark:text-primary-400",
  },
  loan: {
    icon: AlertCircle,
    bgColor: "bg-danger-100 dark:bg-danger-900/30",
    iconColor: "text-danger-600 dark:text-danger-400",
  },
};

export default function Accounts() {
  const [accounts] = useState<Account[]>(sampleAccounts);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const totalBalance = accounts.reduce((sum, acc) => {
    if (acc.type === "credit" || acc.type === "loan") {
      return sum - acc.balance;
    }
    return sum + acc.balance;
  }, 0);

  return (
    <PageLayout title="Accounts" description="Manage your financial accounts">
      <PageHeader
        title="Accounts"
        description="Manage your financial accounts"
        actions={
          <Button variant="primary" onClick={() => setIsAddModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
            Add Account
          </Button>
        }
      />

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <Card variant="highlight">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Total Balance</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-white">
                  {formatCurrency(totalBalance, "CAD")}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  Across {accounts.length} accounts
                </p>
              </div>
              <div className="p-4 bg-primary-100 dark:bg-primary-900/30 rounded-xl">
                <Wallet className="w-8 h-8 text-primary-600 dark:text-primary-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Account Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8"
      >
        {accounts.map((account, index) => {
          const config = accountTypeConfig[account.type];
          const Icon = config.icon;
          return (
            <motion.div
              key={account.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
            >
              <Card variant="interactive" className="group cursor-pointer">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className={cn("p-3 rounded-xl", config.bgColor)}>
                      <Icon className={cn("w-6 h-6", config.iconColor)} />
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="capitalize">
                        {account.type}
                      </Badge>
                      <button className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreHorizontal className="w-4 h-4 text-slate-500" />
                      </button>
                    </div>
                  </div>
                  <h3 className="font-semibold text-slate-900 dark:text-white mb-1">
                    {account.name}
                  </h3>
                  {account.institution && (
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">
                      {account.institution}
                    </p>
                  )}
                  <p
                    className={cn(
                      "text-2xl font-bold",
                      account.type === "credit" || account.type === "loan"
                        ? "text-danger-600 dark:text-danger-400"
                        : "text-slate-900 dark:text-white"
                    )}
                  >
                    {account.type === "credit" || account.type === "loan" ? "-" : ""}
                    {formatCurrency(account.balance, account.currency)}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {/* Add Account Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + accounts.length * 0.05 }}
        >
          <Card
            variant="interactive"
            className="h-full border-dashed cursor-pointer"
            onClick={() => setIsAddModalOpen(true)}
          >
            <CardContent className="p-6 flex flex-col items-center justify-center h-full min-h-[180px]">
              <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-xl mb-3">
                <Plus className="w-6 h-6 text-slate-400" />
              </div>
              <p className="font-medium text-slate-600 dark:text-slate-400">Add Account</p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Coming Soon Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                <ArrowUpRight className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-white mb-1">Coming Soon</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Account management features will be available soon. You'll be able to add, edit,
                  and track multiple accounts with automatic syncing.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Add Account Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Account"
        size="md"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" disabled>
              Add Account
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input label="Account Name" placeholder="e.g., Primary Checking" disabled />
          <Select
            label="Account Type"
            options={[
              { value: "checking", label: "Checking" },
              { value: "savings", label: "Savings" },
              { value: "credit", label: "Credit Card" },
              { value: "investment", label: "Investment" },
              { value: "loan", label: "Loan" },
            ]}
            value="checking"
            onChange={() => {}}
            disabled
          />
          <Input label="Institution" placeholder="e.g., TD Bank" disabled />
          <Select
            label="Currency"
            options={[
              { value: "CAD", label: "CAD - Canadian Dollar" },
              { value: "USD", label: "USD - US Dollar" },
              { value: "BRL", label: "BRL - Brazilian Real" },
            ]}
            value="CAD"
            onChange={() => {}}
            disabled
          />
          <p className="text-sm text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg">
            Account management is coming soon. This feature will allow you to track balances
            across multiple financial institutions.
          </p>
        </div>
      </Modal>
    </PageLayout>
  );
}
