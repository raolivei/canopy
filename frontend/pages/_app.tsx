import "@/styles/globals.css";
import type { AppProps } from "next/app";
import Head from "next/head";
import ErrorBoundary from "@/components/ErrorBoundary";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

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
      <ErrorBoundary>
        <Head>
          <link
            rel="icon"
            href="/brand/canopy-icon-32.png"
            sizes="32x32"
            type="image/png"
          />
          <link
            rel="icon"
            href="/brand/canopy-icon-64.png"
            sizes="64x64"
            type="image/png"
          />
          <link
            rel="icon"
            href="/brand/canopy-icon-192.png"
            sizes="192x192"
            type="image/png"
          />
          <link
            rel="icon"
            href="/brand/canopy-icon-256.png"
            sizes="256x256"
            type="image/png"
          />
          <link
            rel="apple-touch-icon"
            sizes="180x180"
            href="/brand/canopy-icon-180.png"
          />
          <meta name="theme-color" content="#D4AF37" />
          <meta property="og:site_name" content="Canopy" />
          <meta
            property="og:title"
            content="Canopy - Your financial life under one canopy"
          />
          <meta
            property="og:description"
            content="Self-hosted personal finance, investment, and budgeting dashboard. Privacy-first, offline-friendly, Monarch-level UX."
          />
          <meta
            property="og:image"
            content="/brand/canopy-banner-dark-og.png"
          />
          <meta property="og:image:alt" content="Canopy hero banner" />
          <meta property="og:image:width" content="1600" />
          <meta property="og:image:height" content="900" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta
            name="twitter:title"
            content="Canopy - Your financial life under one canopy"
          />
          <meta
            name="twitter:description"
            content="Self-hosted personal finance, investment, and budgeting dashboard. Privacy-first, offline-friendly, Monarch-level UX."
          />
          <meta
            name="twitter:image"
            content="/brand/canopy-banner-dark-og.png"
          />
        </Head>
        <Component {...pageProps} />
      </ErrorBoundary>
    </QueryClientProvider>
  );
}
