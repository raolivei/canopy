export interface Currency {
  code: string
  symbol: string
  name: string
}

export const CURRENCIES: Currency[] = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'BRL', symbol: 'R$', name: 'Brazilian Real' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
]

export function formatCurrency(amount: number, currencyCode: string): string {
  const currency = CURRENCIES.find(c => c.code === currencyCode) || CURRENCIES[0]
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currencyCode,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatCurrencyCompact(amount: number, currencyCode: string): string {
  const currency = CURRENCIES.find(c => c.code === currencyCode) || CURRENCIES[0]
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currencyCode,
    notation: 'compact',
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }).format(amount)
}

export function getCurrencySymbol(currencyCode: string): string {
  const currency = CURRENCIES.find(c => c.code === currencyCode) || CURRENCIES[0]
  return currency.symbol
}

export async function convertCurrency(
  amount: number,
  fromCurrency: string,
  toCurrency: string
): Promise<number> {
  if (fromCurrency === toCurrency) return amount
  
  try {
    const response = await fetch(
      `http://localhost:8000/v1/currency/convert?amount=${amount}&from_currency=${fromCurrency}&to_currency=${toCurrency}`
    )
    const data = await response.json()
    return data.converted_amount
  } catch (error) {
    console.error('Currency conversion failed:', error)
    return amount
  }
}

