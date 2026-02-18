"""
Exchange Rate Service - Fetches real-time rates from frankfurter.app

Frankfurter is a free, open-source API that provides exchange rates 
published by the European Central Bank.
"""

import httpx
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL_HOURS = 4
FRANKFURTER_BASE_URL = "https://api.frankfurter.app"

# Supported currencies (frankfurter supports ~30+ currencies)
SUPPORTED_CURRENCIES = [
    "USD", "CAD", "BRL", "EUR", "GBP", "JPY", "AUD", "CHF", 
    "CNY", "HKD", "INR", "MXN", "NOK", "NZD", "SEK", "SGD"
]


class ExchangeRateCache:
    """Simple in-memory cache for exchange rates."""
    
    def __init__(self):
        self._rates: dict[str, dict[str, float]] = {}
        self._last_update: Optional[datetime] = None
        self._historical_cache: dict[str, dict[str, dict[str, float]]] = {}
    
    @property
    def is_stale(self) -> bool:
        """Check if cache needs refresh."""
        if self._last_update is None:
            return True
        return datetime.now() - self._last_update > timedelta(hours=CACHE_TTL_HOURS)
    
    @property
    def last_update(self) -> Optional[datetime]:
        return self._last_update
    
    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get cached rate if available."""
        if from_currency in self._rates:
            return self._rates[from_currency].get(to_currency)
        return None
    
    def get_rates(self, base_currency: str) -> Optional[dict[str, float]]:
        """Get all rates for a base currency."""
        return self._rates.get(base_currency)
    
    def set_rates(self, base_currency: str, rates: dict[str, float]):
        """Cache rates for a base currency."""
        self._rates[base_currency] = rates
        self._last_update = datetime.now()
    
    def get_historical_rate(self, date: str, from_currency: str, to_currency: str) -> Optional[float]:
        """Get historical rate if cached."""
        if date in self._historical_cache:
            if from_currency in self._historical_cache[date]:
                return self._historical_cache[date][from_currency].get(to_currency)
        return None
    
    def set_historical_rates(self, date: str, base_currency: str, rates: dict[str, float]):
        """Cache historical rates."""
        if date not in self._historical_cache:
            self._historical_cache[date] = {}
        self._historical_cache[date][base_currency] = rates


# Global cache instance
_cache = ExchangeRateCache()


async def fetch_latest_rates(base_currency: str = "USD") -> dict[str, float]:
    """
    Fetch latest exchange rates from frankfurter.app.
    
    Args:
        base_currency: Base currency for rates (default USD)
        
    Returns:
        Dictionary of currency codes to exchange rates
    """
    base = base_currency.upper()
    
    # Check cache first
    if not _cache.is_stale:
        cached = _cache.get_rates(base)
        if cached:
            logger.debug(f"Using cached rates for {base}")
            return cached
    
    # Fetch from API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get rates for supported currencies
            symbols = ",".join([c for c in SUPPORTED_CURRENCIES if c != base])
            url = f"{FRANKFURTER_BASE_URL}/latest?from={base}&to={symbols}"
            
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get("rates", {})
            
            # Add the base currency itself (rate = 1.0)
            rates[base] = 1.0
            
            # Cache the rates
            _cache.set_rates(base, rates)
            logger.info(f"Fetched and cached latest rates for {base}: {len(rates)} currencies")
            
            return rates
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch rates from frankfurter.app: {e}")
        # Return cached rates if available, even if stale
        cached = _cache.get_rates(base)
        if cached:
            logger.warning(f"Using stale cached rates for {base}")
            return cached
        # Fall back to static rates as last resort
        return _get_fallback_rates(base)
    except Exception as e:
        logger.error(f"Unexpected error fetching rates: {e}")
        return _get_fallback_rates(base)


async def fetch_historical_rates(date: str, base_currency: str = "USD") -> dict[str, float]:
    """
    Fetch historical exchange rates for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        base_currency: Base currency for rates
        
    Returns:
        Dictionary of currency codes to exchange rates
    """
    base = base_currency.upper()
    
    # Check cache first
    cached = _cache.get_historical_rate(date, base, base)
    if cached:
        return _cache._historical_cache[date][base]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            symbols = ",".join([c for c in SUPPORTED_CURRENCIES if c != base])
            url = f"{FRANKFURTER_BASE_URL}/{date}?from={base}&to={symbols}"
            
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get("rates", {})
            rates[base] = 1.0
            
            # Cache historical rates
            _cache.set_historical_rates(date, base, rates)
            logger.info(f"Fetched historical rates for {base} on {date}")
            
            return rates
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch historical rates: {e}")
        # Fall back to latest rates
        return await fetch_latest_rates(base)
    except Exception as e:
        logger.error(f"Unexpected error fetching historical rates: {e}")
        return await fetch_latest_rates(base)


async def convert_currency_live(
    amount: float, 
    from_currency: str, 
    to_currency: str,
    date: Optional[str] = None
) -> tuple[float, float]:
    """
    Convert currency using live rates.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        date: Optional date for historical conversion (YYYY-MM-DD)
        
    Returns:
        Tuple of (converted_amount, exchange_rate)
    """
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    if from_curr == to_curr:
        return amount, 1.0
    
    # Get rates
    if date:
        rates = await fetch_historical_rates(date, from_curr)
    else:
        rates = await fetch_latest_rates(from_curr)
    
    rate = rates.get(to_curr, 1.0)
    converted = amount * rate
    
    return converted, rate


def convert_currency_sync(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Synchronous currency conversion using cached rates.
    Falls back to static rates if cache is empty.
    """
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    if from_curr == to_curr:
        return amount
    
    # Try cache first
    cached_rates = _cache.get_rates(from_curr)
    if cached_rates and to_curr in cached_rates:
        return amount * cached_rates[to_curr]
    
    # Fall back to static rates
    fallback = _get_fallback_rates(from_curr)
    return amount * fallback.get(to_curr, 1.0)


def get_cache_status() -> dict:
    """Get current cache status."""
    return {
        "last_update": _cache.last_update.isoformat() if _cache.last_update else None,
        "is_stale": _cache.is_stale,
        "cache_ttl_hours": CACHE_TTL_HOURS,
        "cached_currencies": list(_cache._rates.keys()),
        "historical_dates_cached": list(_cache._historical_cache.keys()),
    }


def get_supported_currencies() -> list[str]:
    """Get list of supported currencies."""
    return SUPPORTED_CURRENCIES.copy()


def _get_fallback_rates(base_currency: str) -> dict[str, float]:
    """Static fallback rates when API is unavailable."""
    FALLBACK_RATES = {
        "USD": {"USD": 1.0, "CAD": 1.36, "BRL": 5.05, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5},
        "CAD": {"USD": 0.74, "CAD": 1.0, "BRL": 3.72, "EUR": 0.68, "GBP": 0.58, "JPY": 110.0},
        "BRL": {"USD": 0.20, "CAD": 0.27, "BRL": 1.0, "EUR": 0.18, "GBP": 0.16, "JPY": 29.6},
        "EUR": {"USD": 1.09, "CAD": 1.48, "BRL": 5.50, "EUR": 1.0, "GBP": 0.86, "JPY": 163.0},
        "GBP": {"USD": 1.27, "CAD": 1.72, "BRL": 6.40, "EUR": 1.16, "GBP": 1.0, "JPY": 189.0},
    }
    return FALLBACK_RATES.get(base_currency, {"USD": 1.0, base_currency: 1.0})


async def refresh_all_rates():
    """Background task to refresh rates for all base currencies."""
    for currency in ["USD", "CAD", "EUR", "GBP", "BRL"]:
        try:
            await fetch_latest_rates(currency)
            await asyncio.sleep(0.5)  # Rate limit
        except Exception as e:
            logger.error(f"Failed to refresh rates for {currency}: {e}")
