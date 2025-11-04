import Link from "next/link";
import { useRouter } from "next/router";
import { Home, DollarSign, TrendingUp, Settings, Wallet } from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Transactions", href: "/transactions", icon: DollarSign },
  { name: "Portfolio", href: "/portfolio", icon: TrendingUp },
  { name: "Accounts", href: "/accounts", icon: Wallet },
  { name: "Settings", href: "/settings", icon: Settings },
];

import DarkModeToggle from "./DarkModeToggle";

export default function Sidebar() {
  const router = useRouter();

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-gray-900 to-gray-800 dark:from-gray-950 dark:to-gray-900 text-white flex flex-col">
      <div className="p-6 border-b border-gray-700 dark:border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-primary-300 bg-clip-text text-transparent">
              LedgerLight
            </h1>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              Personal Finance
            </p>
          </div>
          <DarkModeToggle />
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = router.pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`
                flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
                ${
                  isActive
                    ? "bg-primary-600 text-white shadow-lg shadow-primary-600/20"
                    : "text-gray-300 dark:text-gray-400 hover:bg-gray-700/50 dark:hover:bg-gray-800/50 hover:text-white"
                }
              `}
            >
              <Icon size={20} />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-700 dark:border-gray-800">
        <div className="bg-gray-800/50 dark:bg-gray-900/50 rounded-xl p-4">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Privacy First
          </p>
          <p className="text-sm text-gray-300 dark:text-gray-400 mt-1">
            All data stored locally
          </p>
        </div>
      </div>
    </div>
  );
}
