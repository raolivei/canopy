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

export function formatCurrency(amount: number, currencyCode: string = "CAD"): string {
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
): string {
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
