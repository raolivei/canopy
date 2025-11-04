import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <link rel="icon" href="/brand/ledgerlight-icon-32.png" sizes="32x32" type="image/png" />
        <link rel="icon" href="/brand/ledgerlight-icon-64.png" sizes="64x64" type="image/png" />
        <link rel="apple-touch-icon" href="/brand/ledgerlight-icon-512.png" />
        <meta name="theme-color" content="#0C2650" />
        <meta property="og:site_name" content="LedgerLight" />
        <meta property="og:title" content="LedgerLight" />
        <meta
          property="og:description"
          content="Illuminate your financial operations with LedgerLight's real-time ledger intelligence."
        />
        <meta property="og:image" content="/brand/ledgerlight-banner-dark.png" />
        <meta property="og:image:alt" content="LedgerLight hero banner" />
        <meta property="og:image:width" content="1600" />
        <meta property="og:image:height" content="900" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="LedgerLight" />
        <meta
          name="twitter:description"
          content="Illuminate your financial operations with LedgerLight's real-time ledger intelligence."
        />
        <meta name="twitter:image" content="/brand/ledgerlight-banner-dark.png" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}
