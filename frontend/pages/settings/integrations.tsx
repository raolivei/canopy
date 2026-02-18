import React, { useState, useEffect } from "react";
import Head from "next/head";
import Sidebar from "../../components/Sidebar";
import DarkModeToggle from "../../components/DarkModeToggle";
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
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const INTEGRATIONS_BASE = API_BASE ? `${API_BASE}/v1/integrations` : "/v1/integrations";
const WISE_TOKEN_KEY = "canopy_wise_token";
const WISE_SANDBOX_KEY = "canopy_wise_sandbox";

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
    description:
      "Canadian discount brokerage. Connect your TFSA, RRSP, and trading accounts.",
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
    id: "moomoo",
    name: "Moomoo",
    logo: "🐄",
    description:
      "Commission-free trading. Requires OpenD gateway running locally.",
    status: "disconnected",
    setupSteps: [
      "Download OpenD from Futu's developer portal",
      "Install and run OpenD on your computer",
      "Configure RSA key authentication",
      "Connect Canopy to your local OpenD instance",
    ],
    docsUrl: "https://openapi.futunn.com/",
  },
  {
    id: "wise",
    name: "Wise",
    logo: "💱",
    description:
      "Multi-currency account. Track your CAD, USD, BRL balances automatically.",
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

interface MoomooAccount {
  acc_id: number;
  acc_type: string;
  card_num: string;
  currency: string;
  market: string;
  status: string;
}

interface MoomooPosition {
  code: string;
  name: string;
  quantity: number;
  cost_price: number | null;
  current_price: number | null;
  market_value: number | null;
  profit_loss: number | null;
  profit_loss_pct: number | null;
  currency: string;
  market: string;
}

function MoomooCard({ integration }: { integration: Integration }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [host, setHost] = useState("127.0.0.1");
  const [port, setPort] = useState("11111");
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected" | "pending">("disconnected");
  const [connectionDetails, setConnectionDetails] = useState<any>(null);
  const [accounts, setAccounts] = useState<MoomooAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<MoomooAccount | null>(null);
  const [positions, setPositions] = useState<MoomooPosition[]>([]);
  const [loadingPositions, setLoadingPositions] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testConnection = async () => {
    setIsConnecting(true);
    setError(null);
    setConnectionStatus("pending");
    
    try {
      const response = await fetch(`${INTEGRATIONS_BASE}/moomoo/test-connection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ host, port: parseInt(port) }),
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Connection failed");
      }
      
      const data = await response.json();
      setConnectionStatus("connected");
      setConnectionDetails(data.details);
      
      // Fetch accounts after successful connection
      const accResponse = await fetch(`${INTEGRATIONS_BASE}/moomoo/accounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ host, port: parseInt(port) }),
      });
      
      if (accResponse.ok) {
        const accData = await accResponse.json();
        setAccounts(accData);
      }
    } catch (err: any) {
      setConnectionStatus("disconnected");
      setError(err.message || "Failed to connect to OpenD gateway");
    } finally {
      setIsConnecting(false);
    }
  };

  const fetchPositions = async (account: MoomooAccount) => {
    setLoadingPositions(true);
    setSelectedAccount(account);
    
    try {
      const response = await fetch(`${INTEGRATIONS_BASE}/moomoo/positions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          host,
          port: parseInt(port),
          acc_id: account.acc_id,
          market: account.market || "US",
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setPositions(data);
      }
    } catch (err) {
      console.error("Failed to fetch positions:", err);
    } finally {
      setLoadingPositions(false);
    }
  };

  const statusColors = {
    connected: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    disconnected: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
    pending: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  };

  const statusIcons = {
    connected: <Check className="w-4 h-4" />,
    disconnected: <X className="w-4 h-4" />,
    pending: <Loader2 className="w-4 h-4 animate-spin" />,
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
      <div
        className="p-6 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-3xl">{integration.logo}</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {integration.name}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {integration.description}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColors[connectionStatus]}`}>
              {statusIcons[connectionStatus]}
              {connectionStatus === "connected" ? "Connected" : connectionStatus === "pending" ? "Connecting..." : "Not Connected"}
            </span>
            <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? "rotate-90" : ""}`} />
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="px-6 pb-6 border-t border-gray-100 dark:border-gray-700">
          <div className="pt-4">
            {/* Setup Instructions */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Download className="w-4 h-4" />
                Setup Instructions
              </h4>
              <ol className="space-y-2">
                {integration.setupSteps.map((step, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="flex-shrink-0 w-5 h-5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-medium">
                      {index + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
              <a
                href={integration.docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-3 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                Download OpenD
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>

            {/* Connection Form */}
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Server className="w-4 h-4" />
                OpenD Gateway Connection
              </h4>
              
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Host</label>
                  <input
                    type="text"
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    placeholder="127.0.0.1"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Port</label>
                  <input
                    type="text"
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    placeholder="11111"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
              </div>

              {error && (
                <div className="mb-3 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-400">
                  {error}
                </div>
              )}

              <button
                onClick={(e) => { e.stopPropagation(); testConnection(); }}
                disabled={isConnecting}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Plug className="w-4 h-4" />
                    Test Connection
                  </>
                )}
              </button>
            </div>

            {/* Connection Details */}
            {connectionStatus === "connected" && connectionDetails && (
              <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <h5 className="text-sm font-medium text-green-800 dark:text-green-300 mb-2">Connected to OpenD</h5>
                <div className="grid grid-cols-2 gap-2 text-xs text-green-700 dark:text-green-400">
                  <span>US Market: {connectionDetails.market_us}</span>
                  <span>HK Market: {connectionDetails.market_hk}</span>
                  <span>Server Version: {connectionDetails.server_ver}</span>
                </div>
              </div>
            )}

            {/* Accounts */}
            {accounts.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Trading Accounts</h4>
                <div className="space-y-2">
                  {accounts.map((account) => (
                    <div
                      key={account.acc_id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedAccount?.acc_id === account.acc_id
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                          : "border-gray-200 dark:border-gray-700 hover:border-blue-300"
                      }`}
                      onClick={(e) => { e.stopPropagation(); fetchPositions(account); }}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium text-gray-900 dark:text-white">{account.acc_type}</span>
                          <span className="ml-2 text-sm text-gray-500">#{account.card_num || account.acc_id}</span>
                        </div>
                        <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">{account.currency} • {account.market}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Positions */}
            {selectedAccount && (
              <div className="mt-4">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  Positions ({selectedAccount.acc_type})
                </h4>
                {loadingPositions ? (
                  <div className="flex items-center justify-center py-4 text-gray-500">
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    Loading positions...
                  </div>
                ) : positions.length === 0 ? (
                  <div className="text-center py-4 text-gray-500 dark:text-gray-400">No positions found</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 dark:bg-gray-900/50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Symbol</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Qty</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Price</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Value</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">P/L</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {positions.map((pos) => (
                          <tr key={pos.code}>
                            <td className="px-3 py-2">
                              <div className="font-medium text-gray-900 dark:text-white">{pos.code.split(".")[1] || pos.code}</div>
                              <div className="text-xs text-gray-500 truncate max-w-[150px]">{pos.name}</div>
                            </td>
                            <td className="px-3 py-2 text-right text-gray-900 dark:text-white">{pos.quantity}</td>
                            <td className="px-3 py-2 text-right text-gray-900 dark:text-white">
                              {pos.current_price?.toFixed(2) ?? "-"}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-900 dark:text-white">
                              {pos.market_value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "-"}
                            </td>
                            <td className={`px-3 py-2 text-right ${(pos.profit_loss ?? 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
                              {pos.profit_loss !== null ? (
                                <>
                                  {pos.profit_loss >= 0 ? "+" : ""}{pos.profit_loss.toFixed(2)}
                                  <span className="text-xs ml-1">({pos.profit_loss_pct?.toFixed(2)}%)</span>
                                </>
                              ) : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

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
      const data = await res.json();
      localStorage.setItem(WISE_TOKEN_KEY, apiToken.trim());
      localStorage.setItem(WISE_SANDBOX_KEY, String(sandbox));
      setConnected(true);
      setAccountsLinked(1);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Connection failed");
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
    } catch (e: any) {
      setError(e.message || "Sync failed");
    } finally {
      setIsSyncing(false);
    }
  };

  const statusColors = {
    connected: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    disconnected: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
    pending: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  };
  const statusIcons = {
    connected: <Check className="w-4 h-4" />,
    disconnected: <X className="w-4 h-4" />,
    pending: <Loader2 className="w-4 h-4 animate-spin" />,
  };
  const status = connected ? "connected" : isConnecting ? "pending" : "disconnected";

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
      <div
        className="p-6 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-3xl">{integration.logo}</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{integration.name}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{integration.description}</p>
            </div>
          </div>
          <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColors[status]}`}>
            {statusIcons[status]}
            {status === "connected" ? "Connected" : status === "pending" ? "Connecting..." : "Not Connected"}
          </span>
          <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? "rotate-90" : ""}`} />
        </div>
        {connected && (
          <div className="mt-3 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <span>{accountsLinked} currency balance(s)</span>
            {lastSync && <span>Last sync: {lastSync}</span>}
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleSync(); }}
              disabled={isSyncing}
              className="flex items-center gap-1 text-blue-600 hover:text-blue-700 dark:text-blue-400 disabled:opacity-50"
            >
              <RefreshCw className={isSyncing ? "w-4 h-4 animate-spin" : "w-4 h-4"} />
              Sync Now
            </button>
          </div>
        )}
      </div>
      {isExpanded && (
        <div className="px-6 pb-6 border-t border-gray-100 dark:border-gray-700">
          <div className="pt-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Setup Instructions</h4>
            <ol className="space-y-2">
              {integration.setupSteps.map((step, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <span className="flex-shrink-0 w-5 h-5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-medium">
                    {index + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
            {integration.docsUrl && (
              <a href={integration.docsUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-3 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400">
                View Documentation
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
            <div className="mt-4 space-y-3">
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input type="checkbox" checked={sandbox} onChange={(e) => setSandbox(e.target.checked)} disabled={connected} />
                Use sandbox (testing)
              </label>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">API Token</label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={apiToken}
                    onChange={(e) => setApiToken(e.target.value)}
                    placeholder="Wise API token (Settings → API tokens)"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400"
                  />
                  {connected ? (
                    <button
                      type="button"
                      onClick={handleDisconnect}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleConnect}
                      disabled={!apiToken.trim() || isConnecting}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                    >
                      {isConnecting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                      Connect
                    </button>
                  )}
                </div>
              </div>
              {error && (
                <div className="p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-400">
                  {error}
                </div>
              )}
              {syncResult && (
                <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-sm text-green-800 dark:text-green-300">
                  Synced: {syncResult.assets_created} assets created, {syncResult.assets_updated} updated, {syncResult.transactions_imported} transactions imported ({syncResult.currencies?.join(", ") || ""}).
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
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

  const statusColors = {
    connected:
      "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    disconnected:
      "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
    pending:
      "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  };

  const statusIcons = {
    connected: <Check className="w-4 h-4" />,
    disconnected: <X className="w-4 h-4" />,
    pending: <Loader2 className="w-4 h-4 animate-spin" />,
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
      <div
        className="p-6 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-3xl">{integration.logo}</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {integration.name}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {integration.description}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                statusColors[integration.status]
              }`}
            >
              {statusIcons[integration.status]}
              {integration.status === "connected"
                ? "Connected"
                : integration.status === "pending"
                  ? "Connecting..."
                  : "Not Connected"}
            </span>
            <ChevronRight
              className={`w-5 h-5 text-gray-400 transition-transform ${
                isExpanded ? "rotate-90" : ""
              }`}
            />
          </div>
        </div>

        {integration.status === "connected" && (
          <div className="mt-3 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <span>{integration.accountsLinked} accounts linked</span>
            <span>Last sync: {integration.lastSync}</span>
            <button className="flex items-center gap-1 text-blue-600 hover:text-blue-700 dark:text-blue-400">
              <RefreshCw className="w-4 h-4" />
              Sync Now
            </button>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="px-6 pb-6 border-t border-gray-100 dark:border-gray-700">
          <div className="pt-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Setup Instructions
            </h4>
            <ol className="space-y-2">
              {integration.setupSteps.map((step, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
                >
                  <span className="flex-shrink-0 w-5 h-5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-medium">
                    {index + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>

            {integration.docsUrl && (
              <a
                href={integration.docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-3 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                View Documentation
                <ExternalLink className="w-4 h-4" />
              </a>
            )}

            {integration.id !== "wealthsimple" && integration.id !== "moomoo" && (
              <div className="mt-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    API Token
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={apiToken}
                      onChange={(e) => setApiToken(e.target.value)}
                      placeholder="Enter your API token..."
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <button
                      onClick={() => onConnect(integration.id, apiToken)}
                      disabled={!apiToken}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
                    >
                      Connect
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Integrations() {
  const handleConnect = (integrationId: string, token?: string) => {
    console.log(`Connecting to ${integrationId} with token:`, token);
    alert(
      `Connection to ${integrationId} is not yet implemented.\n\nPlease ensure you have the required credentials ready, then check back later.`,
    );
  };

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
      <Head>
        <title>Integrations - Canopy</title>
      </Head>
      <Sidebar />

      <main className="flex-1 p-8 ml-64">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
              <Plug className="w-8 h-8 text-blue-500" />
              Integrations
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Connect your financial accounts for automatic syncing
            </p>
          </div>
          <DarkModeToggle />
        </div>

        {/* Info Banner */}
        <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-start gap-3">
          <Check className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-900 dark:text-green-300">
              Wise &amp; Moomoo integrations available
            </h3>
            <p className="text-sm text-green-700 dark:text-green-400 mt-1">
              <strong>Wise:</strong> Connect with an API token (wise.com → Settings → API tokens), then Sync to pull balances and transactions into Canopy.{" "}
              <strong className="ml-1">Moomoo:</strong> Connect via the local OpenD gateway to view positions and market data.
            </p>
          </div>
        </div>

        {/* Integration Cards */}
        <div className="space-y-4">
          {integrations.map((integration) =>
            integration.id === "wise" ? (
              <WiseCard key={integration.id} integration={integration} />
            ) : integration.id === "moomoo" ? (
              <MoomooCard key={integration.id} integration={integration} />
            ) : (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConnect={handleConnect}
              />
            )
          )}
        </div>

        {/* CSV Import Section */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-green-500" />
            CSV Import (Available Now)
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            For institutions without API access, you can import data via CSV
            export. Supported formats:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              "Questrade",
              "Wealthsimple",
              "Schwab",
              "Nubank",
              "Clear",
              "XP",
              "RBC",
              "Generic CSV",
            ].map((format) => (
              <div
                key={format}
                className="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 text-center"
              >
                {format}
              </div>
            ))}
          </div>
          <a
            href="/import"
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
          >
            Go to Import Page
            <ChevronRight className="w-4 h-4" />
          </a>
        </div>

        {/* Security Note */}
        <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <div className="flex items-start gap-3">
            <Key className="w-5 h-5 text-gray-500 dark:text-gray-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <strong className="text-gray-700 dark:text-gray-300">
                Security Note:
              </strong>{" "}
              All API credentials are stored locally on your machine and never
              sent to external servers. Canopy runs entirely on your own
              infrastructure.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
