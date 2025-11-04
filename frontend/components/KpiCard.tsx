type KpiCardProps = {
  label: string;
  value: string;
  change?: string;
};

export function KpiCard({ label, value, change }: KpiCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      {change ? (
        <p className="mt-1 text-xs font-medium text-emerald-600">{change}</p>
      ) : null}
    </div>
  );
}

