/**
 * Currency + percent formatters that respect privacy mode.
 *
 * Prefer this over importing ``formatCurrency`` directly on any page
 * that shows balances the user might want to hide.
 */

import { useCallback } from "react";
import {
  formatCurrency as formatCurrencyRaw,
  formatCurrencyCompact as formatCurrencyCompactRaw,
} from "@/utils/currency";
import { usePrivacyMode } from "@/hooks/usePrivacyMode";

export function useMoney(): {
  fmt: (amount: number, currencyCode?: string) => string;
  fmtCompact: (amount: number, currencyCode?: string) => string;
  pct: (value: number, fractionDigits?: number) => string;
  privacyMode: boolean;
} {
  const { privacyMode } = usePrivacyMode();

  const fmt = useCallback(
    (amount: number, currencyCode?: string) =>
      formatCurrencyRaw(amount, currencyCode ?? "CAD", { private: privacyMode }),
    [privacyMode],
  );

  const fmtCompact = useCallback(
    (amount: number, currencyCode?: string) =>
      formatCurrencyCompactRaw(amount, currencyCode ?? "CAD", { private: privacyMode }),
    [privacyMode],
  );

  const pct = useCallback(
    (value: number, fractionDigits = 2) => {
      if (privacyMode) {
        const width = Math.max(4, fractionDigits + 2);
        return `${"*".repeat(width)}%`;
      }
      if (!Number.isFinite(value)) return `${(0).toFixed(fractionDigits)}%`;
      return `${value.toFixed(fractionDigits)}%`;
    },
    [privacyMode],
  );

  return { fmt, fmtCompact, pct, privacyMode };
}
