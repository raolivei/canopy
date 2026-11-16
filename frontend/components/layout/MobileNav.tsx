import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { cn } from "@/utils/cn";
import { useWorkspace } from "@/hooks/useWorkspace";
import { mobileNavigationFor, mobileNavItemIsActive } from "./navigation";

export default function MobileNav() {
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);
  const { workspace } = useWorkspace();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;

  const items = mobileNavigationFor(workspace);

  return (
    <nav
      aria-label={`${workspace === "tax" ? "Tax" : "Wallet"} navigation`}
      className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 safe-area-pb"
    >
      <div className="flex items-center justify-around h-16">
        {items.map((item) => {
          const isActive = mobileNavItemIsActive(router.pathname, item);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
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
