import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import PageLayout from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonChart, SkeletonMetricCard } from "@/components/ui/Skeleton";
import {
  TrendingUp,
  TrendingDown,
  Upload,
  ArrowRight,
  RefreshCw,
  UploadCloud,
  Wallet,
  PiggyBank,
  CreditCard,
  Sparkles,
} from "lucide-react";
import {
  ComposedChart,
  Area,
  Line,
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { format } from "date-fns";
import { useMoney } from "@/hooks/useMoney";
import { motion } from "framer-motion";
import { useRouter } from "next/router";
import { PeriodSelector } from "@/components/ui/PeriodSelector";
import { filterByPeriod, TimePeriod } from "@/utils/dateFiltering";
import {
  CHART_COLORS,
  CHART_PALETTE,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";
import { CurrencyViewToggle } from "@/components/CurrencyViewToggle";
import {
  CurrencyView,
  useCurrencyView,
  viewCurrency,
} from "@/hooks/useCurrencyView";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";
const CAD = "CAD";

interface TimelinePoint {
  id: number;
  as_of_date: string;
  total_value_cad: string | null;
}

interface AllocationSlice {
  key: string;
  value_cad: string;
  pct: number;
}

interface AllocationResponse {
  review_id: number;
  group_by: string;
  total_cad: string;
  slices: AllocationSlice[];
}

interface CompareResponse {
  total_cad_delta: string | null;
  pct_change: number | null;
}

interface NetWorthSlice {
  investments: string;
  cash: string;
  debt: string;
  net_worth: string;
  currency: string;
}

interface NetWorthPoint {
  date: string;
  // Legacy CAD-native fields (kept for back-compat; equal to ``cad``).
  investments: string;
  cash: string;
  debt: string;
  net_worth: string;
  cad: NetWorthSlice;
  usd: NetWorthSlice;
  combined_cad: NetWorthSlice;
  combined_usd: NetWorthSlice;
  fx_rate: string | null;
}

interface NetWorthResponse {
  points: NetWorthPoint[];
  latest_investments: string;
  latest_cash: string;
  latest_debt: string;
  latest_net_worth: string;
  latest_cad: NetWorthSlice | null;
  latest_usd: NetWorthSlice | null;
  latest_combined_cad: NetWorthSlice | null;
  latest_combined_usd: NetWorthSlice | null;
  fx_rate: string | null;
  fx_as_of_date: string | null;
  fx_is_stale: boolean;
}

/** Pick the slice of a net-worth point that matches the selected view. */
function pickSlice(point: NetWorthPoint, view: CurrencyView): NetWorthSlice {
  switch (view) {
    case "CAD":
      return point.cad;
    case "USD":
      return point.usd;
    case "COMBINED_CAD":
      return point.combined_cad;
    case "COMBINED_USD":
      return point.combined_usd;
  }
}

function pickLatestSlice(
  response: NetWorthResponse,
  view: CurrencyView,
): NetWorthSlice | null {
  switch (view) {
    case "CAD":
      return response.latest_cad;
    case "USD":
      return response.latest_usd;
    case "COMBINED_CAD":
      return response.latest_combined_cad;
    case "COMBINED_USD":
      return response.latest_combined_usd;
  }
}

export default function Dashboard() {
  const router = useRouter();
  const { view } = useCurrencyView();
  const { fmt, pct } = useMoney();
  const displayCurrency = viewCurrency(view);
  const [loading, setLoading] = useState(true);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [platformAlloc, setPlatformAlloc] = useState<AllocationResponse | null>(null);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [netWorth, setNetWorth] = useState<NetWorthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [networthPeriod, setNetworthPeriod] = useState<TimePeriod>("all");

  const latestId = timeline.length ? timeline[timeline.length - 1].id : null;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const tlRes = await fetch(`${API_URL}/v1/portfolio-reviews/timeline`);
      if (!tlRes.ok) throw new Error("Could not load portfolio reviews");
      const tl: TimelinePoint[] = await tlRes.json();
      setTimeline(tl);

      const last = tl.length ? tl[tl.length - 1] : null;
      if (last) {
        const pRes = await fetch(
          `${API_URL}/v1/portfolio-reviews/${last.id}/allocation?group_by=platform`,
        );
        if (pRes.ok) setPlatformAlloc(await pRes.json());
      } else {
        setPlatformAlloc(null);
      }

      if (tl.length >= 2) {
        const a = tl[tl.length - 2].id;
        const b = tl[tl.length - 1].id;
        const cRes = await fetch(
          `${API_URL}/v1/portfolio-reviews/compare?from_id=${a}&to_id=${b}`
        );
        if (cRes.ok) setCompare(await cRes.json());
        else setCompare(null);
      } else {
        setCompare(null);
      }

      try {
        const nwRes = await fetch(
          `${API_URL}/v1/wealthsimple-import/networth-timeline`
        );
        if (nwRes.ok) {
          const data: NetWorthResponse = await nwRes.json();
          setNetWorth(data.points.length > 0 ? data : null);
        } else {
          setNetWorth(null);
        }
      } catch {
        setNetWorth(null);
      }
    } catch (e) {
      console.error(e);
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const lineData = useMemo(
    () =>
      timeline.map((p) => ({
        date: format(new Date(p.as_of_date), "MMM yyyy"),
        total: p.total_value_cad ? parseFloat(p.total_value_cad) : 0,
      })),
    [timeline]
  );

  const networthData = useMemo(() => {
    if (!netWorth) return [];

    // First, map to chart format
    const mapped = (netWorth.points ?? []).map((p) => {
      const slice = pickSlice(p, view);
      return {
        date: format(new Date(p.date), "MMM yyyy"),
        rawDate: p.date, // Keep original date for filtering
        investments: parseFloat(slice.investments),
        cash: parseFloat(slice.cash),
        /** Debt magnitude (positive) — shown on its own axis vs. asset stack. */
        debt_abs: Math.abs(parseFloat(slice.debt)),
        net_worth: parseFloat(slice.net_worth),
      };
    });

    // Then, filter by period
    return filterByPeriod(mapped, (item) => item.rawDate, networthPeriod);
  }, [netWorth, view, networthPeriod]);

  const latestTotal = latestId
    ? timeline.find((t) => t.id === latestId)?.total_value_cad
    : null;
  const latestNum = latestTotal ? parseFloat(latestTotal) : 0;

  const pieColors = CHART_PALETTE.length ? CHART_PALETTE : [CHART_COLORS.primary, CHART_COLORS.success, CHART_COLORS.accent];

  if (loading) {
    return (
      <PageLayout title="Dashboard">
        <BrandHeader />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <SkeletonMetricCard />
          <SkeletonMetricCard />
          <SkeletonMetricCard />
          <SkeletonMetricCard />
        </div>
        <SkeletonChart />
      </PageLayout>
    );
  }

  // Net-worth numbers (primary hero when available) — pick the slice
  // that matches the currently-selected Questrade-style currency view.
  const hasNetWorth = !!netWorth;
  const latestSlice = hasNetWorth ? pickLatestSlice(netWorth!, view) : null;
  const nwValue = latestSlice ? parseFloat(latestSlice.net_worth) : 0;
  const nwInvestments = latestSlice ? parseFloat(latestSlice.investments) : 0;
  const nwCash = latestSlice ? parseFloat(latestSlice.cash) : 0;
  const nwDebt = latestSlice ? parseFloat(latestSlice.debt) : 0;

  // Month-over-month delta for net worth, computed in the selected
  // view so a CAD-only switch shows a CAD-only delta.
  const nwDelta = (() => {
    const pts = netWorth?.points ?? [];
    if (pts.length < 2) return null;
    const prev = parseFloat(pickSlice(pts[pts.length - 2], view).net_worth);
    const now = parseFloat(pickSlice(pts[pts.length - 1], view).net_worth);
    if (!isFinite(prev) || prev === 0) return null;
    const absDelta = now - prev;
    const pctDelta = (absDelta / Math.abs(prev)) * 100;
    return { abs: absDelta, pct: pctDelta };
  })();

  return (
    <PageLayout
      title="Dashboard"
      description="Continuous net-worth tracking across Wealthsimple statements and portfolio snapshots"
    >
      <BrandHeader
        actions={
          <>
            <CurrencyViewToggle />
            <Button
              variant="primary"
              leftIcon={<UploadCloud className="w-4 h-4" />}
              onClick={() => router.push("/portfolio/wealthsimple-import")}
            >
              Wealthsimple
            </Button>
            <Button
              variant="secondary"
              leftIcon={<UploadCloud className="w-4 h-4" />}
              onClick={() => router.push("/portfolio/monarch-import")}
            >
              Monarch
            </Button>
            <Button
              variant="ghost"
              leftIcon={<Upload className="w-4 h-4" />}
              onClick={() => router.push("/portfolio/import")}
            >
              Snapshot
            </Button>
            <Button
              variant="ghost"
              leftIcon={<RefreshCw className="w-4 h-4" />}
              onClick={() => load()}
              aria-label="Refresh"
            >
              <span className="sr-only">Refresh</span>
            </Button>
          </>
        }
      />

      {hasNetWorth && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card variant="highlight" className="overflow-hidden">
            <div className="p-8 bg-gradient-to-br from-primary-50 via-white to-emerald-50 dark:from-primary-950/40 dark:via-slate-900 dark:to-emerald-950/30">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                    <p className="text-sm font-medium text-primary-700 dark:text-primary-300 uppercase tracking-wide">
                      Net worth
                    </p>
                  </div>
                  <h2 className="text-5xl lg:text-6xl font-semibold tracking-tight text-slate-900 dark:text-white mb-3">
                    {fmt(nwValue, displayCurrency)}
                  </h2>
                  <div className="flex flex-wrap items-center gap-3">
                    {nwDelta && (
                      <Badge
                        variant={nwDelta.abs >= 0 ? "success" : "danger"}
                        className="text-sm"
                      >
                        {nwDelta.abs >= 0 ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        )}
                        {nwDelta.abs >= 0 ? "+" : ""}
                        {fmt(nwDelta.abs, displayCurrency)} ({nwDelta.pct >= 0 ? "+" : ""}
                        {pct(nwDelta.pct, 2)}) vs last month
                      </Badge>
                    )}
                    <span className="text-sm text-slate-500 dark:text-slate-400">
                      {(netWorth!.points?.length ?? 0)} month
                      {(netWorth!.points?.length ?? 0) === 1 ? "" : "s"} of data
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <NetWorthTile
              label="Investments"
              value={nwInvestments}
              icon={<PiggyBank className="w-4 h-4" />}
              accent="primary"
              currency={displayCurrency}
              format={fmt}
            />
            <NetWorthTile
              label="Cash"
              value={nwCash}
              icon={<Wallet className="w-4 h-4" />}
              accent="success"
              currency={displayCurrency}
              format={fmt}
            />
            <NetWorthTile
              label="Debt"
              value={nwDebt}
              icon={<CreditCard className="w-4 h-4" />}
              accent="danger"
              negative
              currency={displayCurrency}
              format={fmt}
            />
          </div>
        </motion.div>
      )}

      {error && (
        <p className="text-sm text-danger-600 dark:text-danger-400 mb-4">{error}</p>
      )}

      {hasNetWorth && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.03 }}
          className="mb-8"
        >
            <Card>
              <CardHeader>
                <CardTitle>Net worth over time</CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  Stacked areas = assets you own (investments + cash). Red line =
                  total debt (separate scale). Bold line = net worth. Data from
                  Wealthsimple uploads — {displayCurrency}
                </p>
              </CardHeader>

              {/* Period Selector */}
              <div className="px-6 pb-4">
                <PeriodSelector
                  selectedPeriod={networthPeriod}
                  onPeriodChange={setNetworthPeriod}
                />
              </div>

              <CardContent>
                {networthData.length === 0 ? (
                  <div className="h-80 flex items-center justify-center text-slate-500 dark:text-slate-400">
                    No data available for selected period
                  </div>
                ) : (
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={networthData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid {...getGridProps(checkDarkMode())} />
                      <XAxis
                        dataKey="date"
                        {...getAxisProps(checkDarkMode())}
                      />
                      <YAxis
                        yAxisId="left"
                        {...getAxisProps(checkDarkMode())}
                        tickFormatter={(v) => fmt(v as number, displayCurrency)}
                        width={56}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        {...getAxisProps(checkDarkMode())}
                        tickFormatter={(v) => fmt(v as number, displayCurrency)}
                        width={56}
                      />
                      <Tooltip
                        contentStyle={getTooltipStyle(checkDarkMode())}
                        formatter={(v: number, name: string) => [
                          fmt(v, displayCurrency),
                          name,
                        ]}
                      />
                      <Legend />
                      <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="investments"
                        name="Investments (assets)"
                        stackId="assets"
                        stroke={CHART_COLORS.primary}
                        fill={CHART_COLORS.primary}
                        fillOpacity={0.55}
                      />
                      <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="cash"
                        name="Cash (assets)"
                        stackId="assets"
                        stroke={CHART_COLORS.success}
                        fill={CHART_COLORS.success}
                        fillOpacity={0.5}
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="debt_abs"
                        name="Debt (owed)"
                        stroke={CHART_COLORS.danger}
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="net_worth"
                        name="Net worth"
                        stroke={CHART_COLORS.accent}
                        strokeWidth={2.5}
                        dot={{ r: 3 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                )}
              </CardContent>
            </Card>
        </motion.div>
      )}

      {!hasNetWorth && !latestId && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card className="overflow-hidden">
            <div className="p-10 lg:p-14 text-center bg-gradient-to-br from-primary-50/60 via-white to-emerald-50/40 dark:from-primary-950/30 dark:via-slate-900 dark:to-emerald-950/20">
              <img
                src="/brand/canopy-icon.svg"
                alt="Canopy"
                className="w-24 h-24 mx-auto mb-6 rounded-2xl shadow-lg ring-1 ring-slate-200/50 dark:ring-slate-800/50"
              />
              <h2 className="text-2xl lg:text-3xl font-semibold text-slate-900 dark:text-white mb-2">
                Welcome to Canopy
              </h2>
              <p className="text-slate-600 dark:text-slate-400 max-w-lg mx-auto mb-8">
                One number for your net worth, built from every account you own.
                Start with Wealthsimple monthly statements, backfill history
                from Monarch Money, or import a dated portfolio snapshot for
                holdings that don&rsquo;t auto-sync.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <Button
                  variant="primary"
                  size="lg"
                  leftIcon={<UploadCloud className="w-4 h-4" />}
                  onClick={() => router.push("/portfolio/wealthsimple-import")}
                >
                  Drop Wealthsimple CSVs
                </Button>
                <Button
                  variant="secondary"
                  size="lg"
                  leftIcon={<UploadCloud className="w-4 h-4" />}
                  onClick={() => router.push("/portfolio/monarch-import")}
                >
                  Import from Monarch
                </Button>
                <Button
                  variant="ghost"
                  size="lg"
                  leftIcon={<Upload className="w-4 h-4" />}
                  onClick={() => router.push("/portfolio/import")}
                >
                  Portfolio snapshot
                </Button>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {latestId && lineData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="mb-8"
        >
          <Card>
            <CardHeader>
              <CardTitle>Portfolio snapshot — total CAD</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Canadian holdings that don&apos;t auto-sync from Wealthsimple (private equity, real estate, DPSP)
                {latestNum > 0 && (
                  <> — latest review {fmt(latestNum, CAD)}</>
                )}
              </p>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineData}>
                    <CartesianGrid {...getGridProps(checkDarkMode())} />
                    <XAxis dataKey="date" {...getAxisProps(checkDarkMode())} />
                    <YAxis
                      {...getAxisProps(checkDarkMode())}
                      tickFormatter={(v) => fmt(v as number, CAD)}
                    />
                    <Tooltip
                      contentStyle={getTooltipStyle(checkDarkMode())}
                      formatter={(v: number) => [fmt(v, CAD), "Total CAD"]}
                    />
                    <Line
                      type="monotone"
                      dataKey="total"
                      stroke={CHART_COLORS.primary}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {latestId && platformAlloc && platformAlloc.slices.length > 0 && (
        <div className="grid grid-cols-1 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="h-full">
              <CardHeader>
                <CardTitle>By platform</CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  Latest review — {fmt(parseFloat(platformAlloc.total_cad), CAD)} total
                </p>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={platformAlloc.slices.map((s) => ({
                          name: s.key,
                          value: parseFloat(s.value_cad),
                        }))}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={2}
                      >
                        {platformAlloc.slices.map((slice, i) => (
                          <Cell
                            key={slice.key}
                            fill={pieColors[i % pieColors.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={getTooltipStyle(checkDarkMode())}
                        formatter={(v: number, name: string) => [
                          fmt(v, CAD),
                          name,
                        ]}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Budget & transactions</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Cash flow and bank CSV tools (optional)
              </p>
            </div>
            <Link href="/transactions">
              <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Open
              </Button>
            </Link>
          </CardHeader>
        </Card>
      </motion.div>
    </PageLayout>
  );
}

function BrandHeader({ actions }: { actions?: React.ReactNode } = {}) {
  return (
    <div className="mb-6 lg:mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <img
            src="/brand/canopy-icon.svg"
            alt="Canopy"
            className="w-14 h-14 rounded-xl shadow-md ring-1 ring-slate-200/60 dark:ring-slate-700/60"
          />
          <div>
            <h1 className="text-2xl lg:text-3xl font-semibold tracking-tight text-slate-900 dark:text-white leading-none">
              Canopy
            </h1>
            <p className="mt-1.5 text-sm text-primary-700 dark:text-primary-300">
              Continuous net-worth tracking
            </p>
          </div>
        </div>
        {actions && (
          <div className="flex flex-wrap items-center gap-2">{actions}</div>
        )}
      </div>
    </div>
  );
}

type TileAccent = "primary" | "success" | "danger" | "neutral";

const ACCENT_STYLES: Record<
  TileAccent,
  { iconBg: string; iconFg: string; valueText: string }
> = {
  primary: {
    iconBg: "bg-primary-100 dark:bg-primary-950/50",
    iconFg: "text-primary-600 dark:text-primary-400",
    valueText: "text-slate-900 dark:text-white",
  },
  success: {
    iconBg: "bg-success-100 dark:bg-success-950/50",
    iconFg: "text-success-600 dark:text-success-400",
    valueText: "text-slate-900 dark:text-white",
  },
  danger: {
    iconBg: "bg-danger-100 dark:bg-danger-950/50",
    iconFg: "text-danger-600 dark:text-danger-400",
    valueText: "text-danger-700 dark:text-danger-400",
  },
  neutral: {
    iconBg: "bg-slate-100 dark:bg-slate-800",
    iconFg: "text-slate-600 dark:text-slate-400",
    valueText: "text-slate-900 dark:text-white",
  },
};

function NetWorthTile({
  label,
  value,
  icon,
  accent = "neutral",
  emphasis = false,
  negative = false,
  currency = "CAD",
  format,
}: {
  label: string;
  value: number;
  icon?: React.ReactNode;
  accent?: TileAccent;
  emphasis?: boolean;
  negative?: boolean;
  currency?: string;
  format: (amount: number, currencyCode?: string) => string;
}) {
  const displayValue = negative ? -Math.abs(value) : value;
  const styles = ACCENT_STYLES[accent];
  return (
    <Card variant={emphasis ? "highlight" : "default"} className="group transition-shadow hover:shadow-md">
      <CardContent className="py-5">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {icon && (
            <span
              className={`inline-flex items-center justify-center w-6 h-6 rounded-md ${styles.iconBg} ${styles.iconFg}`}
            >
              {icon}
            </span>
          )}
          <span>{label}</span>
        </div>
        <div
          className={`mt-2 font-semibold tracking-tight ${
            emphasis ? "text-3xl" : "text-2xl"
          } ${negative ? styles.valueText : "text-slate-900 dark:text-white"}`}
        >
          {format(displayValue, currency)}
        </div>
      </CardContent>
    </Card>
  );
}
