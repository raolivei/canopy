"""Moomoo (Futu) API integration service.

Moomoo/Futu uses a local gateway (OpenD) that connects to Futu servers.
The user must:
1. Download and install OpenD from https://openapi.futunn.com/
2. Configure RSA key authentication
3. Run OpenD locally (default: localhost:11111)

This service connects to the local OpenD gateway via TCP using futu-api.

API Documentation: https://openapi.futunn.com/futu-api-doc/
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Default OpenD gateway settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 11111


class MoomooMarket(str, Enum):
    """Supported markets."""
    US = "US"  # US stocks
    HK = "HK"  # Hong Kong stocks
    CN = "CN"  # China A-shares (via HK Connect)
    SG = "SG"  # Singapore
    JP = "JP"  # Japan


class MoomooAccountType(str, Enum):
    """Account types."""
    CASH = "CASH"
    MARGIN = "MARGIN"


@dataclass
class MoomooAccount:
    """A Moomoo trading account."""
    acc_id: int
    acc_type: str
    card_num: str
    currency: str
    market: str
    status: str


@dataclass
class MoomooPosition:
    """A position (holding) in a Moomoo account."""
    code: str
    name: str
    quantity: Decimal
    cost_price: Optional[Decimal]
    current_price: Optional[Decimal]
    market_value: Optional[Decimal]
    profit_loss: Optional[Decimal]
    profit_loss_pct: Optional[Decimal]
    currency: str
    market: str


@dataclass
class MoomooBalance:
    """Balance summary for an account."""
    currency: str
    cash: Decimal
    frozen_cash: Decimal
    market_value: Decimal
    total_assets: Decimal
    available_funds: Decimal


@dataclass
class MoomooQuote:
    """Market quote for a security."""
    code: str
    name: str
    last_price: Decimal
    open_price: Optional[Decimal]
    high_price: Optional[Decimal]
    low_price: Optional[Decimal]
    prev_close: Optional[Decimal]
    volume: int
    turnover: Decimal
    change_val: Optional[Decimal]
    change_pct: Optional[Decimal]
    update_time: str


class MoomooConnectionError(Exception):
    """Raised when connection to OpenD fails."""
    pass


class MoomooAuthError(Exception):
    """Raised when authentication fails."""
    pass


class MoomooIntegrationService:
    """Service for integrating with Moomoo/Futu via local OpenD gateway.

    Usage:
        1. User installs and runs OpenD locally
        2. User configures RSA key (optional but recommended for security)
        3. Pass host/port (and optionally rsa_path) to constructor
        4. Call connect(), then use API methods
        5. Call close() when done

    Example:
        with MoomooIntegrationService() as moomoo:
            if moomoo.connect():
                accounts = moomoo.get_accounts()
                for acc in accounts:
                    positions = moomoo.get_positions(acc.acc_id)
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        rsa_path: Optional[str] = None,
        password_md5: Optional[str] = None,
    ):
        """Initialize the Moomoo integration service.
        
        Args:
            host: OpenD gateway host (default: 127.0.0.1)
            port: OpenD gateway port (default: 11111)
            rsa_path: Path to RSA private key file for authentication
            password_md5: MD5 hash of trading password (for trade operations)
        """
        self.host = host
        self.port = port
        self.rsa_path = rsa_path
        self.password_md5 = password_md5
        self._quote_ctx = None
        self._trade_ctx = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to the OpenD gateway.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            from futu import OpenQuoteContext, OpenSecTradeContext, TrdEnv, TrdMarket
            
            # Initialize quote context for market data
            self._quote_ctx = OpenQuoteContext(
                host=self.host,
                port=self.port,
            )
            
            # Test connection
            ret, data = self._quote_ctx.get_global_state()
            if ret != 0:
                logger.error(f"Failed to connect to OpenD: {data}")
                return False
            
            logger.info(f"Connected to Moomoo OpenD gateway at {self.host}:{self.port}")
            self._connected = True
            return True
            
        except ImportError:
            logger.error("futu-api package not installed. Run: pip install futu-api")
            raise MoomooConnectionError("futu-api package not installed")
        except Exception as e:
            logger.error(f"Failed to connect to OpenD: {e}")
            raise MoomooConnectionError(f"Connection failed: {e}")

    def _get_trade_context(self, market: str = "US"):
        """Get or create a trade context for the specified market."""
        if self._trade_ctx is None:
            from futu import OpenSecTradeContext, TrdEnv, TrdMarket
            
            # Map market string to TrdMarket
            market_map = {
                "US": TrdMarket.US,
                "HK": TrdMarket.HK,
                "CN": TrdMarket.HKCC,  # China via HK Connect
                "SG": TrdMarket.SG,
                "JP": TrdMarket.JP,
            }
            trd_market = market_map.get(market, TrdMarket.US)
            
            self._trade_ctx = OpenSecTradeContext(
                host=self.host,
                port=self.port,
                security_firm=None,  # Auto-detect
            )
        
        return self._trade_ctx

    def get_connection_status(self) -> dict:
        """Get the current connection status and server info."""
        if not self._quote_ctx:
            return {
                "connected": False,
                "error": "Not connected",
            }
        
        try:
            ret, data = self._quote_ctx.get_global_state()
            if ret != 0:
                return {
                    "connected": False,
                    "error": str(data),
                }
            
            return {
                "connected": True,
                "market_hk": data.get("market_hk", "UNKNOWN"),
                "market_us": data.get("market_us", "UNKNOWN"),
                "market_sh": data.get("market_sh", "UNKNOWN"),
                "market_sz": data.get("market_sz", "UNKNOWN"),
                "server_ver": data.get("server_ver", "UNKNOWN"),
                "quote_rights": data.get("qot_rights", []),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }

    def get_accounts(self) -> list[MoomooAccount]:
        """Fetch all trading accounts."""
        if not self._connected:
            raise MoomooConnectionError("Not connected to OpenD")
        
        try:
            trade_ctx = self._get_trade_context()
            ret, data = trade_ctx.get_acc_list()
            
            if ret != 0:
                logger.error(f"Failed to get accounts: {data}")
                return []
            
            accounts = []
            for _, row in data.iterrows():
                accounts.append(MoomooAccount(
                    acc_id=row["acc_id"],
                    acc_type=row.get("acc_type", ""),
                    card_num=row.get("card_num", ""),
                    currency=row.get("currency", "USD"),
                    market=row.get("trd_market", ""),
                    status=row.get("acc_status", ""),
                ))
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            raise

    def get_positions(self, acc_id: int, market: str = "US") -> list[MoomooPosition]:
        """Fetch positions for an account.
        
        Args:
            acc_id: Account ID
            market: Market code (US, HK, CN, SG, JP)
        """
        if not self._connected:
            raise MoomooConnectionError("Not connected to OpenD")
        
        try:
            from futu import TrdEnv, TrdMarket
            
            trade_ctx = self._get_trade_context(market)
            
            # Map market string to TrdMarket
            market_map = {
                "US": TrdMarket.US,
                "HK": TrdMarket.HK,
                "CN": TrdMarket.HKCC,
                "SG": TrdMarket.SG,
                "JP": TrdMarket.JP,
            }
            trd_market = market_map.get(market, TrdMarket.US)
            
            ret, data = trade_ctx.position_list_query(
                acc_id=acc_id,
                trd_market=trd_market,
                trd_env=TrdEnv.REAL,  # Real trading environment
            )
            
            if ret != 0:
                logger.error(f"Failed to get positions: {data}")
                return []
            
            positions = []
            for _, row in data.iterrows():
                qty = Decimal(str(row.get("qty", 0)))
                if qty <= 0:
                    continue
                    
                positions.append(MoomooPosition(
                    code=row.get("code", ""),
                    name=row.get("stock_name", ""),
                    quantity=qty,
                    cost_price=Decimal(str(row["cost_price"])) if row.get("cost_price") else None,
                    current_price=Decimal(str(row["nominal_price"])) if row.get("nominal_price") else None,
                    market_value=Decimal(str(row["market_val"])) if row.get("market_val") else None,
                    profit_loss=Decimal(str(row["pl_val"])) if row.get("pl_val") else None,
                    profit_loss_pct=Decimal(str(row["pl_ratio"])) if row.get("pl_ratio") else None,
                    currency=row.get("currency", "USD"),
                    market=market,
                ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise

    def get_balances(self, acc_id: int, market: str = "US") -> list[MoomooBalance]:
        """Fetch account balances.
        
        Args:
            acc_id: Account ID
            market: Market code (US, HK, CN, SG, JP)
        """
        if not self._connected:
            raise MoomooConnectionError("Not connected to OpenD")
        
        try:
            from futu import TrdEnv, TrdMarket
            
            trade_ctx = self._get_trade_context(market)
            
            market_map = {
                "US": TrdMarket.US,
                "HK": TrdMarket.HK,
                "CN": TrdMarket.HKCC,
                "SG": TrdMarket.SG,
                "JP": TrdMarket.JP,
            }
            trd_market = market_map.get(market, TrdMarket.US)
            
            ret, data = trade_ctx.accinfo_query(
                acc_id=acc_id,
                trd_market=trd_market,
                trd_env=TrdEnv.REAL,
            )
            
            if ret != 0:
                logger.error(f"Failed to get balances: {data}")
                return []
            
            balances = []
            for _, row in data.iterrows():
                balances.append(MoomooBalance(
                    currency=row.get("currency", "USD"),
                    cash=Decimal(str(row.get("cash", 0))),
                    frozen_cash=Decimal(str(row.get("frozen_cash", 0))),
                    market_value=Decimal(str(row.get("market_val", 0))),
                    total_assets=Decimal(str(row.get("total_assets", 0))),
                    available_funds=Decimal(str(row.get("avl_withdrawal_cash", 0))),
                ))
            
            return balances
            
        except Exception as e:
            logger.error(f"Error fetching balances: {e}")
            raise

    def get_quote(self, codes: list[str]) -> list[MoomooQuote]:
        """Get real-time quotes for securities.
        
        Args:
            codes: List of security codes (e.g., ["US.AAPL", "HK.00700"])
        """
        if not self._quote_ctx:
            raise MoomooConnectionError("Not connected to OpenD")
        
        try:
            ret, data = self._quote_ctx.get_market_snapshot(codes)
            
            if ret != 0:
                logger.error(f"Failed to get quotes: {data}")
                return []
            
            quotes = []
            for _, row in data.iterrows():
                quotes.append(MoomooQuote(
                    code=row.get("code", ""),
                    name=row.get("name", ""),
                    last_price=Decimal(str(row.get("last_price", 0))),
                    open_price=Decimal(str(row["open_price"])) if row.get("open_price") else None,
                    high_price=Decimal(str(row["high_price"])) if row.get("high_price") else None,
                    low_price=Decimal(str(row["low_price"])) if row.get("low_price") else None,
                    prev_close=Decimal(str(row["prev_close_price"])) if row.get("prev_close_price") else None,
                    volume=int(row.get("volume", 0)),
                    turnover=Decimal(str(row.get("turnover", 0))),
                    change_val=Decimal(str(row["price_spread"])) if row.get("price_spread") else None,
                    change_pct=Decimal(str(row["change_rate"])) if row.get("change_rate") else None,
                    update_time=str(row.get("update_time", "")),
                ))
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            raise

    def search_stocks(self, keyword: str, market: str = "US") -> list[dict]:
        """Search for stocks by keyword.
        
        Args:
            keyword: Search keyword (ticker symbol or company name)
            market: Market to search (US, HK, CN, SG, JP)
        """
        if not self._quote_ctx:
            raise MoomooConnectionError("Not connected to OpenD")
        
        try:
            from futu import Market
            
            market_map = {
                "US": Market.US,
                "HK": Market.HK,
                "CN": Market.SH,  # Shanghai
                "SG": Market.SG,
                "JP": Market.JP,
            }
            mkt = market_map.get(market, Market.US)
            
            ret, data = self._quote_ctx.get_stock_basicinfo(mkt, code_list=[])
            
            if ret != 0:
                return []
            
            # Filter by keyword
            results = []
            keyword_lower = keyword.lower()
            for _, row in data.iterrows():
                code = row.get("code", "")
                name = row.get("name", "")
                if keyword_lower in code.lower() or keyword_lower in name.lower():
                    results.append({
                        "code": code,
                        "name": name,
                        "lot_size": row.get("lot_size", 1),
                        "stock_type": row.get("stock_type", ""),
                    })
                    if len(results) >= 20:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []

    def close(self) -> None:
        """Close all connections to OpenD."""
        if self._quote_ctx:
            try:
                self._quote_ctx.close()
            except Exception:
                pass
            self._quote_ctx = None
        
        if self._trade_ctx:
            try:
                self._trade_ctx.close()
            except Exception:
                pass
            self._trade_ctx = None
        
        self._connected = False
        logger.info("Closed Moomoo OpenD connections")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
