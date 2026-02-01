"""Price fetching service using Yahoo Finance API."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.asset import Asset, AssetType
from backend.db.models.price_history import PriceHistory


logger = logging.getLogger(__name__)


class PriceFetcher:
    """Fetches current and historical prices from Yahoo Finance."""
    
    # Map our asset types to Yahoo Finance symbol suffixes
    CRYPTO_SUFFIX = "-USD"  # BTC -> BTC-USD
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_yf_symbol(self, asset: Asset) -> str:
        """Convert our symbol to Yahoo Finance format."""
        symbol = asset.symbol.upper()
        
        # Crypto needs -USD suffix
        if asset.asset_type == AssetType.CRYPTO and not symbol.endswith("-USD"):
            return f"{symbol}-USD"
        
        return symbol
    
    def fetch_current_price(self, symbol: str) -> Optional[Decimal]:
        """Fetch current price for a symbol from Yahoo Finance.
        
        Args:
            symbol: Stock/ETF ticker (AAPL) or crypto (BTC-USD)
            
        Returns:
            Current price as Decimal, or None if fetch failed
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get the current price from various sources
            info = ticker.info
            
            # Try different price fields (Yahoo Finance is inconsistent)
            price = None
            for field in ['regularMarketPrice', 'currentPrice', 'previousClose', 'open']:
                if field in info and info[field] is not None:
                    price = info[field]
                    break
            
            if price is None:
                # Fallback: get the last close from history
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            if price is not None:
                return Decimal(str(price))
            
            logger.warning(f"Could not fetch price for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def fetch_price_history(
        self, 
        symbol: str, 
        period: str = "1y"
    ) -> list[tuple[datetime, Decimal]]:
        """Fetch historical prices for a symbol.
        
        Args:
            symbol: Stock/ETF ticker or crypto symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            List of (datetime, price) tuples
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No history data for {symbol}")
                return []
            
            return [
                (index.to_pydatetime(), Decimal(str(row['Close'])))
                for index, row in hist.iterrows()
            ]
            
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return []
    
    def update_asset_price(self, asset: Asset) -> bool:
        """Update the current price for an asset.
        
        Fetches the price and updates both the asset's cached price
        and adds a record to price_history.
        
        Returns:
            True if price was updated, False otherwise
        """
        yf_symbol = self._get_yf_symbol(asset)
        price = self.fetch_current_price(yf_symbol)
        
        if price is None:
            return False
        
        # Update asset's cached price
        asset.current_price = price
        asset.price_updated_at = datetime.utcnow()
        
        # Add to price history
        history = PriceHistory(
            asset_id=asset.id,
            price=price,
        )
        self.db.add(history)
        self.db.commit()
        
        logger.info(f"Updated price for {asset.symbol}: {price}")
        return True
    
    def update_all_prices(self) -> dict[str, bool]:
        """Update prices for all tracked assets.
        
        Returns:
            Dict mapping symbol to success status
        """
        assets = self.db.execute(select(Asset)).scalars().all()
        results = {}
        
        for asset in assets:
            results[asset.symbol] = self.update_asset_price(asset)
        
        return results
    
    def get_asset_price_history(
        self, 
        asset_id: int, 
        days: int = 30
    ) -> list[PriceHistory]:
        """Get price history from database for an asset."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        return self.db.execute(
            select(PriceHistory)
            .where(PriceHistory.asset_id == asset_id)
            .where(PriceHistory.fetched_at >= cutoff)
            .order_by(PriceHistory.fetched_at)
        ).scalars().all()


# Standalone function for API use
def fetch_quote(symbol: str) -> Optional[dict]:
    """Fetch a stock/crypto quote without database access.
    
    Returns dict with symbol, price, currency, name, etc.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get price
        price = None
        for field in ['regularMarketPrice', 'currentPrice', 'previousClose']:
            if field in info and info[field]:
                price = info[field]
                break
        
        if price is None:
            return None
        
        return {
            "symbol": symbol,
            "price": Decimal(str(price)),
            "currency": info.get("currency", "USD"),
            "name": info.get("shortName") or info.get("longName", symbol),
            "exchange": info.get("exchange"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
        }
        
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        return None
