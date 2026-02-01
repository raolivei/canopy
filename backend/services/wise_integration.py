"""Wise (TransferWise) API integration service.

Wise provides a free API for personal accounts to access:
- Account balances
- Transaction history
- Transfer details

API Documentation: https://docs.wise.com/api-docs/api-reference
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

import httpx
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class WiseBalance(BaseModel):
    """Balance for a single currency in Wise."""
    currency: str
    amount: Decimal
    reserved: Decimal = Decimal("0")


class WiseTransaction(BaseModel):
    """A transaction from Wise."""
    id: str
    date: datetime
    description: str
    amount: Decimal
    currency: str
    running_balance: Optional[Decimal] = None
    transaction_type: str  # CREDIT, DEBIT, etc.
    reference: Optional[str] = None
    merchant: Optional[str] = None
    category: Optional[str] = None


class WiseProfile(BaseModel):
    """Wise user profile."""
    id: int
    type: str  # personal or business
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class WiseIntegrationService:
    """Service for integrating with Wise API.
    
    Usage:
        1. Get your API token from Wise Settings > API tokens
        2. Create a new token with "Read only" permissions
        3. Pass the token to this service
        
    The token should be stored securely (e.g., in environment variables).
    """
    
    BASE_URL = "https://api.wise.com"
    SANDBOX_URL = "https://api.sandbox.transferwise.tech"
    
    def __init__(self, api_token: str, sandbox: bool = False):
        """Initialize the Wise integration.
        
        Args:
            api_token: Your Wise API token (read-only recommended)
            sandbox: Use sandbox environment for testing
        """
        self.api_token = api_token
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        self._profile_id: Optional[int] = None
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request to the Wise API."""
        url = f"{self.base_url}{endpoint}"
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_profiles(self) -> list[WiseProfile]:
        """Get all profiles (personal and business) for the authenticated user."""
        data = self._get("/v1/profiles")
        return [
            WiseProfile(
                id=p["id"],
                type=p["type"],
                first_name=p.get("details", {}).get("firstName"),
                last_name=p.get("details", {}).get("lastName"),
            )
            for p in data
        ]
    
    def get_personal_profile_id(self) -> int:
        """Get the personal profile ID (cached after first call)."""
        if self._profile_id is None:
            profiles = self.get_profiles()
            personal = next((p for p in profiles if p.type == "personal"), None)
            if not personal:
                raise ValueError("No personal profile found")
            self._profile_id = personal.id
        return self._profile_id
    
    def get_balances(self, profile_id: Optional[int] = None) -> list[WiseBalance]:
        """Get all currency balances for the profile."""
        profile_id = profile_id or self.get_personal_profile_id()
        data = self._get(f"/v4/profiles/{profile_id}/balances?types=STANDARD")
        
        balances = []
        for balance in data:
            balances.append(WiseBalance(
                currency=balance["currency"],
                amount=Decimal(str(balance["amount"]["value"])),
                reserved=Decimal(str(balance.get("reservedAmount", {}).get("value", 0))),
            ))
        return balances
    
    def get_transactions(
        self,
        currency: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        profile_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[WiseTransaction]:
        """Get transactions for a specific currency.
        
        Args:
            currency: Currency code (e.g., "USD", "CAD", "BRL")
            start_date: Start of date range (defaults to 90 days ago)
            end_date: End of date range (defaults to now)
            profile_id: Profile ID (defaults to personal profile)
            limit: Maximum number of transactions to return
        """
        profile_id = profile_id or self.get_personal_profile_id()
        
        # Default date range
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=90)
        
        # First, get the balance account ID for this currency
        balances_data = self._get(f"/v4/profiles/{profile_id}/balances?types=STANDARD")
        balance_account = next(
            (b for b in balances_data if b["currency"] == currency.upper()),
            None
        )
        
        if not balance_account:
            logger.warning(f"No balance account found for currency {currency}")
            return []
        
        balance_id = balance_account["id"]
        
        # Get transactions for this balance
        params = {
            "currency": currency.upper(),
            "intervalStart": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "intervalEnd": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": limit,
        }
        
        data = self._get(
            f"/v3/profiles/{profile_id}/borderless-accounts/{balance_id}/statement.json",
            params=params
        )
        
        transactions = []
        for tx in data.get("transactions", []):
            # Parse date
            date_str = tx.get("date", "")
            try:
                tx_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except:
                tx_date = datetime.utcnow()
            
            # Determine type
            amount_data = tx.get("amount", {})
            amount = Decimal(str(amount_data.get("value", 0)))
            tx_type = "CREDIT" if amount > 0 else "DEBIT"
            
            # Get running balance
            running_balance = None
            if "runningBalance" in tx:
                running_balance = Decimal(str(tx["runningBalance"]["value"]))
            
            # Get merchant/reference info
            details = tx.get("details", {})
            merchant = details.get("merchant", {}).get("name")
            reference = details.get("paymentReference") or tx.get("referenceNumber")
            
            transactions.append(WiseTransaction(
                id=str(tx.get("referenceNumber", tx.get("id", ""))),
                date=tx_date,
                description=details.get("description", tx.get("details", {}).get("type", "Transaction")),
                amount=amount,
                currency=amount_data.get("currency", currency),
                running_balance=running_balance,
                transaction_type=tx_type,
                reference=reference,
                merchant=merchant,
                category=details.get("category"),
            ))
        
        return transactions
    
    def get_all_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        profile_id: Optional[int] = None,
    ) -> list[WiseTransaction]:
        """Get transactions across all currencies.
        
        Fetches balances first, then gets transactions for each currency.
        """
        profile_id = profile_id or self.get_personal_profile_id()
        balances = self.get_balances(profile_id)
        
        all_transactions = []
        for balance in balances:
            if balance.amount != 0 or True:  # Get transactions even for zero balances
                try:
                    txs = self.get_transactions(
                        currency=balance.currency,
                        start_date=start_date,
                        end_date=end_date,
                        profile_id=profile_id,
                    )
                    all_transactions.extend(txs)
                except Exception as e:
                    logger.error(f"Error fetching {balance.currency} transactions: {e}")
        
        # Sort by date descending
        all_transactions.sort(key=lambda x: x.date, reverse=True)
        return all_transactions
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for one-off use
def fetch_wise_transactions(
    api_token: str,
    currency: Optional[str] = None,
    days: int = 90,
    sandbox: bool = False,
) -> list[WiseTransaction]:
    """Fetch Wise transactions with a simple interface.
    
    Args:
        api_token: Wise API token
        currency: Specific currency to fetch (None for all)
        days: Number of days of history to fetch
        sandbox: Use sandbox environment
        
    Returns:
        List of WiseTransaction objects
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    with WiseIntegrationService(api_token, sandbox=sandbox) as wise:
        if currency:
            return wise.get_transactions(
                currency=currency,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            return wise.get_all_transactions(
                start_date=start_date,
                end_date=end_date,
            )
