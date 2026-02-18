"""
Currency models and conversion utilities.

This module provides synchronous access to currency conversion.
For async operations with live rates, use backend.services.exchange_rate_service.
"""

from pydantic import BaseModel
from typing import Dict
from datetime import datetime

from backend.services.exchange_rate_service import (
    convert_currency_sync,
    get_supported_currencies as _get_supported_currencies,
    SUPPORTED_CURRENCIES,
)


class ExchangeRate(BaseModel):
    """Exchange rate data model."""
    base_currency: str
    rates: Dict[str, float]
    date: datetime


class CurrencyConversion(BaseModel):
    """Currency conversion result."""
    original_amount: float
    original_currency: str
    converted_amount: float
    converted_currency: str
    exchange_rate: float
    date: str


# Re-export fallback rates for backwards compatibility
DEFAULT_EXCHANGE_RATES = {
    "USD": {"USD": 1.0, "CAD": 1.36, "BRL": 5.05, "EUR": 0.92, "GBP": 0.79},
    "CAD": {"USD": 0.74, "CAD": 1.0, "BRL": 3.72, "EUR": 0.68, "GBP": 0.58},
    "BRL": {"USD": 0.20, "CAD": 0.27, "BRL": 1.0, "EUR": 0.18, "GBP": 0.16},
    "EUR": {"USD": 1.09, "CAD": 1.48, "BRL": 5.50, "EUR": 1.0, "GBP": 0.86},
    "GBP": {"USD": 1.27, "CAD": 1.72, "BRL": 6.40, "EUR": 1.16, "GBP": 1.0},
}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Convert amount from one currency to another.
    
    Uses cached live rates when available, falls back to static rates.
    For async conversion with guaranteed live rates, use:
        from backend.services.exchange_rate_service import convert_currency_live
    """
    return convert_currency_sync(amount, from_currency, to_currency)


def get_supported_currencies() -> list[str]:
    """Get list of supported currencies."""
    return _get_supported_currencies()

