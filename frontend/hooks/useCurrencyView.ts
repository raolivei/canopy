/**
 * Questrade-style currency view hook.
 *
 * Canopy supports four display modes, mirroring Questrade's account
 * summary:
 *
 *   - "CAD"           - native CAD balances only
 *   - "USD"           - native USD balances only
 *   - "COMBINED_CAD"  - all balances converted to CAD (default)
 *   - "COMBINED_USD"  - all balances converted to USD
 *
 * The current selection is persisted in localStorage so it follows the
 * user between page loads and tabs (same origin). When the hook is
 * used during SSR or before hydration, it returns the default until
 * the client effect runs so the initial HTML matches and we avoid
 * hydration mismatch warnings.
 */

import { useCallback, useEffect, useState } from "react";

export type CurrencyView = "CAD" | "USD" | "COMBINED_CAD" | "COMBINED_USD";

export const DEFAULT_CURRENCY_VIEW: CurrencyView = "COMBINED_CAD";

const STORAGE_KEY = "canopy.currencyView";

/** Broadcast view changes to other components in the same tab. */
const EVENT_NAME = "canopy:currency-view-changed";

function readStoredView(): CurrencyView {
  if (typeof window === "undefined") return DEFAULT_CURRENCY_VIEW;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === "CAD" || raw === "USD" || raw === "COMBINED_CAD" || raw === "COMBINED_USD") {
      return raw;
    }
  } catch {
    // localStorage can throw in private mode; fall through to default.
  }
  return DEFAULT_CURRENCY_VIEW;
}

export function useCurrencyView(): {
  view: CurrencyView;
  setView: (next: CurrencyView) => void;
  hydrated: boolean;
} {
  // Always initialise with the default so SSR and the first client render
  // agree. A separate effect swaps in the stored value once we're on the
  // client, avoiding the "Hydration failed because the initial UI does
  // not match" error we already fought off with the toast portals.
  const [view, setViewState] = useState<CurrencyView>(DEFAULT_CURRENCY_VIEW);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setViewState(readStoredView());
    setHydrated(true);

    const handler = (evt: Event) => {
      const custom = evt as CustomEvent<{ view: CurrencyView }>;
      if (custom.detail?.view) setViewState(custom.detail.view);
    };
    const storageHandler = (evt: StorageEvent) => {
      if (evt.key === STORAGE_KEY && evt.newValue) {
        setViewState(evt.newValue as CurrencyView);
      }
    };

    window.addEventListener(EVENT_NAME, handler as EventListener);
    window.addEventListener("storage", storageHandler);
    return () => {
      window.removeEventListener(EVENT_NAME, handler as EventListener);
      window.removeEventListener("storage", storageHandler);
    };
  }, []);

  const setView = useCallback((next: CurrencyView) => {
    setViewState(next);
    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // Silently ignore storage failures; in-memory view still works.
      }
      window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: { view: next } }));
    }
  }, []);

  return { view, setView, hydrated };
}

/** Currency the selected view is denominated in (for formatCurrency). */
export function viewCurrency(view: CurrencyView): "CAD" | "USD" {
  switch (view) {
    case "USD":
    case "COMBINED_USD":
      return "USD";
    case "CAD":
    case "COMBINED_CAD":
    default:
      return "CAD";
  }
}

/** Human-readable label for the selected view (e.g. for headings). */
export function viewLabel(view: CurrencyView): string {
  switch (view) {
    case "CAD":
      return "CAD only";
    case "USD":
      return "USD only";
    case "COMBINED_CAD":
      return "Combined (CAD)";
    case "COMBINED_USD":
      return "Combined (USD)";
  }
}

/**
 * Convert a native amount into the selected view's currency using the
 * given USD/CAD rate.
 *
 * The semantics match Questrade: "CAD only" and "USD only" filter;
 * they do NOT convert. So a USD-native amount under a CAD-only view
 * returns 0 (it isn't part of that bucket). Combined views convert.
 */
export function convertForView(
  amount: number,
  nativeCurrency: string,
  view: CurrencyView,
  usdCadRate: number | null | undefined,
): number {
  const from = (nativeCurrency || "CAD").toUpperCase();
  if (view === "CAD") return from === "CAD" ? amount : 0;
  if (view === "USD") return from === "USD" ? amount : 0;

  if (!usdCadRate || usdCadRate <= 0) {
    // No FX available: fall back to filtering (so Combined CAD behaves
    // like CAD-only and Combined USD behaves like USD-only, matching
    // what the backend does when the cache is empty).
    if (view === "COMBINED_CAD") return from === "CAD" ? amount : 0;
    return from === "USD" ? amount : 0;
  }

  if (view === "COMBINED_CAD") {
    return from === "CAD" ? amount : amount * usdCadRate;
  }
  // COMBINED_USD
  return from === "USD" ? amount : amount / usdCadRate;
}

/** True when the view is currency-specific (vs. combined). */
export function isSingleCurrencyView(view: CurrencyView): boolean {
  return view === "CAD" || view === "USD";
}
