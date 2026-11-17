import { FileText, Wallet } from "lucide-react";

import type { Workspace } from "@/hooks/useWorkspace";
import { cn } from "@/utils/cn";

interface WorkspaceSwitchProps {
  workspace: Workspace;
  onChange: (next: Workspace) => void;
  collapsed?: boolean;
  className?: string;
}

const OPTIONS: { value: Workspace; label: string; icon: typeof Wallet }[] = [
  { value: "wallet", label: "Wallet", icon: Wallet },
  { value: "tax", label: "Tax", icon: FileText },
];

/** Segmented control for the two primary workspaces. */
export function WorkspaceSwitch({ workspace, onChange, collapsed = false, className }: WorkspaceSwitchProps) {
  return (
    <div
      role="group"
      aria-label="Workspace"
      className={cn(
        "flex rounded-lg bg-slate-100 dark:bg-slate-800 p-1 gap-1",
        collapsed ? "flex-col" : "flex-row",
        className,
      )}
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const selected = workspace === value;
        return (
          <button
            key={value}
            type="button"
            aria-pressed={selected}
            aria-label={collapsed ? `${label} workspace` : undefined}
            title={collapsed ? `${label} workspace` : undefined}
            onClick={() => onChange(value)}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
              selected
                ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100",
            )}
          >
            <Icon className="w-4 h-4 shrink-0" aria-hidden />
            {!collapsed && <span>{label}</span>}
          </button>
        );
      })}
    </div>
  );
}
