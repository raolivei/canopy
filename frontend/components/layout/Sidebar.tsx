import { useState, useEffect } from "react";
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
  ChevronLeft,
  ChevronDown,
  Moon,
  BarChart2,
  Sun,
  Command,
  UploadCloud,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/utils/cn";

const primaryNavigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Wealthsimple import", href: "/portfolio/wealthsimple-import", icon: UploadCloud },
  { name: "Monarch import", href: "/portfolio/monarch-import", icon: UploadCloud },
  { name: "Holdings", href: "/portfolio", icon: TrendingUp },
  { name: "Accounts", href: "/accounts", icon: Wallet },
  { name: "Insights", href: "/insights", icon: Target },
  { name: "Annual Report", href: "/report", icon: BarChart2 },
  { name: "Settings", href: "/settings", icon: Settings },
];

// Active-but-power-user features. Kept reachable, just out of the
// primary vertical.
const advancedNavigation = [
  { name: "Transactions", href: "/transactions", icon: DollarSign },
  { name: "Bank CSV import", href: "/import", icon: Upload },
  { name: "Integrations", href: "/settings/integrations", icon: Plug },
];

// Old flows we still ship for back-compat (portfolio-review snapshots
// are the one case we explicitly carry over from 0.7.x). Separated
// from "Advanced" so it's clear these are not where new work happens.
const legacyNavigation = [
  { name: "Import snapshot", href: "/portfolio/import", icon: Upload },
];

interface NavItem {
  name: string;
  href: string;
  icon: typeof Home;
}

interface RenderSectionArgs {
  title: string;
  items: NavItem[];
  open: boolean;
  setOpen: (next: boolean) => void;
  isCollapsed: boolean;
  router: ReturnType<typeof useRouter>;
}

// Shared rendering for the collapsible Advanced / Legacy sections.
// Keeps both groups visually identical while letting each own its own
// expand/collapse state.
function renderSection({
  title,
  items,
  open,
  setOpen,
  isCollapsed,
  router,
}: RenderSectionArgs) {
  return (
    <>
      {!isCollapsed && (
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="w-full flex items-center gap-2 px-3 py-2 mt-2 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-400"
        >
          <ChevronDown
            className={cn("w-4 h-4 transition-transform", open ? "rotate-180" : "")}
          />
          {title}
        </button>
      )}

      {(open || isCollapsed) &&
        items.map((item) => {
          const isActive =
            router.pathname === item.href ||
            (item.href !== "/" && router.pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  : "text-slate-500 dark:text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800/80 hover:text-slate-800 dark:hover:text-slate-200"
              )}
              title={isCollapsed ? item.name : undefined}
            >
              <Icon className="w-5 h-5 shrink-0 text-slate-400 dark:text-slate-500" />
              <AnimatePresence mode="wait">
                {!isCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: "auto" }}
                    exit={{ opacity: 0, width: 0 }}
                    transition={{ duration: 0.15 }}
                    className="truncate"
                  >
                    {item.name}
                  </motion.span>
                )}
              </AnimatePresence>
            </Link>
          );
        })}
    </>
  );
}

interface SidebarProps {
  onCommandPaletteOpen?: () => void;
}

export default function Sidebar({ onCommandPaletteOpen }: SidebarProps) {
  const router = useRouter();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [legacyOpen, setLegacyOpen] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    const savedCollapsed = localStorage.getItem("sidebar-collapsed");
    if (savedCollapsed) {
      setIsCollapsed(savedCollapsed === "true");
    }
    
    const isDark = document.documentElement.classList.contains("dark");
    setIsDarkMode(isDark);
  }, []);

  const toggleCollapsed = () => {
    const newValue = !isCollapsed;
    setIsCollapsed(newValue);
    localStorage.setItem("sidebar-collapsed", String(newValue));
  };

  const toggleDarkMode = () => {
    const newValue = !isDarkMode;
    setIsDarkMode(newValue);
    if (newValue) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("darkMode", "true");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("darkMode", "false");
    }
  };

  if (!isMounted) {
    return null;
  }

  return (
    <>
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 64 : 240 }}
        transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
        className={cn(
          "fixed left-0 top-0 h-full z-40",
          "bg-white dark:bg-slate-900",
          "border-r border-slate-200 dark:border-slate-800",
          "flex flex-col"
        )}
      >
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100 dark:border-slate-800">
          <AnimatePresence mode="wait">
            {!isCollapsed ? (
              <motion.div
                key="full-logo"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                <Link
                  href="/"
                  aria-label="Canopy home"
                  className="flex items-center gap-2 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                >
                  <img
                    src="/brand/canopy-icon.svg"
                    alt="Canopy"
                    className="w-8 h-8 rounded-lg"
                  />
                  <span className="font-semibold text-slate-900 dark:text-white">
                    Canopy
                  </span>
                </Link>
              </motion.div>
            ) : (
              <motion.div
                key="icon-logo"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="mx-auto"
              >
                <Link
                  href="/"
                  aria-label="Canopy home"
                  className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                >
                  <img
                    src="/brand/canopy-icon.svg"
                    alt="Canopy"
                    className="w-8 h-8 rounded-lg"
                  />
                </Link>
              </motion.div>
            )}
          </AnimatePresence>
          
          {!isCollapsed && (
            <button
              onClick={toggleCollapsed}
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors"
              title="Collapse sidebar"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Command Palette Trigger */}
        {onCommandPaletteOpen && (
          <div className="px-3 py-2">
            <button
              onClick={onCommandPaletteOpen}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 rounded-md",
                "text-sm text-slate-500 dark:text-slate-400",
                "bg-slate-100 dark:bg-slate-800",
                "hover:bg-slate-200 dark:hover:bg-slate-700",
                "transition-colors"
              )}
            >
              <Command className="w-4 h-4" />
              {!isCollapsed && (
                <>
                  <span className="flex-1 text-left">Search...</span>
                  <kbd className="text-xs bg-white dark:bg-slate-900 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                    ⌘K
                  </kbd>
                </>
              )}
            </button>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {primaryNavigation.map((item) => {
            const isActive =
              router.pathname === item.href ||
              (item.href !== "/" && router.pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary-50 dark:bg-primary-950/50 text-primary-700 dark:text-primary-300"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100"
                )}
                title={isCollapsed ? item.name : undefined}
              >
                <Icon
                  className={cn(
                    "w-5 h-5 shrink-0",
                    isActive
                      ? "text-primary-600 dark:text-primary-400"
                      : "text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-400"
                  )}
                />
                <AnimatePresence mode="wait">
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.15 }}
                      className="truncate"
                    >
                      {item.name}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            );
          })}

          {renderSection({
            title: "Advanced",
            items: advancedNavigation,
            open: advancedOpen,
            setOpen: setAdvancedOpen,
            isCollapsed,
            router,
          })}

          {renderSection({
            title: "Legacy",
            items: legacyNavigation,
            open: legacyOpen,
            setOpen: setLegacyOpen,
            isCollapsed,
            router,
          })}
        </nav>

        {/* Footer */}
        <div className="px-3 py-4 border-t border-slate-100 dark:border-slate-800 space-y-2">
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium",
              "text-slate-600 dark:text-slate-400",
              "hover:bg-slate-100 dark:hover:bg-slate-800",
              "transition-colors"
            )}
            title={isCollapsed ? (isDarkMode ? "Light mode" : "Dark mode") : undefined}
          >
            {isDarkMode ? (
              <Sun className="w-5 h-5 text-slate-400 dark:text-slate-500" />
            ) : (
              <Moon className="w-5 h-5 text-slate-400" />
            )}
            {!isCollapsed && (
              <span>{isDarkMode ? "Light mode" : "Dark mode"}</span>
            )}
          </button>

          {/* Expand Button (when collapsed) */}
          {isCollapsed && (
            <button
              onClick={toggleCollapsed}
              className={cn(
                "w-full flex items-center justify-center px-3 py-2 rounded-md",
                "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300",
                "hover:bg-slate-100 dark:hover:bg-slate-800",
                "transition-colors"
              )}
              title="Expand sidebar"
            >
              <ChevronLeft className="w-5 h-5 rotate-180" />
            </button>
          )}
        </div>
      </motion.aside>
    </>
  );
}
