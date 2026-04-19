export const CHART_COLORS = {
  primary: "#14b8a6",
  primaryDark: "#0d9488",
  accent: "#6366f1",
  success: "#10b981",
  successDark: "#059669",
  warning: "#f59e0b",
  danger: "#ef4444",
  purple: "#8b5cf6",
  pink: "#ec4899",
  cyan: "#06b6d4",
  blue: "#3b82f6",
  orange: "#f97316",
} as const;

export const CHART_PALETTE = [
  CHART_COLORS.primary,
  CHART_COLORS.accent,
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.danger,
  CHART_COLORS.purple,
  CHART_COLORS.pink,
  CHART_COLORS.cyan,
] as const;

export const ALLOCATION_PALETTE = [
  CHART_COLORS.blue,
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.purple,
  CHART_COLORS.primary,
  CHART_COLORS.pink,
  CHART_COLORS.cyan,
  CHART_COLORS.orange,
] as const;

export function getGradientDef(id: string, color: string, opacity = 0.3) {
  return {
    id,
    color,
    topOpacity: opacity,
    bottomOpacity: 0,
  };
}

export const tooltipStyle = {
  light: {
    backgroundColor: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "10px",
    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    padding: "12px",
    fontSize: "13px",
  },
  dark: {
    backgroundColor: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: "10px",
    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.3)",
    padding: "12px",
    fontSize: "13px",
    color: "#f1f5f9",
  },
} as const;

export function getTooltipStyle(isDarkMode: boolean) {
  return isDarkMode ? tooltipStyle.dark : tooltipStyle.light;
}

export const gridStyle = {
  strokeDasharray: "3 3",
  light: { stroke: "#e2e8f0" },
  dark: { stroke: "#1e293b" },
} as const;

export function getGridProps(isDarkMode: boolean) {
  return {
    strokeDasharray: gridStyle.strokeDasharray,
    stroke: isDarkMode ? gridStyle.dark.stroke : gridStyle.light.stroke,
  };
}

export const axisStyle = {
  light: { fill: "#64748b", fontSize: 12 },
  dark: { fill: "#94a3b8", fontSize: 12 },
} as const;

export function getAxisProps(isDarkMode: boolean) {
  return {
    tick: isDarkMode ? axisStyle.dark : axisStyle.light,
    tickLine: false,
    axisLine: false,
  };
}

export const chartMargin = {
  compact: { top: 5, right: 5, left: 0, bottom: 0 },
  default: { top: 10, right: 10, left: 0, bottom: 0 },
  spacious: { top: 20, right: 20, left: 10, bottom: 10 },
} as const;

export const chartHeight = {
  sm: 200,
  md: 256,
  lg: 320,
  xl: 400,
} as const;

export function formatCompactValue(value: number, prefix = "$"): string {
  if (Math.abs(value) >= 1_000_000) {
    return `${prefix}${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `${prefix}${(value / 1_000).toFixed(0)}K`;
  }
  return `${prefix}${value.toFixed(0)}`;
}

export function isDarkMode(): boolean {
  if (typeof window === "undefined") return false;
  return document.documentElement.classList.contains("dark");
}
