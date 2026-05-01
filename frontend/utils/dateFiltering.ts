import { subDays, subMonths, subYears, startOfYear, parseISO, isAfter, isBefore } from "date-fns";

export type TimePeriod = "5d" | "1m" | "3m" | "6m" | "1y" | "ytd" | "all";

export interface PeriodConfig {
  value: TimePeriod;
  label: string;
}

export const PERIOD_CONFIGS: PeriodConfig[] = [
  { value: "5d", label: "5D" },
  { value: "1m", label: "1M" },
  { value: "3m", label: "3M" },
  { value: "6m", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "ytd", label: "YTD" },
  { value: "all", label: "All" },
];

/**
 * Get the date range for a given time period.
 *
 * @param period - The time period to calculate
 * @returns Object with start date and optional end date
 */
export function getDateRangeForPeriod(period: TimePeriod): { start: Date; end: Date | null } {
  const end = new Date();

  switch (period) {
    case "5d":
      return { start: subDays(end, 5), end };
    case "1m":
      return { start: subMonths(end, 1), end };
    case "3m":
      return { start: subMonths(end, 3), end };
    case "6m":
      return { start: subMonths(end, 6), end };
    case "1y":
      return { start: subYears(end, 1), end };
    case "ytd":
      return { start: startOfYear(end), end };
    case "all":
      return { start: new Date(0), end: null };
    default:
      return { start: new Date(0), end: null };
  }
}

/**
 * Filter an array of items by a time period based on a date accessor function.
 *
 * @param data - Array of items to filter
 * @param dateAccessor - Function to extract date string from each item
 * @param period - Time period to filter by
 * @returns Filtered array
 */
export function filterByPeriod<T>(
  data: T[],
  dateAccessor: (item: T) => string,
  period: TimePeriod
): T[] {
  // Return early for empty data or "all" period
  if (!data || data.length === 0) return [];
  if (period === "all") return data;

  const { start, end } = getDateRangeForPeriod(period);

  return data.filter((item) => {
    try {
      const dateStr = dateAccessor(item);
      const itemDate = parseISO(dateStr);

      // Check if date is valid
      if (isNaN(itemDate.getTime())) {
        console.warn(`Invalid date string: ${dateStr}`);
        return false;
      }

      // Check if date is within range (inclusive on both ends)
      const itemTime = itemDate.getTime();
      const startTime = start.getTime();
      const endTime = end ? end.getTime() : null;

      const afterStart = itemTime >= startTime;
      const beforeEnd = endTime === null || itemTime <= endTime;

      return afterStart && beforeEnd;
    } catch (error) {
      console.error(`Error parsing date for item:`, item, error);
      return false;
    }
  });
}
