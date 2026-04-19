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
import { useMoney } from "@/hooks/useMoney";
import { useRouter } from "next/router";
import { CurrencyViewToggle } from "@/components/CurrencyViewToggle";
import {
  convertForView,
  useCurrencyView,
  viewCurrency,
} from "@/hooks/useCurrencyView";

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

interface CurrencyTotals {
  cash: number;
  debt: number;
  net: number;
}

interface CombinedTotals extends CurrencyTotals {
  currency: string;
}

interface FxInfo {
  usd_cad_rate: number | null;
  as_of_date: string | null;
  source: string | null;
  is_stale: boolean;
}

interface AccountsResponse {
  summary: {
    total_cash: number;
    total_debt: number;
    net_cash: number;
    currency: string;
  };
  accounts: Account[];
  totals_by_currency: Record<"CAD" | "USD", CurrencyTotals>;
  totals_combined: Record<"CAD" | "USD", CombinedTotals>;
  fx: FxInfo;
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
  const { view } = useCurrencyView();
  const { fmt } = useMoney();
  const { data, isLoading, error } = useQuery<AccountsResponse>({
    queryKey: ["accounts"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/accounts/`);
      if (!res.ok) throw new Error(`Failed to load accounts (${res.status})`);
      return res.json();
    },
  });

  const accounts = data?.accounts ?? [];
  const hasAccounts = accounts.length > 0;
  const totalsByCcy = data?.totals_by_currency;
  const totalsCombined = data?.totals_combined;
  const rate = data?.fx?.usd_cad_rate ?? null;

  // Compute the summary triple for the currently-selected view. The
  // backend already prepared all four buckets, so the frontend just
  // picks whichever one matches.
  const currentTotals: CurrencyTotals | undefined = (() => {
    if (!totalsByCcy || !totalsCombined) return undefined;
    switch (view) {
      case "CAD":
        return totalsByCcy.CAD;
      case "USD":
        return totalsByCcy.USD;
      case "COMBINED_CAD":
        return totalsCombined.CAD;
      case "COMBINED_USD":
        return totalsCombined.USD;
    }
  })();

  const displayCurrency = viewCurrency(view);

  return (
    <PageLayout
      title="Accounts"
      description="Cash, credit, and loans — investments live on Holdings"
    >
      <PageHeader
        title="Accounts"
        description="Cash, credit, and loans — investments live on Holdings"
        actions={
          <div className="flex items-start gap-4">
            <CurrencyViewToggle />
            <Button
              variant="primary"
              leftIcon={<UploadCloud className="w-4 h-4" />}
              onClick={() => router.push("/portfolio/wealthsimple-import")}
            >
              Import statements
            </Button>
          </div>
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

      {currentTotals && (
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
                    {fmt(currentTotals.cash, displayCurrency)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                    Total debt
                  </p>
                  <p className="text-2xl font-bold text-danger-600 dark:text-danger-400">
                    {fmt(currentTotals.debt, displayCurrency)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                    Net cash position
                  </p>
                  <p
                    className={cn(
                      "text-2xl font-bold",
                      currentTotals.net >= 0
                        ? "text-slate-900 dark:text-white"
                        : "text-danger-600 dark:text-danger-400",
                    )}
                  >
                    {fmt(currentTotals.net, displayCurrency)}
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
            // Questrade-style: account cards always show the *native*
            // balance in the account's own currency, with the currency
            // code prominently displayed. The top-line summary is what
            // rolls up to the selected view.
            const native = account.currency || "CAD";
            // When a single-currency view is active and the account is
            // in the other currency, fade it so the user can see what's
            // being excluded at a glance.
            const excluded =
              (view === "CAD" && native !== "CAD") ||
              (view === "USD" && native !== "USD");
            const viewedAmount = convertForView(
              account.balance,
              native,
              view,
              rate,
            );
            return (
              <motion.div
                key={account.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 + index * 0.03 }}
                className={cn(excluded && "opacity-40")}
              >
                <Card variant="interactive" className="h-full">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className={cn("p-3 rounded-xl", config.bgColor)}>
                        <Icon className={cn("w-6 h-6", config.iconColor)} />
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{native}</Badge>
                        <Badge variant="secondary">{config.label}</Badge>
                      </div>
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
                      {fmt(account.balance, native)}
                    </p>
                    {/* Show the converted figure below only when the
                        view isn't already the native currency — keeps
                        the card from repeating itself. */}
                    {!excluded &&
                      (view === "COMBINED_CAD" || view === "COMBINED_USD") &&
                      displayCurrency !== native && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          ≈ {fmt(viewedAmount, displayCurrency)} @ FX
                        </p>
                      )}
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
