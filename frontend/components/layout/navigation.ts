/**
 * Navigation definitions shared by the sidebar and the mobile bar.
 *
 * Wallet keeps every existing route; Tax starts with its overview page.
 * Adding a page means adding it here once.
 */

import {
  Activity,
  BarChart2,
  DollarSign,
  FileText,
  Home,
  Menu,
  PiggyBank,
  Plug,
  Settings,
  Target,
  TrendingUp,
  UploadCloud,
  Wallet,
} from "lucide-react";

import type { Workspace } from "@/hooks/useWorkspace";

export interface NavItem {
  name: string;
  href: string;
  icon: typeof Home;
}

export const walletNavigation: NavItem[] = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Holdings", href: "/portfolio", icon: TrendingUp },
  { name: "Accounts", href: "/accounts", icon: Wallet },
  { name: "Transactions", href: "/transactions", icon: DollarSign },
  { name: "Budgets", href: "/budgets", icon: PiggyBank },
  { name: "Cash Flow", href: "/cashflow", icon: Activity },
  { name: "Import", href: "/import", icon: UploadCloud },
  { name: "Insights", href: "/insights", icon: Target },
  { name: "Annual Report", href: "/report", icon: BarChart2 },
  { name: "Integrations", href: "/settings/integrations", icon: Plug },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const taxNavigation: NavItem[] = [
  { name: "Tax overview", href: "/tax", icon: FileText },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const mobileWalletNavigation: NavItem[] = [
  { name: "Home", href: "/", icon: Home },
  { name: "Import", href: "/import", icon: UploadCloud },
  { name: "Holdings", href: "/portfolio", icon: TrendingUp },
  { name: "Txns", href: "/transactions", icon: DollarSign },
  { name: "Accounts", href: "/accounts", icon: Wallet },
  { name: "More", href: "/settings", icon: Menu },
];

export const mobileTaxNavigation: NavItem[] = [
  { name: "Tax", href: "/tax", icon: FileText },
  { name: "More", href: "/settings", icon: Menu },
];

export function navigationFor(workspace: Workspace): NavItem[] {
  return workspace === "tax" ? taxNavigation : walletNavigation;
}

export function mobileNavigationFor(workspace: Workspace): NavItem[] {
  return workspace === "tax" ? mobileTaxNavigation : mobileWalletNavigation;
}

/** Sidebar active-state rule: exact match, or a child route of a non-root item. */
export function navItemIsActive(pathname: string, href: string): boolean {
  if (pathname === href) return true;
  if (href === "/") return false;
  if (href === "/settings") {
    return pathname === "/settings";
  }
  const prefix = href.endsWith("/") ? href : `${href}/`;
  return pathname.startsWith(prefix);
}

/** Mobile bar active-state rule (Import groups the import flows; More covers settings). */
export function mobileNavItemIsActive(pathname: string, item: NavItem): boolean {
  if (item.name === "Import") {
    return (
      pathname === "/import" ||
      pathname === "/portfolio/wealthsimple-import" ||
      pathname === "/portfolio/monarch-import" ||
      pathname === "/portfolio/import" ||
      pathname.startsWith("/portfolio/import/") ||
      pathname.startsWith("/import/")
    );
  }
  if (item.href === "/transactions") return pathname === "/transactions";
  if (item.href === "/settings") return pathname === "/settings" || pathname.startsWith("/settings/");
  return pathname === item.href || (item.href !== "/" && pathname.startsWith(`${item.href}/`));
}
