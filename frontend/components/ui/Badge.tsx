import React from "react";
import { cn } from "@/utils/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "primary" | "success" | "warning" | "danger" | "outline";
  size?: "sm" | "md";
  dot?: boolean;
}

export function Badge({
  className,
  variant = "default",
  size = "md",
  dot = false,
  children,
  ...props
}: BadgeProps) {
  const variants = {
    default: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    primary:
      "bg-primary-100 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300",
    success:
      "bg-success-100 text-success-700 dark:bg-success-900/50 dark:text-success-300",
    warning:
      "bg-warning-100 text-warning-700 dark:bg-warning-900/50 dark:text-warning-300",
    danger:
      "bg-danger-100 text-danger-700 dark:bg-danger-900/50 dark:text-danger-300",
    outline:
      "bg-transparent border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300",
  };

  const dotColors = {
    default: "bg-slate-500",
    primary: "bg-primary-500",
    success: "bg-success-500",
    warning: "bg-warning-500",
    danger: "bg-danger-500",
    outline: "bg-slate-500",
  };

  const sizes = {
    sm: "px-1.5 py-0.5 text-[10px]",
    md: "px-2 py-0.5 text-xs",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-medium rounded-full",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span className={cn("w-1.5 h-1.5 rounded-full", dotColors[variant])} />
      )}
      {children}
    </span>
  );
}

export interface StatusBadgeProps {
  status: "active" | "inactive" | "pending" | "error" | "success";
  label?: string;
  showDot?: boolean;
}

export function StatusBadge({
  status,
  label,
  showDot = true,
}: StatusBadgeProps) {
  const statusConfig = {
    active: { variant: "success" as const, defaultLabel: "Active" },
    inactive: { variant: "default" as const, defaultLabel: "Inactive" },
    pending: { variant: "warning" as const, defaultLabel: "Pending" },
    error: { variant: "danger" as const, defaultLabel: "Error" },
    success: { variant: "success" as const, defaultLabel: "Success" },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} dot={showDot}>
      {label || config.defaultLabel}
    </Badge>
  );
}

export interface CurrencyBadgeProps {
  currency: string;
  className?: string;
}

export function CurrencyBadge({ currency, className }: CurrencyBadgeProps) {
  const currencyColors: Record<string, string> = {
    USD: "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300",
    CAD: "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300",
    BRL: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300",
    EUR: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300",
    GBP: "bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full",
        currencyColors[currency] ||
          "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
        className
      )}
    >
      {currency}
    </span>
  );
}
