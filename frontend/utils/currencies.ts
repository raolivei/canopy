/**
 * ISO 4217 codes offered by currency pickers. The Exchange ledger is the only
 * place that accepts currencies beyond CAD/USD; the rest of the app stays CAD.
 */

export const EXCHANGE_CURRENCIES: { code: string; name: string }[] = [
  { code: "CAD", name: "Canadian dollar" },
  { code: "USD", name: "US dollar" },
  { code: "BRL", name: "Brazilian real" },
  { code: "EUR", name: "Euro" },
  { code: "GBP", name: "British pound" },
  { code: "MXN", name: "Mexican peso" },
  { code: "ARS", name: "Argentine peso" },
  { code: "CLP", name: "Chilean peso" },
  { code: "COP", name: "Colombian peso" },
  { code: "PEN", name: "Peruvian sol" },
  { code: "CHF", name: "Swiss franc" },
  { code: "JPY", name: "Japanese yen" },
  { code: "CNY", name: "Chinese yuan" },
  { code: "INR", name: "Indian rupee" },
  { code: "PHP", name: "Philippine peso" },
  { code: "AUD", name: "Australian dollar" },
  { code: "NZD", name: "New Zealand dollar" },
];

export const CURRENCY_OPTIONS = EXCHANGE_CURRENCIES.map((c) => ({ value: c.code, label: `${c.code} · ${c.name}` }));
