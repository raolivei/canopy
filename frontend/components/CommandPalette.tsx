import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/router";
import { createPortal } from "react-dom";
import {
  Search,
  Home,
  TrendingUp,
  DollarSign,
  Wallet,
  Target,
  Upload,
  Plug,
  Settings,
  Plus,
  Moon,
  Sun,
  ArrowRight,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/utils/cn";

interface CommandItem {
  id: string;
  title: string;
  description?: string;
  icon: React.ReactNode;
  category: string;
  action: () => void;
  keywords?: string[];
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setIsDarkMode(document.documentElement.classList.contains("dark"));
    }
  }, [isOpen]);

  const toggleDarkMode = useCallback(() => {
    const newValue = !isDarkMode;
    setIsDarkMode(newValue);
    if (newValue) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("darkMode", "true");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("darkMode", "false");
    }
    onClose();
  }, [isDarkMode, onClose]);

  const commands: CommandItem[] = useMemo(
    () => [
      {
        id: "dashboard",
        title: "Go to Dashboard",
        icon: <Home className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/"),
        keywords: ["home", "overview"],
      },
      {
        id: "portfolio",
        title: "Go to Portfolio",
        icon: <TrendingUp className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/portfolio"),
        keywords: ["investments", "holdings", "stocks"],
      },
      {
        id: "transactions",
        title: "Go to Transactions",
        icon: <DollarSign className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/transactions"),
        keywords: ["expenses", "income", "payments"],
      },
      {
        id: "accounts",
        title: "Go to Accounts",
        icon: <Wallet className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/accounts"),
        keywords: ["bank", "balance"],
      },
      {
        id: "insights",
        title: "Go to Insights",
        icon: <Target className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/insights"),
        keywords: ["analytics", "reports", "statistics"],
      },
      {
        id: "import",
        title: "Import Data",
        icon: <Upload className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/import"),
        keywords: ["csv", "upload", "file"],
      },
      {
        id: "integrations",
        title: "Go to Integrations",
        icon: <Plug className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/settings/integrations"),
        keywords: ["connect", "api", "sync"],
      },
      {
        id: "settings",
        title: "Go to Settings",
        icon: <Settings className="w-4 h-4" />,
        category: "Navigation",
        action: () => router.push("/settings"),
        keywords: ["preferences", "config"],
      },
      {
        id: "add-transaction",
        title: "Add Transaction",
        description: "Create a new transaction",
        icon: <Plus className="w-4 h-4" />,
        category: "Actions",
        action: () => {
          router.push("/transactions?action=add");
          onClose();
        },
        keywords: ["create", "new", "expense", "income"],
      },
      {
        id: "toggle-theme",
        title: isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode",
        description: "Toggle between light and dark theme",
        icon: isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />,
        category: "Settings",
        action: toggleDarkMode,
        keywords: ["theme", "dark", "light", "mode"],
      },
    ],
    [router, isDarkMode, toggleDarkMode, onClose]
  );

  const filteredCommands = useMemo(() => {
    if (!query) return commands;

    const lowerQuery = query.toLowerCase();
    return commands.filter((cmd) => {
      const titleMatch = cmd.title.toLowerCase().includes(lowerQuery);
      const descMatch = cmd.description?.toLowerCase().includes(lowerQuery);
      const keywordMatch = cmd.keywords?.some((k) =>
        k.toLowerCase().includes(lowerQuery)
      );
      return titleMatch || descMatch || keywordMatch;
    });
  }, [commands, query]);

  const groupedCommands = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    filteredCommands.forEach((cmd) => {
      if (!groups[cmd.category]) {
        groups[cmd.category] = [];
      }
      groups[cmd.category].push(cmd);
    });
    return groups;
  }, [filteredCommands]);

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < filteredCommands.length - 1 ? prev + 1 : 0
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev > 0 ? prev - 1 : filteredCommands.length - 1
          );
          break;
        case "Enter":
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action();
            onClose();
          }
          break;
        case "Escape":
          e.preventDefault();
          onClose();
          break;
      }
    },
    [isOpen, filteredCommands, selectedIndex, onClose]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (listRef.current) {
      const selectedElement = listRef.current.querySelector(
        `[data-index="${selectedIndex}"]`
      );
      selectedElement?.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  const content = (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-x-4 top-[20%] z-50 mx-auto max-w-xl"
          >
            <div className="overflow-hidden rounded-xl bg-white dark:bg-slate-900 shadow-2xl border border-slate-200 dark:border-slate-800">
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 border-b border-slate-200 dark:border-slate-800">
                <Search className="w-5 h-5 text-slate-400" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search commands..."
                  className="flex-1 h-14 bg-transparent text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none"
                />
                <kbd className="hidden sm:flex items-center gap-1 px-2 py-1 text-xs text-slate-400 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  ESC
                </kbd>
              </div>

              {/* Results */}
              <div ref={listRef} className="max-h-80 overflow-y-auto p-2">
                {filteredCommands.length === 0 ? (
                  <div className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                    No results found for "{query}"
                  </div>
                ) : (
                  Object.entries(groupedCommands).map(([category, items]) => (
                    <div key={category} className="mb-2 last:mb-0">
                      <div className="px-3 py-1.5 text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                        {category}
                      </div>
                      {items.map((item, index) => {
                        const globalIndex = filteredCommands.indexOf(item);
                        const isSelected = globalIndex === selectedIndex;

                        return (
                          <button
                            key={item.id}
                            data-index={globalIndex}
                            onClick={() => {
                              item.action();
                              onClose();
                            }}
                            onMouseEnter={() => setSelectedIndex(globalIndex)}
                            className={cn(
                              "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors",
                              isSelected
                                ? "bg-primary-50 dark:bg-primary-950/50 text-primary-700 dark:text-primary-300"
                                : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                            )}
                          >
                            <div
                              className={cn(
                                "p-1.5 rounded-md",
                                isSelected
                                  ? "bg-primary-100 dark:bg-primary-900/50 text-primary-600 dark:text-primary-400"
                                  : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                              )}
                            >
                              {item.icon}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium truncate">
                                {item.title}
                              </div>
                              {item.description && (
                                <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                                  {item.description}
                                </div>
                              )}
                            </div>
                            {isSelected && (
                              <ArrowRight className="w-4 h-4 text-primary-500" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-4 py-2 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 text-xs text-slate-500 dark:text-slate-400">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                      ↑↓
                    </kbd>
                    Navigate
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                      ↵
                    </kbd>
                    Select
                  </span>
                </div>
                <span className="text-slate-400 dark:text-slate-500">
                  {filteredCommands.length} commands
                </span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );

  if (typeof window === "undefined") return null;

  return createPortal(content, document.body);
}
