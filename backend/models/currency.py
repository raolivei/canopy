from pydantic import BaseModel
from typing import Dict
from datetime import datetime

class ExchangeRate(BaseModel):
    base_currency: str
    rates: Dict[str, float]
    date: datetime

# Mock exchange rates (in production, fetch from API)
DEFAULT_EXCHANGE_RATES = {
    "USD": {
        "USD": 1.0,
        "CAD": 1.35,
        "BRL": 5.10,
        "EUR": 0.92,
        "GBP": 0.79,
    },
    "CAD": {
        "USD": 0.74,
        "CAD": 1.0,
        "BRL": 3.78,
        "EUR": 0.68,
        "GBP": 0.59,
    },
    "BRL": {
        "USD": 0.20,
        "CAD": 0.26,
        "BRL": 1.0,
        "EUR": 0.18,
        "GBP": 0.16,
    },
    "EUR": {
        "USD": 1.09,
        "CAD": 1.47,
        "BRL": 5.56,
        "EUR": 1.0,
        "GBP": 0.86,
    },
    "GBP": {
        "USD": 1.27,
        "CAD": 1.71,
        "BRL": 6.46,
        "EUR": 1.16,
        "GBP": 1.0,
    },
}

def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert amount from one currency to another"""
    if from_currency == to_currency:
        return amount
    
    rates = DEFAULT_EXCHANGE_RATES.get(from_currency, {})
    rate = rates.get(to_currency, 1.0)
    return amount * rate

def get_supported_currencies() -> list[str]:
    """Get list of supported currencies"""
    return list(DEFAULT_EXCHANGE_RATES.keys())

