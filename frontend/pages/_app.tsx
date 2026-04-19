import "@/styles/globals.css";
import type { AppProps } from "next/app";
import Head from "next/head";
import ErrorBoundary from "@/components/ErrorBoundary";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ToastProvider } from "@/components/ui/Toast";

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
      <ErrorBoundary>
        <Head>
          <link rel="icon" type="image/svg+xml" href="/brand/canopy-icon.svg" />
          <link rel="apple-touch-icon" sizes="1024x1024" href="/brand/canopy-icon-1024.png" />
          <meta name="theme-color" content="#0f2b1f" />
          <meta property="og:site_name" content="Canopy" />
          <meta property="og:title" content="Canopy — Continuous net-worth tracking" />
          <meta
            property="og:description"
            content="Self-hosted personal finance. Drop Wealthsimple statements, snapshot the rest, see one net-worth number over time."
          />
          <meta property="og:image" content="/brand/canopy-banner-dark-og.png" />
          <meta property="og:image:alt" content="Canopy — Continuous net-worth tracking" />
          <meta property="og:image:width" content="1200" />
          <meta property="og:image:height" content="630" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content="Canopy — Continuous net-worth tracking" />
          <meta
            name="twitter:description"
            content="Self-hosted personal finance. Drop Wealthsimple statements, snapshot the rest, see one net-worth number over time."
          />
          <meta name="twitter:image" content="/brand/canopy-banner-dark-og.png" />
        </Head>
        <Component {...pageProps} />
      </ErrorBoundary>
      </ToastProvider>
    </QueryClientProvider>
  );
}
