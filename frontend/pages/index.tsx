import Head from 'next/head';

import { KpiCard } from '../components/KpiCard';
import { Layout } from '../components/Layout';

const mockBudget = [
  { label: 'Essentials', spent: '$1,240', budget: '$1,500' },
  { label: 'Investments', spent: '$650', budget: '$800' },
  { label: 'Discretionary', spent: '$310', budget: '$600' }
];

export default function Home() {
  return (
    <>
      <Head>
        <title>LedgerLight Dashboard</title>
        <meta
          content="Unified budgeting and investment insights for your homelab."
          name="description"
        />
      </Head>
      <Layout title="LedgerLight" subtitle="Unified personal finance command center">
        <section className="grid gap-4 md:grid-cols-3">
          <KpiCard label="Net Worth" value="$245,200" change="+4.2% MoM" />
          <KpiCard label="30D Spending" value="$2,200" change="-3.8% vs avg" />
          <KpiCard label="Invested" value="$178,450" change="+2.1% WoW" />
        </section>
        <section className="mt-10">
          <h2 className="text-lg font-semibold text-slate-800">
            Budget Snapshot
          </h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            {mockBudget.map((category) => (
              <div
                key={category.label}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <p className="text-sm text-slate-500">{category.label}</p>
                <p className="mt-2 text-xl font-semibold text-slate-900">{category.spent}</p>
                <p className="mt-1 text-xs text-slate-500">
                  of <span className="font-medium text-slate-700">{category.budget}</span>
                </p>
              </div>
            ))}
          </div>
        </section>
      </Layout>
    </>
  );
}

