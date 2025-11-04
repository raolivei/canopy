import { PropsWithChildren } from 'react';

type LayoutProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
}>;

export function Layout({ title, subtitle, children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-ledger-light">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-1 px-6 py-6">
          <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
          {subtitle ? (
            <p className="text-sm text-slate-600">{subtitle}</p>
          ) : null}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      <footer className="border-t border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto max-w-6xl px-6 py-4 text-xs text-slate-500">
          LedgerLight · Privacy-first personal finance dashboard
        </div>
      </footer>
    </div>
  );
}

