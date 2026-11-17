import Link from "next/link";
import { FileText, FolderLock, ListChecks, ScrollText } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";

const PLANNED = [
  {
    icon: FolderLock,
    title: "Document vault",
    body: "Slips, receipts, filed returns and assessment notices stored privately, versioned and deduplicated.",
  },
  {
    icon: ScrollText,
    title: "Yearly ledger",
    body: "Reported versus assessed amounts, payments, refunds and interest per tax year, each line backed by a document.",
  },
  {
    icon: ListChecks,
    title: "Actions and deadlines",
    body: "Correspondence by case, requested information, stated deadlines and your draft responses across years.",
  },
  {
    icon: FileText,
    title: "Accountant export",
    body: "Originals, structured facts and a reviewed summary bundled for your accountant or filing software.",
  },
];

/**
 * Landing content for the Tax workspace while it is being built.
 * Deliberately shows no figures: nothing here is derived from your data yet.
 */
export function TaxOverview() {
  return (
    <div className="space-y-6">
      <Card variant="highlight">
        <CardHeader>
          <CardTitle>The Tax workspace is not available yet</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
          <p>
            Tax will organise your records and correspondence by tax year and keep an evidence-backed ledger of
            what was reported, assessed, paid and refunded. It shares accounts, settings and search with Wallet.
          </p>
          <p>
            Nothing on this page is computed from your data. Until the first release, Wallet remains the place for
            transactions, budgets and cash flow.{" "}
            <Link href="/" className="font-medium text-primary-700 dark:text-primary-300 underline-offset-2 hover:underline">
              Back to Wallet
            </Link>
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {PLANNED.map(({ icon: Icon, title, body }) => (
          <Card key={title}>
            <CardContent className="flex gap-3 p-5">
              <div className="mt-0.5 rounded-lg bg-slate-100 p-2 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                <Icon className="h-5 w-5" aria-hidden />
              </div>
              <div>
                <h3 className="font-medium text-slate-900 dark:text-white">{title}</h3>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{body}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
