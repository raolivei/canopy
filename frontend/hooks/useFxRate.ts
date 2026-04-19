/**
 * Hook that fetches and caches the current USD/CAD rate from the
 * Canopy backend (which in turn hits Bank of Canada).
 *
 * Returns the rate, the date it was observed, and an ``isStale`` flag
 * the UI can use to surface a banner when BoC is unreachable. The
 * rate is revalidated every 10 minutes while the tab is open —
 * refreshing more aggressively is pointless since BoC only publishes
 * daily.
 */

import { useQuery } from "@tanstack/react-query";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export interface UsdCadRate {
  pair: "USDCAD";
  rate: number | null;
  as_of_date: string | null;
  source: string | null;
  is_stale: boolean;
}

const TEN_MINUTES = 10 * 60 * 1000;

export function useFxRate() {
  return useQuery<UsdCadRate>({
    queryKey: ["fx", "usd-cad"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/fx/usd-cad`);
      if (!res.ok) {
        throw new Error(`Failed to load FX rate (${res.status})`);
      }
      return res.json();
    },
    staleTime: TEN_MINUTES,
    refetchOnWindowFocus: false,
    retry: 1,
  });
}
