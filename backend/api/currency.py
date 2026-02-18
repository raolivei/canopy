from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from datetime import datetime

from backend.services.exchange_rate_service import (
    fetch_latest_rates,
    fetch_historical_rates,
    convert_currency_live,
    get_cache_status,
    get_supported_currencies,
    refresh_all_rates,
    SUPPORTED_CURRENCIES,
)

router = APIRouter(prefix="/v1/currency", tags=["currency"])


@router.get("/supported")
async def get_supported_currencies_list():
    """Get list of supported currencies."""
    return {
        "currencies": get_supported_currencies(),
        "default": "CAD",
        "primary": ["USD", "CAD", "BRL", "EUR", "GBP"],
    }


@router.get("/rates")
async def get_exchange_rates(
    base_currency: str = Query("USD", description="Base currency for rates"),
    background_tasks: BackgroundTasks = None,
):
    """
    Get live exchange rates for a base currency.
    
    Rates are fetched from frankfurter.app (ECB data) and cached for 4 hours.
    """
    rates = await fetch_latest_rates(base_currency.upper())
    cache_status = get_cache_status()
    
    return {
        "base_currency": base_currency.upper(),
        "rates": rates,
        "last_update": cache_status["last_update"],
        "is_live": not cache_status["is_stale"],
        "source": "frankfurter.app (ECB)",
    }


@router.get("/rates/historical")
async def get_historical_rates(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    base_currency: str = Query("USD", description="Base currency for rates"),
):
    """
    Get historical exchange rates for a specific date.
    
    Historical data goes back to 1999 for EUR and varies for other currencies.
    """
    rates = await fetch_historical_rates(date, base_currency.upper())
    
    return {
        "base_currency": base_currency.upper(),
        "date": date,
        "rates": rates,
        "source": "frankfurter.app (ECB)",
    }


@router.get("/convert")
async def convert_amount(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code"),
    date: Optional[str] = Query(None, description="Optional date for historical conversion (YYYY-MM-DD)"),
):
    """
    Convert amount from one currency to another using live rates.
    
    Optionally provide a date for historical conversion.
    """
    converted, rate = await convert_currency_live(
        amount, 
        from_currency.upper(), 
        to_currency.upper(),
        date
    )
    
    return {
        "original_amount": amount,
        "original_currency": from_currency.upper(),
        "converted_amount": round(converted, 2),
        "converted_currency": to_currency.upper(),
        "exchange_rate": round(rate, 6),
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "is_historical": date is not None,
    }


@router.get("/status")
async def get_currency_status():
    """Get the status of the exchange rate cache."""
    return get_cache_status()


@router.post("/refresh")
async def refresh_rates(background_tasks: BackgroundTasks):
    """
    Trigger a refresh of exchange rates.
    
    Rates are refreshed in the background.
    """
    background_tasks.add_task(refresh_all_rates)
    return {
        "message": "Rate refresh initiated",
        "status": "processing",
    }

