import React, { forwardRef } from "react";
import { cn } from "@/utils/cn";
import { AlertCircle, TrendingUp, TrendingDown, Lightbulb, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./Card";

export type InsightType = "warning" | "success" | "info" | "neutral";

export interface InsightCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  type?: InsightType;
  metric?: string | number;
  metricLabel?: string;
  description?: string;
  subtext?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const typeStyles: Record<InsightType, { bg: string; border: string; icon: React.ReactNode; badge: string }> = {
  warning: {
    bg: "bg-warning-50 dark:bg-warning-950/30",
    border: "border-warning-200 dark:border-warning-800",
    icon: <AlertCircle className="w-5 h-5 text-warning-600 dark:text-warning-400" />,
    badge: "bg-warning-100 dark:bg-warning-900/50 text-warning-800 dark:text-warning-200",
  },
  success: {
    bg: "bg-success-50 dark:bg-success-950/30",
    border: "border-success-200 dark:border-success-800",
    icon: <CheckCircle className="w-5 h-5 text-success-600 dark:text-success-400" />,
    badge: "bg-success-100 dark:bg-success-900/50 text-success-800 dark:text-success-200",
  },
  info: {
    bg: "bg-primary-50 dark:bg-primary-950/30",
    border: "border-primary-200 dark:border-primary-800",
    icon: <Lightbulb className="w-5 h-5 text-primary-600 dark:text-primary-400" />,
    badge: "bg-primary-100 dark:bg-primary-900/50 text-primary-800 dark:text-primary-200",
  },
  neutral: {
    bg: "bg-slate-50 dark:bg-slate-800/30",
    border: "border-slate-200 dark:border-slate-700",
    icon: <TrendingUp className="w-5 h-5 text-slate-600 dark:text-slate-400" />,
    badge: "bg-slate-100 dark:bg-slate-700/50 text-slate-800 dark:text-slate-200",
  },
};

const InsightCard = forwardRef<HTMLDivElement, InsightCardProps>(
  (
    {
      className,
      title,
      type = "neutral",
      metric,
      metricLabel,
      description,
      subtext,
      action,
      ...props
    },
    ref
  ) => {
    const style = typeStyles[type];

    return (
      <Card ref={ref} className={cn(style.bg, style.border, "border", className)} {...props}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 flex-1">
              <div className="flex-shrink-0 mt-0.5">{style.icon}</div>
              <div className="flex-1">
                <CardTitle className="text-base font-semibold text-slate-900 dark:text-white">
                  {title}
                </CardTitle>
                {description && (
                  <CardDescription className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                    {description}
                  </CardDescription>
                )}
              </div>
            </div>
            {metric !== undefined && (
              <div className={cn("px-3 py-1 rounded-full text-sm font-semibold whitespace-nowrap", style.badge)}>
                {metric}
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          <div className="space-y-2">
            {metricLabel && (
              <p className="text-xs text-slate-500 dark:text-slate-400">{metricLabel}</p>
            )}
            {subtext && (
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                {subtext}
              </p>
            )}
            {action && (
              <button
                onClick={action.onClick}
                className="mt-3 inline-flex items-center text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
              >
                {action.label}
                <span className="ml-1">&rarr;</span>
              </button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }
);

InsightCard.displayName = "InsightCard";

export { InsightCard };
