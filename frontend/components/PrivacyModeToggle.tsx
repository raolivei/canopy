/**
 * Icon button to toggle amount masking (privacy overlay).
 */

import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/utils/cn";
import { usePrivacyMode } from "@/hooks/usePrivacyMode";

interface PrivacyModeToggleProps {
  className?: string;
  /** When true, show a short text label next to the icon (desktop). */
  showLabel?: boolean;
}

export function PrivacyModeToggle({
  className,
  showLabel = false,
}: PrivacyModeToggleProps) {
  const { privacyMode, togglePrivacyMode, hydrated } = usePrivacyMode();
  const active = hydrated && privacyMode;

  return (
    <button
      type="button"
      onClick={togglePrivacyMode}
      title={active ? "Show amounts" : "Hide amounts (privacy)"}
      aria-pressed={active}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500",
        active
          ? "border-emerald-600 bg-emerald-600 text-white shadow"
          : "border-slate-200 bg-white text-slate-600 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:text-white",
        className,
      )}
    >
      {active ? (
        <EyeOff className="h-4 w-4 shrink-0" aria-hidden />
      ) : (
        <Eye className="h-4 w-4 shrink-0" aria-hidden />
      )}
      {showLabel && (
        <span className="hidden sm:inline">{active ? "Show values" : "Hide values"}</span>
      )}
    </button>
  );
}
