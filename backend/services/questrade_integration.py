"""Questrade API integration service.

Questrade uses OAuth 2.0 refresh token flow. User obtains a refresh token from
https://my.questrade.com/APIAccess and passes it here. We exchange it for an
access token (valid 30 min) and use the returned api_server URL for all API calls.

API Documentation: https://www.questrade.com/api/documentation
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TOKEN_URL = "https://login.questrade.com/oauth2/token"


@dataclass
class QuestradeAccount:
    """A Questrade account (TFSA, RRSP, Margin, etc.)."""
    number: str
    type: str
    status: str
    is_primary: bool
    is_billing: bool
    client_account_type: str


@dataclass
class QuestradePosition:
    """A position (holding) in a Questrade account."""
    symbol_id: int
    symbol: str
    open_quantity: Decimal
    current_market_value: Optional[Decimal]
    current_price: Optional[Decimal]
    average_entry_price: Optional[Decimal]
    open_pnl: Optional[Decimal]
    closed_pnl: Optional[Decimal]


@dataclass
class QuestradeBalance:
    """Balance summary for an account."""
    currency: str
    cash: Decimal
    market_value: Decimal
    total_equity: Decimal
    buying_power: Optional[Decimal]
    maintenance_excess: Optional[Decimal]


class QuestradeIntegrationService:
    """Service for integrating with Questrade API.

    Usage:
        1. User registers at https://my.questrade.com/APIAccess
        2. User copies the refresh token (and optionally client ID)
        3. Pass refresh_token to constructor; call get_access_token() then API methods
    """

    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token.strip()
        self._access_token: Optional[str] = None
        self._api_server: Optional[str] = None
        self._expires_at: Optional[float] = None
        self._client: Optional[httpx.Client] = None

    def _ensure_token(self) -> None:
        """Refresh access token if expired or missing."""
        import time
        if (
            self._access_token
            and self._api_server
            and self._expires_at
            and time.time() < self._expires_at - 60
        ):
            return
        self._refresh_token()

    def _refresh_token(self) -> None:
        """Exchange refresh token for access token and api_server URL."""
        import time
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._api_server = data["api_server"].rstrip("/")
        expires_in = int(data.get("expires_in", 1800))
        self._expires_at = time.time() + expires_in
        if "refresh_token" in data:
            self.refresh_token = data["refresh_token"]
            logger.info("Questrade: stored new refresh token for next use")
        if self._client:
            self._client.close()
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """GET from Questrade API (path like 'accounts' or 'accounts/123/positions')."""
        self._ensure_token()
        path = path.strip("/")
        url = f"{self._api_server}/v1/{path}"
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_accounts(self) -> list[QuestradeAccount]:
        """Fetch all accounts for the authenticated user."""
        data = self._get("accounts")
        return [
            QuestradeAccount(
                number=str(acc["number"]),
                type=acc.get("type", ""),
                status=acc.get("status", ""),
                is_primary=acc.get("isPrimary", False),
                is_billing=acc.get("isBilling", False),
                client_account_type=acc.get("clientAccountType", ""),
            )
            for acc in data.get("accounts", [])
        ]

    def get_positions(self, account_number: str) -> list[QuestradePosition]:
        """Fetch positions for an account."""
        data = self._get(f"accounts/{account_number}/positions")
        positions = []
        for p in data.get("positions", []):
            open_qty = Decimal(str(p.get("openQuantity", 0)))
            if open_qty <= 0:
                continue
            positions.append(QuestradePosition(
                symbol_id=p.get("symbolId", 0),
                symbol=p.get("symbol", ""),
                open_quantity=open_qty,
                current_market_value=(
                    Decimal(str(p["currentMarketValue"])) if p.get("currentMarketValue") is not None else None
                ),
                current_price=(
                    Decimal(str(p["currentPrice"])) if p.get("currentPrice") is not None else None
                ),
                average_entry_price=(
                    Decimal(str(p["averageEntryPrice"])) if p.get("averageEntryPrice") is not None else None
                ),
                open_pnl=(
                    Decimal(str(p["openPnl"])) if p.get("openPnl") is not None else None
                ),
                closed_pnl=(
                    Decimal(str(p["closedPnl"])) if p.get("closedPnl") is not None else None
                ),
            ))
        return positions

    def get_balances(self, account_number: str) -> list[QuestradeBalance]:
        """Fetch balances for an account."""
        data = self._get(f"accounts/{account_number}/balances")
        balances = []
        for b in data.get("perCurrencyBalances", []) or []:
            balances.append(QuestradeBalance(
                currency=b.get("currency", "CAD"),
                cash=Decimal(str(b.get("cash", 0))),
                market_value=Decimal(str(b.get("marketValue", 0))),
                total_equity=Decimal(str(b.get("totalEquity", 0))),
                buying_power=(
                    Decimal(str(b["buyingPower"])) if b.get("buyingPower") is not None else None
                ),
                maintenance_excess=(
                    Decimal(str(b["maintenanceExcess"])) if b.get("maintenanceExcess") is not None else None
                ),
            ))
        return balances

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
