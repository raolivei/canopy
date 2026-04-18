import React from "react";
import { useQuery } from "@tanstack/react-query";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonMetricCard } from "@/components/ui/Skeleton";
import {
  Wallet,
  CreditCard,
  Building2,
  PiggyBank,
  AlertCircle,
  UploadCloud,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/utils/cn";
import { formatCurrency } from "@/utils/currency";
import { useRouter } from "next/router";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

type AccountKind =
  | "checking"
  | "savings"
  | "cash"
  | "credit"
  | "loan"
  | "line_of_credit";

interface Account {
  id: string;
  name: string;
  kind: AccountKind;
  balance: number;
  currency: string;
  institution?: string | null;
  external_account_id?: string | null;
  last4?: string | null;
  source?: string | null;
  updated_at?: string | null;
}

interface AccountsResponse {
  summary: {
    total_cash: number;
    total_debt: number;
    net_cash: number;
    currency: string;
  };
  accounts: Account[];
}

const accountTypeConfig: Record<
  AccountKind,
  { icon: React.ElementType; bgColor: string; iconColor: string; label: string }
> = {
  checking: {
    icon: Building2,
    bgColor: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
    label: "Checking",
  },
  savings: {
    icon: PiggyBank,
    bgColor: "bg-success-100 dark:bg-success-900/30",
    iconColor: "text-success-600 dark:text-success-400",
    label: "Savings",
  },
  cash: {
    icon: Wallet,
    bgColor: "bg-slate-100 dark:bg-slate-800",
    iconColor: "text-slate-600 dark:text-slate-300",
    label: "Cash",
  },
  credit: {
    icon: CreditCard,
    bgColor: "bg-purple-100 dark:bg-purple-900/30",
    iconColor: "text-purple-600 dark:text-purple-400",
    label: "Credit Card",
  },
  line_of_credit: {
    icon: CreditCard,
    bgColor: "bg-orange-100 dark:bg-orange-900/30",
    iconColor: "text-orange-600 dark:text-orange-400",
    label: "Line of Credit",
  },
  loan: {
    icon: AlertCircle,
    bgColor: "bg-danger-100 dark:bg-danger-900/30",
    iconColor: "text-danger-600 dark:text-danger-400",
    label: "Loan",
  },
};

const isDebtKind = (kind: AccountKind) =>
  kind === "credit" || kind === "loan" || kind === "line_of_credit";

export default function Accounts() {
  const router = useRouter();
  const { data, isLoading, error } = useQuery<AccountsResponse>({
    queryKey: ["accounts"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/accounts/`);
      if (!res.ok) throw new Error(`Failed to load accounts (${res.status})`);
      return res.json();
    },
  });

  const accounts = data?.accounts ?? [];
  const summary = data?.summary;
  const hasAccounts = accounts.length > 0;

  return (
    <PageLayout
      title="Accounts"
      description="Cash, credit, and loans — investments live on Holdings"
    >
      <PageHeader
        title="Accounts"
        description="Cash, credit, and loans — investments live on Holdings"
        actions={
          <Button
            variant="primary"
            leftIcon={<UploadCloud className="w-4 h-4" />}
            onClick={() => router.push("/portfolio/wealthsimple-import")}
          >
            Import statements
          </Button>
        }
      />

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <SkeletonMetricCard />
          <SkeletonMetricCard />
          <SkeletonMetricCard />
        </div>
      )}

      {error && (
        <Card className="mb-6">
          <CardContent className="p-6 text-sm text-danger-600 dark:text-danger-400">
            {(error as Error).message}
          </CardContent>
        </Card>
      )}

      {summary && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card variant="highlight">
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                    Total cash
                  </p>
                  <p className="text-2xl font-bold text-success-600 dark:text-success-400">
                    {formatCurrency(summary.total_cash, "CAD")}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                    Total debt
                  </p>
                  <p className="text-2xl font-bold text-danger-600 dark:text-danger-400">
                    {formatCurrency(summary.total_debt, "CAD")}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                    Net cash position
                  </p>
                  <p
                    className={cn(
                      "text-2xl font-bold",
                      summary.net_cash >= 0
                        ? "text-slate-900 dark:text-white"
                        : "text-danger-600 dark:text-danger-400",
                    )}
                  >
                    {formatCurrency(summary.net_cash, "CAD")}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {!isLoading && !hasAccounts && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardContent className="p-10 text-center">
              <div className="inline-flex p-3 bg-slate-100 dark:bg-slate-800 rounded-xl mb-4">
                <Wallet className="w-8 h-8 text-slate-500" />
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                No accounts yet
              </h2>
              <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-6">
                Drop a Wealthsimple monthly statement and Canopy will create your
                chequing, credit card, and line of credit accounts automatically.
              </p>
              <Button
                variant="primary"
                leftIcon={<UploadCloud className="w-4 h-4" />}
                onClick={() => router.push("/portfolio/wealthsimple-import")}
              >
                Import Wealthsimple CSVs
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {hasAccounts && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {accounts.map((account, index) => {
            const config = accountTypeConfig[account.kind];
            const Icon = config.icon;
            const debt = isDebtKind(account.kind);
            return (
              <motion.div
                key={account.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 + index * 0.03 }}
              >
                <Card variant="interactive" className="h-full">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className={cn("p-3 rounded-xl", config.bgColor)}>
                        <Icon className={cn("w-6 h-6", config.iconColor)} />
                      </div>
                      <Badge variant="secondary">{config.label}</Badge>
                    </div>
                    <h3 className="font-semibold text-slate-900 dark:text-white mb-1 truncate">
                      {account.name}
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-3 truncate">
                      {[account.institution, account.last4 && `•••• ${account.last4}`]
                        .filter(Boolean)
                        .join(" · ") || "—"}
                    </p>
                    <p
                      className={cn(
                        "text-2xl font-bold",
                        debt
                          ? "text-danger-600 dark:text-danger-400"
                          : "text-slate-900 dark:text-white",
                      )}
                    >
                      {debt ? "-" : ""}
                      {formatCurrency(account.balance, account.currency || "CAD")}
                    </p>
                    {account.source && (
                      <p className="text-xs text-slate-400 mt-2 capitalize">
                        Synced from {account.source}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </PageLayout>
  );
}
