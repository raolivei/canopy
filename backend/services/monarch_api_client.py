"""Spike: Test Monarch Money API integration for viability of live sync."""

import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class MonarchAPIClient:
    """Spike client for testing Monarch Money API integration.

    Goal: Evaluate authentication complexity, rate limits, latency, and reliability
    to determine if live Monarch API sync is viable for production.

    Current approach: CSV imports (working, low maintenance)
    This spike tests: Live API sync (potential future, high maintenance)
    """

    BASE_URL = "https://api.monarchmoney.com"

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.client = httpx.AsyncClient()
        self.request_count = 0
        self.latency_samples = []

    async def authenticate(self) -> bool:
        """Authenticate with Monarch Money API.

        Tests:
        - Email/password authentication
        - Token response format
        - Token refresh mechanism
        """
        try:
            start = datetime.now()

            response = await self.client.post(
                f"{self.BASE_URL}/auth/login",
                json={"email": self.email, "password": self.password}
            )

            latency = (datetime.now() - start).total_seconds()
            self.latency_samples.append(latency)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.token_expiry = datetime.now() + timedelta(
                    seconds=data.get("expires_in", 3600)
                )
                logger.info(f"✅ Authentication successful (latency: {latency:.2f}s)")
                return True
            else:
                logger.error(f"❌ Auth failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Auth exception: {e}")
            return False

    async def get_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch transactions from Monarch API.

        Tests:
        - API endpoint accessibility
        - Response format
        - Data completeness
        - Latency
        """
        if not self.access_token:
            logger.error("Not authenticated")
            return []

        try:
            start = datetime.now()

            response = await self.client.get(
                f"{self.BASE_URL}/transactions",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"limit": limit}
            )

            latency = (datetime.now() - start).total_seconds()
            self.latency_samples.append(latency)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                txns = data.get("transactions", [])
                logger.info(f"✅ Fetched {len(txns)} transactions (latency: {latency:.2f}s)")
                return txns
            elif response.status_code == 429:
                logger.error(f"⚠️  Rate limited: {response.headers.get('Retry-After')}")
                return []
            else:
                logger.error(f"❌ Failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return []

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Fetch accounts from Monarch API.

        Tests:
        - Account types returned
        - Balance/currency info
        - Data structure
        """
        if not self.access_token:
            logger.error("Not authenticated")
            return []

        try:
            start = datetime.now()

            response = await self.client.get(
                f"{self.BASE_URL}/accounts",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            latency = (datetime.now() - start).total_seconds()
            self.latency_samples.append(latency)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                accounts = data.get("accounts", [])
                logger.info(f"✅ Fetched {len(accounts)} accounts (latency: {latency:.2f}s)")
                return accounts
            else:
                logger.error(f"❌ Failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return []

    async def refresh_token_if_needed(self) -> bool:
        """Test token refresh mechanism.

        Tests:
        - Refresh token validity
        - Token rotation
        - Refresh endpoint reliability
        """
        if not self.token_expiry or datetime.now() < self.token_expiry:
            return True  # Token still valid

        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        try:
            start = datetime.now()

            response = await self.client.post(
                f"{self.BASE_URL}/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )

            latency = (datetime.now() - start).total_seconds()
            self.latency_samples.append(latency)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.token_expiry = datetime.now() + timedelta(
                    seconds=data.get("expires_in", 3600)
                )
                logger.info(f"✅ Token refreshed (latency: {latency:.2f}s)")
                return True
            else:
                logger.error(f"❌ Refresh failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Refresh exception: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Return spike test metrics."""
        if not self.latency_samples:
            return {}

        samples = sorted(self.latency_samples)
        return {
            "total_requests": self.request_count,
            "avg_latency_ms": sum(samples) / len(samples) * 1000,
            "p95_latency_ms": samples[int(len(samples) * 0.95)] * 1000 if len(samples) > 1 else 0,
            "p99_latency_ms": samples[int(len(samples) * 0.99)] * 1000 if len(samples) > 1 else 0,
            "min_latency_ms": min(samples) * 1000,
            "max_latency_ms": max(samples) * 1000,
        }

    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()


async def run_spike_test(email: str, password: str):
    """Run complete spike test and report findings."""
    client = MonarchAPIClient(email, password)

    try:
        # Test 1: Authentication
        logger.info("\n=== Test 1: Authentication ===")
        auth_success = await client.authenticate()
        if not auth_success:
            logger.error("Authentication failed, cannot proceed")
            return

        # Test 2: Get accounts
        logger.info("\n=== Test 2: Fetch Accounts ===")
        accounts = await client.get_accounts()
        logger.info(f"Account types: {[a.get('type') for a in accounts]}")

        # Test 3: Get transactions
        logger.info("\n=== Test 3: Fetch Transactions ===")
        txns = await client.get_transactions(limit=10)
        if txns:
            logger.info(f"Sample transaction: {txns[0]}")

        # Test 4: Token refresh
        logger.info("\n=== Test 4: Token Refresh ===")
        refresh_ok = await client.refresh_token_if_needed()
        logger.info(f"Token refresh OK: {refresh_ok}")

        # Report metrics
        logger.info("\n=== Spike Metrics ===")
        metrics = client.get_metrics()
        for key, value in metrics.items():
            logger.info(f"{key}: {value}")

    finally:
        await client.close()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    email = os.getenv("MONARCH_EMAIL")
    password = os.getenv("MONARCH_PASSWORD")

    if not email or not password:
        print("Set MONARCH_EMAIL and MONARCH_PASSWORD environment variables")
        exit(1)

    asyncio.run(run_spike_test(email, password))
