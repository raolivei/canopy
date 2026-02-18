import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  Home,
  DollarSign,
  TrendingUp,
  Settings,
  Wallet,
  Upload,
  Target,
  Plug,
} from "lucide-react";
import { motion } from "framer-motion";
import DarkModeToggle from "./DarkModeToggle";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Transactions", href: "/transactions", icon: DollarSign },
  { name: "Import", href: "/import", icon: Upload },
  { name: "Portfolio", href: "/portfolio", icon: TrendingUp },
  { name: "Insights", href: "/insights", icon: Target },
  { name: "Accounts", href: "/accounts", icon: Wallet },
  { name: "Integrations", href: "/settings/integrations", icon: Plug },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const router = useRouter();

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="fixed left-0 top-0 h-full w-64 bg-gradient-dark text-white flex flex-col border-r border-slate-800/50"
    >
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <div className="relative h-10 w-40">
              <Image
                src="/brand/canopy-logo-light.svg"
                alt="Canopy logo"
                fill
                sizes="160px"
                priority
                className="object-contain object-left dark:hidden"
              />
              <Image
                src="/brand/canopy-logo-dark.svg"
                alt="Canopy logo"
                fill
                sizes="160px"
                priority
                className="hidden object-contain object-left dark:block"
              />
            </div>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-2 tracking-wide italic">
              Grow. Protect. Flourish.
            </p>
          </div>
          <DarkModeToggle />
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {navigation.map((item, index) => {
          const isActive = router.pathname === item.href;
          const Icon = item.icon;
          return (
            <motion.div
              key={item.name}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: index * 0.05, duration: 0.2 }}
            >
              <Link
                href={item.href}
                className={`
                  relative flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-300 ease-out
                  ${
                    isActive
                      ? "bg-primary-600 text-white shadow-glow"
                      : "text-slate-300 dark:text-slate-400 hover:bg-slate-800/50 hover:text-white"
                  }
                `}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute inset-0 bg-gradient-primary rounded-md"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
                <Icon
                  size={20}
                  className={`relative z-10 ${isActive ? "text-white" : ""}`}
                />
                <span
                  className={`relative z-10 font-medium ${isActive ? "text-white" : ""}`}
                >
                  {item.name}
                </span>
              </Link>
            </motion.div>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-800/50">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-800/30 dark:bg-slate-900/50 rounded-lg p-4 border border-slate-700/50"
        >
          <p className="text-xs text-slate-400 dark:text-slate-500 font-medium">
            Privacy First
          </p>
          <p className="text-sm text-slate-300 dark:text-slate-400 mt-1">
            All data stored locally
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}
