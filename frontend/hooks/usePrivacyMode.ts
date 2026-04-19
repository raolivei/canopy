/**
 * Privacy overlay for amounts (screenshots, demos, shoulder surfing).
 *
 * When enabled, currency formatters mask values as asterisks. State is
 * persisted in ``localStorage`` and broadcast with a custom event so
 * every consumer of :func:`useMoney` re-renders in sync.
 *
 * Initial render always uses ``false`` (same hydration strategy as
 * ``useCurrencyView``) — the real value is read once in ``useEffect``.
 */

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "canopy.privacyMode";
const EVENT_NAME = "canopy:privacy-mode-changed";

function readStored(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

export function usePrivacyMode(): {
  privacyMode: boolean;
  setPrivacyMode: (next: boolean) => void;
  togglePrivacyMode: () => void;
  hydrated: boolean;
} {
  const [privacyMode, setPrivacyModeState] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setPrivacyModeState(readStored());
    setHydrated(true);

    const onCustom = () => setPrivacyModeState(readStored());
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setPrivacyModeState(readStored());
    };
    window.addEventListener(EVENT_NAME, onCustom);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(EVENT_NAME, onCustom);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const persist = useCallback((next: boolean) => {
    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(STORAGE_KEY, next ? "true" : "false");
      } catch {
        // private mode / quota — in-memory toggle still works
      }
      window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: { value: next } }));
    }
  }, []);

  const setPrivacyMode = useCallback(
    (next: boolean) => {
      setPrivacyModeState(next);
      persist(next);
    },
    [persist],
  );

  const togglePrivacyMode = useCallback(() => {
    setPrivacyModeState((prev) => {
      const next = !prev;
      persist(next);
      return next;
    });
  }, [persist]);

  return { privacyMode, setPrivacyMode, togglePrivacyMode, hydrated };
}
