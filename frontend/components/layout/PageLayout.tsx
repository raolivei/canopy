import { useState, useEffect, useCallback } from "react";
import Head from "next/head";
import Sidebar from "./Sidebar";
import MobileNav from "./MobileNav";
import CommandPalette from "../CommandPalette";
import { cn } from "@/utils/cn";

interface PageLayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
  fullWidth?: boolean;
}

export default function PageLayout({
  children,
  title = "Canopy",
  description,
  className,
  fullWidth = false,
}: PageLayoutProps) {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    const savedCollapsed = localStorage.getItem("sidebar-collapsed");
    if (savedCollapsed) {
      setIsSidebarCollapsed(savedCollapsed === "true");
    }

    const handleStorageChange = () => {
      const collapsed = localStorage.getItem("sidebar-collapsed");
      setIsSidebarCollapsed(collapsed === "true");
    };

    window.addEventListener("storage", handleStorageChange);
    
    const interval = setInterval(() => {
      const collapsed = localStorage.getItem("sidebar-collapsed");
      setIsSidebarCollapsed(collapsed === "true");
    }, 100);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  const handleCommandPaletteOpen = useCallback(() => {
    setIsCommandPaletteOpen(true);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen(true);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const pageTitle = title === "Canopy" ? title : `${title} - Canopy`;

  return (
    <>
      <Head>
        <title>{pageTitle}</title>
        {description && <meta name="description" content={description} />}
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
      </Head>

      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        {/* Sidebar - Hidden on mobile */}
        <div className="hidden lg:block">
          <Sidebar onCommandPaletteOpen={handleCommandPaletteOpen} />
        </div>

        {/* Main Content */}
        <main
          className={cn(
            "min-h-screen transition-all duration-200",
            "pb-20 lg:pb-0",
            isSidebarCollapsed ? "lg:pl-16" : "lg:pl-60",
            className
          )}
        >
          <div
            className={cn(
              "p-4 lg:p-8",
              !fullWidth && "max-w-7xl mx-auto"
            )}
          >
            {children}
          </div>
        </main>

        {/* Mobile Navigation */}
        <MobileNav />

        {/* Command Palette */}
        <CommandPalette
          isOpen={isCommandPaletteOpen}
          onClose={() => setIsCommandPaletteOpen(false)}
        />
      </div>
    </>
  );
}

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("mb-6 lg:mb-8", className)}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-slate-500 dark:text-slate-400">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3">{actions}</div>}
      </div>
    </div>
  );
}
