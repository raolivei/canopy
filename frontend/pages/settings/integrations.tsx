import React, { useState, useEffect } from "react";
import Link from "next/link";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import {
  Plug,
  ExternalLink,
  Check,
  X,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  Key,
  Globe,
  Loader2,
  Server,
  Download,
  ArrowLeft,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/utils/cn";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const INTEGRATIONS_BASE = API_BASE ? `${API_BASE}/v1/integrations` : "/v1/integrations";
const WISE_TOKEN_KEY = "canopy_wise_token";
const WISE_SANDBOX_KEY = "canopy_wise_sandbox";
const QUESTRADE_TOKEN_KEY = "canopy_questrade_token";

interface Integration {
  id: string;
  name: string;
  logo: string;
  description: string;
  status: "connected" | "disconnected" | "pending";
  lastSync?: string;
  accountsLinked?: number;
  setupSteps: string[];
  docsUrl: string;
}

const integrations: Integration[] = [
  {
    id: "questrade",
    name: "Questrade",
    logo: "🇨🇦",
    description: "Canadian discount brokerage. Connect your TFSA, RRSP, and trading accounts.",
    status: "disconnected",
    setupSteps: [
      "Go to my.questrade.com/APIAccess",
      "Register a new application",
      "Copy your Client ID and generate a refresh token",
      "Enter the credentials below",
    ],
    docsUrl: "https://www.questrade.com/api/documentation",
  },
  {
    id: "wise",
    name: "Wise",
    logo: "💱",
    description: "Track your CAD balance automatically (FX conversions are folded into CAD).",
    status: "disconnected",
    setupSteps: [
      "Log in to Wise and go to Settings",
      "Navigate to API tokens",
      "Generate a new Personal Token",
      "Enter the token below",
    ],
    docsUrl: "https://wise.com/developers/api",
  },
  {
    id: "wealthsimple",
    name: "Wealthsimple",
    logo: "🍁",
    description: "Canadian robo-advisor. RRSP, TFSA, FHSA, and Cash accounts.",
    status: "disconnected",
    setupSteps: [
      "Wealthsimple does not have a public API",
      "Use CSV export from the app",
      "Import via the Import page",
    ],
    docsUrl: "",
  },
];

function WiseCard({ integration }: { integration: Integration }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [apiToken, setApiToken] = useState("");
  const [sandbox, setSandbox] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [accountsLinked, setAccountsLinked] = useState<number>(0);
  const [syncResult, setSyncResult] = useState<{ assets_created: number; assets_updated: number; transactions_imported: number; currencies: string[] } | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem(WISE_TOKEN_KEY);
    const useSandbox = localStorage.getItem(WISE_SANDBOX_KEY) === "true";
    setSandbox(useSandbox);
    if (token) {
      setConnected(true);
      setApiToken(token);
      fetch(`${INTEGRATIONS_BASE}/wise/balances`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_token: token, sandbox: useSandbox }),
      })
        .then((r) => r.ok ? r.json() : [])
        .then((balances) => {
          if (Array.isArray(balances)) setAccountsLinked(balances.length);
        })
        .catch(() => {});
    }
    fetch(`${INTEGRATIONS_BASE}/wise/status`)
      .then((r) => r.json())
      .then((data) => {
        if (data.connected && !token) setConnected(true);
      })
      .catch(() => {});
  }, []);

  const handleConnect = async () => {
    if (!apiToken.trim()) return;
    setIsConnecting(true);
    setError(null);
    try {
      const res = await fetch(`${INTEGRATIONS_BASE}/wise/test-connection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_token: apiToken.trim(), sandbox }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Connection failed");
      }
      localStorage.setItem(WISE_TOKEN_KEY, apiToken.trim());
      localStorage.setItem(WISE_SANDBOX_KEY, String(sandbox));
      setConnected(true);
      setAccountsLinked(1);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Connection failed");
      setConnected(false);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = () => {
    localStorage.removeItem(WISE_TOKEN_KEY);
    localStorage.removeItem(WISE_SANDBOX_KEY);
    setConnected(false);
    setLastSync(null);
    setAccountsLinked(0);
    setSyncResult(null);
    setApiToken("");
  };

  const handleSync = async () => {
    const token = localStorage.getItem(WISE_TOKEN_KEY) || apiToken;
    if (!token) {
      setError("No token. Connect first.");
      return;
    }
    setIsSyncing(true);
    setError(null);
    setSyncResult(null);
    try {
      const res = await fetch(`${INTEGRATIONS_BASE}/wise/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_token: token, sandbox, days: 90 }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Sync failed");
      }
      const data = await res.json();
      setSyncResult(data);
      setLastSync(new Date().toLocaleString());
      setAccountsLinked(data.currencies?.length ?? 0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setIsSyncing(false);
    }
  };

  const status = connected ? "connected" : isConnecting ? "pending" : "disconnected";

  return (
    <Card>
      <div
        className="p-6 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-3xl">{integration.logo}</span>
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{integration.name}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">{integration.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={status} />
            <ChevronRight className={cn("w-5 h-5 text-slate-400 transition-transform", isExpanded && "rotate-90")} />
          </div>
        </div>
        {connected && (
          <div className="mt-3 flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
            <span>{accountsLinked} currency balance(s)</span>
            {lastSync && <span>Last sync: {lastSync}</span>}
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleSync(); }}
              disabled={isSyncing}
              className="flex items-center gap-1 text-primary-600 hover:text-primary-700 dark:text-primary-400 disabled:opacity-50"
            >
              <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
              Sync Now
            </button>
          </div>
        )}
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 border-t border-slate-100 dark:border-slate-800">
              <div className="pt-4 space-y-4">
                <SetupInstructions steps={integration.setupSteps} docsUrl={integration.docsUrl} />

                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={sandbox}
                    onChange={(e) => setSandbox(e.target.checked)}
                    disabled={connected}
                    className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                  />
                  Use sandbox (testing)
                </label>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    API Token
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="password"
                      value={apiToken}
                      onChange={(e) => setApiToken(e.target.value)}
                      placeholder="Wise API token (Settings → API tokens)"
                      className="flex-1"
                    />
                    {connected ? (
                      <Button variant="danger" onClick={handleDisconnect}>
                        Disconnect
                      </Button>
                    ) : (
                      <Button
                        variant="primary"
                        onClick={handleConnect}
                        loading={isConnecting}
                        disabled={!apiToken.trim() || isConnecting}
                      >
                        Connect
                      </Button>
                    )}
                  </div>
                </div>

                {error && (
                  <div className="p-2 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded text-sm text-danger-700 dark:text-danger-400">
                    {error}
                  </div>
                )}

                {syncResult && (
                  <div className="p-3 bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 rounded-lg text-sm text-success-800 dark:text-success-300">
                    Synced: {syncResult.assets_created} assets created, {syncResult.assets_updated} updated, {syncResult.transactions_imported} transactions imported ({syncResult.currencies?.join(", ") || ""}).
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function QuestradeCard({ integration }: { integration: Integration }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [refreshToken, setRefreshToken] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [accounts, setAccounts] = useState<{ number: string; type: string; status: string }[]>([]);
  const [syncResult, setSyncResult] = useState<{ accounts_synced: number; assets_created: number; assets_updated: number; positions_synced: number } | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem(QUESTRADE_TOKEN_KEY);
    if (token) {
      setConnected(true);
      setRefreshToken(token);
    }
  }, []);

  const handleConnect = async () => {
    if (!refreshToken.trim()) return;
    setIsConnecting(true);
    setError(null);
    try {
      const res = await fetch(`${INTEGRATIONS_BASE}/questrade/test-connection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken.trim() }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Connection failed");
      }
      const data = await res.json();
      if (data.new_refresh_token) {
        localStorage.setItem(QUESTRADE_TOKEN_KEY, data.new_refresh_token);
        setRefreshToken(data.new_refresh_token);
      } else {
        localStorage.setItem(QUESTRADE_TOKEN_KEY, refreshToken.trim());
      }
      setConnected(true);
      setAccounts(data.accounts || []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Connection failed");
      setConnected(false);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = () => {
    localStorage.removeItem(QUESTRADE_TOKEN_KEY);
    setConnected(false);
    setAccounts([]);
    setSyncResult(null);
    setRefreshToken("");
  };

  const handleSync = async () => {
    const token = localStorage.getItem(QUESTRADE_TOKEN_KEY) || refreshToken;
    if (!token) { setError("No token. Connect first."); return; }
    setIsSyncing(true);
    setError(null);
    setSyncResult(null);
    try {
      const res = await fetch(`${INTEGRATIONS_BASE}/questrade/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: token }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Sync failed");
      }
      const data = await res.json();
      setSyncResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <Card>
      <div
        className="p-6 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-3xl">{integration.logo}</span>
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{integration.name}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">{integration.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={connected ? "connected" : "disconnected"} />
            <ChevronRight className={cn("w-5 h-5 text-slate-400 transition-transform", isExpanded && "rotate-90")} />
          </div>
        </div>
        {connected && accounts.length > 0 && (
          <div className="mt-3 flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
            <span>{accounts.length} account(s)</span>
            <span>{accounts.map((a) => a.type).join(", ")}</span>
          </div>
        )}
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 border-t border-slate-100 dark:border-slate-800">
              <div className="pt-4 space-y-4">
                <SetupInstructions steps={integration.setupSteps} docsUrl={integration.docsUrl} />

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Refresh Token
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="password"
                      value={refreshToken}
                      onChange={(e) => setRefreshToken(e.target.value)}
                      placeholder="Paste your Questrade refresh token..."
                      className="flex-1"
                    />
                    {connected ? (
                      <Button variant="danger" onClick={(e) => { e.stopPropagation(); handleDisconnect(); }}>
                        Disconnect
                      </Button>
                    ) : (
                      <Button
                        variant="primary"
                        onClick={(e) => { e.stopPropagation(); handleConnect(); }}
                        disabled={!refreshToken.trim() || isConnecting}
                      >
                        {isConnecting ? "Connecting..." : "Connect"}
                      </Button>
                    )}
                  </div>
                </div>

                {connected && (
                  <div className="flex items-center gap-3">
                    <Button
                      variant="secondary"
                      leftIcon={<RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />}
                      onClick={(e) => { e.stopPropagation(); handleSync(); }}
                      disabled={isSyncing}
                    >
                      {isSyncing ? "Syncing..." : "Sync Now"}
                    </Button>
                  </div>
                )}

                {syncResult && (
                  <div className="p-3 bg-success-50 dark:bg-success-900/20 rounded-lg text-sm text-success-700 dark:text-success-300">
                    Synced {syncResult.accounts_synced} account(s): {syncResult.assets_created} assets created, {syncResult.assets_updated} updated, {syncResult.positions_synced} positions synced
                  </div>
                )}

                {error && (
                  <div className="p-3 bg-danger-50 dark:bg-danger-900/20 rounded-lg text-sm text-danger-700 dark:text-danger-300">
                    {error}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function IntegrationCard({
  integration,
  onConnect,
}: {
  integration: Integration;
  onConnect: (id: string, token?: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [apiToken, setApiToken] = useState("");

  return (
    <Card>
      <div
        className="p-6 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-3xl">{integration.logo}</span>
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                {integration.name}
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {integration.description}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={integration.status} />
            <ChevronRight className={cn("w-5 h-5 text-slate-400 transition-transform", isExpanded && "rotate-90")} />
          </div>
        </div>

        {integration.status === "connected" && (
          <div className="mt-3 flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
            <span>{integration.accountsLinked} accounts linked</span>
            <span>Last sync: {integration.lastSync}</span>
            <button className="flex items-center gap-1 text-primary-600 hover:text-primary-700 dark:text-primary-400">
              <RefreshCw className="w-4 h-4" />
              Sync Now
            </button>
          </div>
        )}
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 border-t border-slate-100 dark:border-slate-800">
              <div className="pt-4 space-y-4">
                <SetupInstructions steps={integration.setupSteps} docsUrl={integration.docsUrl} />

                {integration.id !== "wealthsimple" && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      API Token
                    </label>
                    <div className="flex gap-2">
                      <Input
                        type="password"
                        value={apiToken}
                        onChange={(e) => setApiToken(e.target.value)}
                        placeholder="Enter your API token..."
                        className="flex-1"
                      />
                      <Button
                        variant="primary"
                        onClick={() => onConnect(integration.id, apiToken)}
                        disabled={!apiToken}
                      >
                        Connect
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function StatusBadge({ status }: { status: "connected" | "disconnected" | "pending" }) {
  const variants = {
    connected: "success" as const,
    disconnected: "secondary" as const,
    pending: "warning" as const,
  };
  const icons = {
    connected: <Check className="w-3.5 h-3.5" />,
    disconnected: <X className="w-3.5 h-3.5" />,
    pending: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
  };
  const labels = {
    connected: "Connected",
    disconnected: "Not Connected",
    pending: "Connecting...",
  };

  return (
    <Badge variant={variants[status]} className="flex items-center gap-1">
      {icons[status]}
      {labels[status]}
    </Badge>
  );
}

function SetupInstructions({ steps, docsUrl, docsLabel = "View Documentation" }: { steps: string[]; docsUrl: string; docsLabel?: string }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
        <Download className="w-4 h-4" />
        Setup Instructions
      </h4>
      <ol className="space-y-2">
        {steps.map((step, index) => (
          <li key={index} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
            <span className="flex-shrink-0 w-5 h-5 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full flex items-center justify-center text-xs font-medium">
              {index + 1}
            </span>
            {step}
          </li>
        ))}
      </ol>
      {docsUrl && (
        <a
          href={docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 mt-3 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
        >
          {docsLabel}
          <ExternalLink className="w-4 h-4" />
        </a>
      )}
    </div>
  );
}

export default function Integrations() {
  const handleConnect = (integrationId: string, token?: string) => {
    console.log(`Connecting to ${integrationId} with token:`, token);
    alert(
      `Connection to ${integrationId} is not yet implemented.\n\nPlease ensure you have the required credentials ready, then check back later.`
    );
  };

  return (
    <PageLayout title="Integrations" description="Connect your financial accounts">
      <PageHeader
        title="Integrations"
        description="Connect your financial accounts for automatic syncing"
        actions={
          <Link href="/settings">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back to Settings
            </Button>
          </Link>
        }
      />

      {/* Info Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <Card className="bg-success-50 dark:bg-success-900/20 border-success-200 dark:border-success-800">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Check className="w-5 h-5 text-success-600 dark:text-success-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-success-900 dark:text-success-300">
                  Wise integration available
                </h3>
                <p className="text-sm text-success-700 dark:text-success-400 mt-1">
                  <strong>Wise:</strong> Connect with an API token (wise.com → Settings → API tokens), then Sync to pull balances and transactions into Canopy.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Integration Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="space-y-4 mb-8"
      >
        {integrations.map((integration) =>
          integration.id === "wise" ? (
            <WiseCard key={integration.id} integration={integration} />
          ) : integration.id === "questrade" ? (
            <QuestradeCard key={integration.id} integration={integration} />
          ) : (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              onConnect={handleConnect}
            />
          )
        )}
      </motion.div>

      {/* CSV Import Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6"
      >
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-success-500" />
              <CardTitle>CSV Import (Available Now)</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600 dark:text-slate-400 mb-4">
              For institutions without API access, you can import data via CSV export. Supported formats:
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              {["Questrade", "Wealthsimple", "Schwab", "Nubank", "Clear", "XP", "RBC", "Generic CSV"].map((format) => (
                <div
                  key={format}
                  className="px-3 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-sm text-slate-700 dark:text-slate-300 text-center"
                >
                  {format}
                </div>
              ))}
            </div>
            <Link href="/import">
              <Button variant="primary" rightIcon={<ChevronRight className="w-4 h-4" />}>
                Go to Import Page
              </Button>
            </Link>
          </CardContent>
        </Card>
      </motion.div>

      {/* Security Note */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-slate-100 dark:bg-slate-800/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Key className="w-5 h-5 text-slate-500 dark:text-slate-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-slate-600 dark:text-slate-400">
                <strong className="text-slate-700 dark:text-slate-300">Security Note:</strong>{" "}
                All API credentials are stored locally on your machine and never sent to external servers. Canopy runs entirely on your own infrastructure.
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </PageLayout>
  );
}
