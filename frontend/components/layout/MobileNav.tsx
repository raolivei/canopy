import Link from "next/link";
import { useRouter } from "next/router";
import {
  Home,
  TrendingUp,
  DollarSign,
  Wallet,
  Menu,
} from "lucide-react";
import { cn } from "@/utils/cn";

const mobileNavItems = [
  { name: "Home", href: "/", icon: Home },
  { name: "Portfolio", href: "/portfolio", icon: TrendingUp },
  { name: "Transactions", href: "/transactions", icon: DollarSign },
  { name: "Accounts", href: "/accounts", icon: Wallet },
  { name: "More", href: "/settings", icon: Menu },
];

export default function MobileNav() {
  const router = useRouter();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 safe-area-pb">
      <div className="flex items-center justify-around h-16">
        {mobileNavItems.map((item) => {
          const isActive =
            router.pathname === item.href ||
            (item.href !== "/" && item.href !== "/settings" && router.pathname.startsWith(item.href));
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
