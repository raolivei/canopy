// Canopy is a CAD-only Canadian investments app. This helper exists purely
// to keep the existing `formatCurrency(amount, "CAD")` call sites happy while
// we standardise the codebase on CAD.

export const CAD = "CAD" as const;

export interface Currency {
  code: "CAD";
  symbol: "C$";
  name: "Canadian Dollar";
}

export const CAD_CURRENCY: Currency = {
  code: "CAD",
  symbol: "C$",
  name: "Canadian Dollar",
};

export const CURRENCIES: Currency[] = [CAD_CURRENCY];

export interface FormatCurrencyOptions {
  /** When true, mask the numeric value with asterisks (privacy). */
  private?: boolean;
}

/** Placeholder string roughly matching formatted currency width. */
function privateCurrencyMask(currencyCode: string): string {
  const c = (currencyCode || "CAD").toUpperCase();
  const body = "*".repeat(10);
  if (c === "USD") return `$${body}`;
  if (c === "CAD") return `CA$${body}`;
  return `${c} ${body}`;
}

export function formatCurrency(
  amount: number,
  currencyCode: string = "CAD",
  opts?: FormatCurrencyOptions,
): string {
  if (opts?.private) {
    return privateCurrencyMask(currencyCode);
  }
  if (!Number.isFinite(amount)) amount = 0;
  return new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency: currencyCode || "CAD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatCurrencyCompact(
  amount: number,
  currencyCode: string = "CAD",
  opts?: FormatCurrencyOptions,
): string {
  if (opts?.private) {
    const c = (currencyCode || "CAD").toUpperCase();
    const body = "*".repeat(6);
    if (c === "USD") return `$${body}`;
    if (c === "CAD") return `CA$${body}`;
    return `${c} ${body}`;
  }
  if (!Number.isFinite(amount)) amount = 0;
  return new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency: currencyCode || "CAD",
    notation: "compact",
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }).format(amount);
}

export function getCurrencySymbol(_currencyCode: string = "CAD"): string {
  return "C$";
}
