import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  Home,
  TrendingUp,
  Wallet,
  Menu,
  UploadCloud,
  DollarSign,
} from "lucide-react";
import { cn } from "@/utils/cn";

// The primary mobile slot points at the Wealthsimple importer now that
// portfolio-snapshot CSVs live under Legacy. Reachable from the
// command palette / sidebar when needed.
const mobileNavItems = [
  { name: "Home", href: "/", icon: Home },
  { name: "Import", href: "/portfolio/wealthsimple-import", icon: UploadCloud },
  { name: "Holdings", href: "/portfolio", icon: TrendingUp },
  { name: "Txns", href: "/transactions", icon: DollarSign },
  { name: "Accounts", href: "/accounts", icon: Wallet },
  { name: "More", href: "/settings", icon: Menu },
];

export default function MobileNav() {
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);

  // Render nothing on the server / first client paint. Browser
  // extensions (e.g. Dark Reader) inject attributes like
  // ``data-darkreader-inline-stroke`` onto lucide SVG icons before
  // hydration, producing "Extra attributes from the server" warnings.
  // Gating renders on ``isMounted`` mirrors what Sidebar already does.
  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 safe-area-pb">
      <div className="flex items-center justify-around h-16">
        {mobileNavItems.map((item) => {
          const path = router.pathname;
          const isActive =
            item.name === "Import"
              ? (
                  path === "/portfolio/wealthsimple-import" ||
                  path === "/portfolio/monarch-import" ||
                  path === "/portfolio/import" ||
                  path.startsWith("/portfolio/import/") ||
                  path === "/import" ||
                  path.startsWith("/import/")
                )
              : item.href === "/transactions"
                ? path === "/transactions"
              : item.href === "/settings"
                ? path === "/settings" || path.startsWith("/settings/")
                : path === item.href ||
                  (item.href !== "/" && path.startsWith(`${item.href}/`));
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center w-full h-full gap-1",
                "text-xs font-medium transition-colors",
                isActive
                  ? "text-primary-600 dark:text-primary-400"
                  : "text-slate-500 dark:text-slate-400"
              )}
            >
              <Icon
                className={cn(
                  "w-5 h-5",
                  isActive
                    ? "text-primary-600 dark:text-primary-400"
                    : "text-slate-400 dark:text-slate-500"
                )}
              />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
