import { useState } from "react";
import Head from "next/head";
import PageLayout from "@/components/layout/PageLayout";
import { Card } from "@/components/ui/Card";

export default function RecurringPage() {
  const [recurring, setRecurring] = useState([]);

  return (
    <>
      <Head>
        <title>Recurring Transactions — Canopy</title>
      </Head>
      <PageLayout title="Recurring Transactions">
        <div className="space-y-4">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Recurring Transactions</h2>
            <p className="text-slate-600 dark:text-slate-400">
              Coming soon: Identify and manage your recurring expenses and income.
            </p>
          </Card>
        </div>
      </PageLayout>
    </>
  );
}
