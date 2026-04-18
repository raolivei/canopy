import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
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
  LineChart as LineChartIcon,
} from "lucide-react";
import {
  LineChart,
  Line,
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
import { formatCurrency } from "@/utils/currency";
import { motion } from "framer-motion";
import { useRouter } from "next/router";
import {
  CHART_COLORS,
  CHART_PALETTE,
  getTooltipStyle,
  getGridProps,
  getAxisProps,
  isDarkMode as checkDarkMode,
} from "@/utils/chartTheme";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";
const USD = "USD";

interface TimelinePoint {
  id: number;
  as_of_date: string;
  total_value_usd: string | null;
}

interface AllocationSlice {
  key: string;
  value_usd: string;
  pct: number;
}

interface AllocationResponse {
  review_id: number;
  group_by: string;
  total_usd: string;
  slices: AllocationSlice[];
}

interface CompareResponse {
  total_usd_delta: string | null;
  pct_change: number | null;
}

interface NetWorthPoint {
  date: string;
  investments: string;
  cash: string;
  debt: string;
  net_worth: string;
}

interface NetWorthResponse {
  points: NetWorthPoint[];
  latest_investments: string;
  latest_cash: string;
  latest_debt: string;
  latest_net_worth: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [regionAlloc, setRegionAlloc] = useState<AllocationResponse | null>(null);
  const [platformAlloc, setPlatformAlloc] = useState<AllocationResponse | null>(null);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [netWorth, setNetWorth] = useState<NetWorthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        const [rRes, pRes] = await Promise.all([
          fetch(`${API_URL}/v1/portfolio-reviews/${last.id}/allocation?group_by=region`),
          fetch(`${API_URL}/v1/portfolio-reviews/${last.id}/allocation?group_by=platform`),
        ]);
        if (rRes.ok) setRegionAlloc(await rRes.json());
        if (pRes.ok) setPlatformAlloc(await pRes.json());
      } else {
        setRegionAlloc(null);
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
        total: p.total_value_usd ? parseFloat(p.total_value_usd) : 0,
      })),
    [timeline]
  );

  const networthData = useMemo(
    () =>
      (netWorth?.points ?? []).map((p) => ({
        date: format(new Date(p.date), "MMM yyyy"),
        investments: parseFloat(p.investments),
        cash: parseFloat(p.cash),
        debt: -Math.abs(parseFloat(p.debt)),
        net_worth: parseFloat(p.net_worth),
      })),
    [netWorth]
  );

  const CAD = "CAD";

  const latestTotal = latestId
    ? timeline.find((t) => t.id === latestId)?.total_value_usd
    : null;
  const latestNum = latestTotal ? parseFloat(latestTotal) : 0;

  const pieColors = CHART_PALETTE.length ? CHART_PALETTE : [CHART_COLORS.primary, CHART_COLORS.success, CHART_COLORS.accent];

  if (loading) {
    return (
      <PageLayout title="Dashboard">
        <PageHeader title="Portfolio review" description="Semi-annual snapshot progress" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <SkeletonMetricCard />
          <SkeletonMetricCard />
        </div>
        <SkeletonChart />
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Dashboard" description="Portfolio allocation and progress across reviews">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <Card variant="highlight" className="p-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <p className="text-sm font-medium text-primary-700 dark:text-primary-300 mb-1">
                Portfolio (review, USD)
              </p>
              <h1 className="text-4xl lg:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white mb-2">
                {latestId
                  ? formatCurrency(latestNum, USD)
                  : "No reviews yet"}
              </h1>
              <div className="flex flex-wrap items-center gap-2">
                {compare?.pct_change != null && (
                  <Badge
                    variant={compare.pct_change >= 0 ? "success" : "danger"}
                    className="text-sm"
                  >
                    {compare.pct_change >= 0 ? (
                      <TrendingUp className="w-3 h-3 mr-1" />
                    ) : (
                      <TrendingDown className="w-3 h-3 mr-1" />
                    )}
                    {compare.pct_change >= 0 ? "+" : ""}
                    {compare.pct_change.toFixed(2)}% vs last review
                  </Badge>
                )}
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {timeline.length} snapshot{timeline.length === 1 ? "" : "s"} imported
                </span>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="primary"
                leftIcon={<Upload className="w-4 h-4" />}
                onClick={() => router.push("/portfolio/import")}
              >
                Import snapshot
              </Button>
              <Button
                variant="secondary"
                leftIcon={<RefreshCw className="w-4 h-4" />}
                onClick={() => load()}
              >
                Refresh
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>

      {error && (
        <p className="text-sm text-danger-600 dark:text-danger-400 mb-4">{error}</p>
      )}

      {netWorth && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.03 }}
          className="mb-8"
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <NetWorthTile
              label="Net worth"
              value={parseFloat(netWorth.latest_net_worth)}
              emphasis
            />
            <NetWorthTile
              label="Investments"
              value={parseFloat(netWorth.latest_investments)}
            />
            <NetWorthTile
              label="Cash"
              value={parseFloat(netWorth.latest_cash)}
            />
            <NetWorthTile
              label="Debt"
              value={parseFloat(netWorth.latest_debt)}
              negative
            />
          </div>

          {networthData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Net worth over time</CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  Built from Wealthsimple statement uploads (investments + cash
                  minus debt)
                </p>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={networthData}>
                      <CartesianGrid {...getGridProps(checkDarkMode())} />
                      <XAxis
                        dataKey="date"
                        {...getAxisProps(checkDarkMode())}
                      />
                      <YAxis
                        {...getAxisProps(checkDarkMode())}
                        tickFormatter={(v) =>
                          formatCurrency(v as number, CAD)
                        }
                      />
                      <Tooltip
                        contentStyle={getTooltipStyle(checkDarkMode())}
                        formatter={(v: number, name: string) => [
                          formatCurrency(v, CAD),
                          name,
                        ]}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="investments"
                        stroke={CHART_COLORS.primary}
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="cash"
                        stroke={CHART_COLORS.success}
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="debt"
                        stroke={CHART_COLORS.danger}
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="net_worth"
                        stroke={CHART_COLORS.accent}
                        strokeWidth={3}
                        dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      )}

      {!latestId && (
        <Card className="mb-8">
          <CardContent className="py-12 text-center">
            <LineChartIcon className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
            <p className="text-slate-600 dark:text-slate-400 mb-6 max-w-md mx-auto">
              Import your semi-annual spreadsheet (Brazil / Canada / Crypto sections) to see
              allocation charts and progress over time.
            </p>
            <Button variant="primary" onClick={() => router.push("/portfolio/import")}>
              Import portfolio CSV
            </Button>
          </CardContent>
        </Card>
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
              <CardTitle>Total USD over reviews</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                From imported snapshots (as-of dates)
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
                      tickFormatter={(v) => formatCurrency(v as number, USD)}
                    />
                    <Tooltip
                      contentStyle={getTooltipStyle(checkDarkMode())}
                      formatter={(v: number) => [formatCurrency(v, USD), "Total USD"]}
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

      {latestId && (regionAlloc || platformAlloc) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {[regionAlloc, platformAlloc].map(
            (alloc, idx) =>
              alloc &&
              alloc.slices.length > 0 && (
                <motion.div
                  key={alloc.group_by}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + idx * 0.05 }}
                >
                  <Card className="h-full">
                    <CardHeader>
                      <CardTitle>
                        {alloc.group_by === "region" ? "By region" : "By platform"}
                      </CardTitle>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        Latest review — {formatCurrency(parseFloat(alloc.total_usd), USD)} total
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={alloc.slices.map((s) => ({
                                name: s.key,
                                value: parseFloat(s.value_usd),
                              }))}
                              dataKey="value"
                              nameKey="name"
                              cx="50%"
                              cy="50%"
                              innerRadius={50}
                              outerRadius={80}
                              paddingAngle={2}
                            >
                              {alloc.slices.map((slice, i) => (
                                <Cell
                                  key={slice.key}
                                  fill={pieColors[i % pieColors.length]}
                                />
                              ))}
                            </Pie>
                            <Tooltip
                              contentStyle={getTooltipStyle(checkDarkMode())}
                              formatter={(v: number, name: string) => [
                                formatCurrency(v, USD),
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
              )
          )}
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

function NetWorthTile({
  label,
  value,
  emphasis = false,
  negative = false,
}: {
  label: string;
  value: number;
  emphasis?: boolean;
  negative?: boolean;
}) {
  const displayValue = negative ? -Math.abs(value) : value;
  return (
    <Card className={emphasis ? "" : ""} variant={emphasis ? "highlight" : "default"}>
      <CardContent className="py-5">
        <div className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </div>
        <div
          className={`mt-1 font-semibold ${
            emphasis ? "text-3xl" : "text-2xl"
          } ${
            negative
              ? "text-danger-600 dark:text-danger-400"
              : "text-slate-900 dark:text-white"
          }`}
        >
          {formatCurrency(displayValue, "CAD")}
        </div>
      </CardContent>
    </Card>
  );
}
