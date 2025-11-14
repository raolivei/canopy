from fastapi import APIRouter
from typing import Dict
from backend.models.currency import (
    get_supported_currencies,
    convert_currency,
    DEFAULT_EXCHANGE_RATES,
    ExchangeRate,
)
from datetime import datetime

router = APIRouter(prefix="/v1/currency", tags=["currency"])

@router.get("/supported")
async def get_supported_currencies_list():
    """Get list of supported currencies"""
    return {
        "currencies": get_supported_currencies(),
        "default": "USD"
    }

@router.get("/rates")
async def get_exchange_rates(base_currency: str = "USD"):
    """Get exchange rates for a base currency"""
    rates = DEFAULT_EXCHANGE_RATES.get(base_currency.upper(), DEFAULT_EXCHANGE_RATES["USD"])
    return {
        "base_currency": base_currency.upper(),
        "rates": rates,
        "date": datetime.now().isoformat(),
    }

@router.get("/convert")
async def convert_amount(
    amount: float,
    from_currency: str,
    to_currency: str
):
    """Convert amount from one currency to another"""
    converted = convert_currency(amount, from_currency.upper(), to_currency.upper())
    return {
        "original_amount": amount,
        "original_currency": from_currency.upper(),
        "converted_amount": round(converted, 2),
        "converted_currency": to_currency.upper(),
        "exchange_rate": DEFAULT_EXCHANGE_RATES.get(
            from_currency.upper(), {}
        ).get(to_currency.upper(), 1.0),
    }

