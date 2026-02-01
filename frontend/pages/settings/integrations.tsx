import React, { useState } from "react";
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
} from "lucide-react";

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
    id: "moomoo",
    name: "Moomoo",
    logo: "🐄",
    description: "Commission-free trading. Requires OpenD gateway running locally.",
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
    description: "Multi-currency account. Track your CAD, USD, BRL balances automatically.",
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

function IntegrationCard({
  integration,
  onConnect,
}: {
  integration: Integration;
  onConnect: (id: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [apiToken, setApiToken] = useState("");

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

            {integration.id !== "wealthsimple" && (
              <div className="mt-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {integration.id === "moomoo" ? "OpenD Host" : "API Token"}
                  </label>
                  <div className="flex gap-2">
                    <input
                      type={integration.id === "moomoo" ? "text" : "password"}
                      value={apiToken}
                      onChange={(e) => setApiToken(e.target.value)}
                      placeholder={
                        integration.id === "moomoo"
                          ? "localhost:11111"
                          : "Enter your API token..."
                      }
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <button
                      onClick={() => onConnect(integration.id)}
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
  const handleConnect = (integrationId: string) => {
    // TODO: Implement actual connection logic when APIs are ready
    console.log(`Connecting to ${integrationId}...`);
    alert(
      `Connection to ${integrationId} is not yet implemented.\n\nPlease ensure you have the required credentials ready, then check back later.`
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
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-900 dark:text-blue-300">
              API Integrations Coming Soon
            </h3>
            <p className="text-sm text-blue-700 dark:text-blue-400 mt-1">
              Direct API connections to your financial institutions are being developed.
              In the meantime, you can use CSV imports to add your data.
              Set up your API credentials now so you're ready when the features launch.
            </p>
          </div>
        </div>

        {/* Integration Cards */}
        <div className="space-y-4">
          {integrations.map((integration) => (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              onConnect={handleConnect}
            />
          ))}
        </div>

        {/* CSV Import Section */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-green-500" />
            CSV Import (Available Now)
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            For institutions without API access, you can import data via CSV export.
            Supported formats:
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
              <strong className="text-gray-700 dark:text-gray-300">Security Note:</strong>{" "}
              All API credentials are stored locally on your machine and never sent to external servers.
              Canopy runs entirely on your own infrastructure.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
