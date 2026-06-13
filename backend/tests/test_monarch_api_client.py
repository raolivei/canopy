"""Tests for Monarch API spike client."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from backend.services.monarch_api_client import MonarchAPIClient


@pytest.mark.asyncio
async def test_authentication_success():
    """Test successful authentication."""
    client = MonarchAPIClient("test@example.com", "password")

    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "refresh_token": "refresh_token",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        result = await client.authenticate()
        assert result is True
        assert client.access_token == "test_token"
        assert client.refresh_token == "refresh_token"
        assert client.token_expiry is not None

    await client.close()


@pytest.mark.asyncio
async def test_authentication_failure():
    """Test failed authentication."""
    client = MonarchAPIClient("test@example.com", "wrong_password")

    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        mock_post.return_value = mock_response

        result = await client.authenticate()
        assert result is False
        assert client.access_token is None

    await client.close()


@pytest.mark.asyncio
async def test_get_transactions():
    """Test fetching transactions."""
    client = MonarchAPIClient("test@example.com", "password")
    client.access_token = "test_token"

    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactions": [
                {"id": "1", "merchant": "Netflix", "amount": -15.99},
                {"id": "2", "merchant": "Grocery Store", "amount": -52.50}
            ]
        }
        mock_get.return_value = mock_response

        txns = await client.get_transactions(limit=10)
        assert len(txns) == 2
        assert txns[0]["merchant"] == "Netflix"
        assert client.request_count == 1

    await client.close()


@pytest.mark.asyncio
async def test_get_accounts():
    """Test fetching accounts."""
    client = MonarchAPIClient("test@example.com", "password")
    client.access_token = "test_token"

    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accounts": [
                {"id": "acc1", "name": "Checking", "type": "CHECKING", "balance": 5000},
                {"id": "acc2", "name": "Credit Card", "type": "CREDIT_CARD", "balance": -500}
            ]
        }
        mock_get.return_value = mock_response

        accounts = await client.get_accounts()
        assert len(accounts) == 2
        assert accounts[0]["type"] == "CHECKING"

    await client.close()


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test handling of rate limit response."""
    client = MonarchAPIClient("test@example.com", "password")
    client.access_token = "test_token"

    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response

        txns = await client.get_transactions()
        assert len(txns) == 0
        # Rate limiting is handled gracefully

    await client.close()


@pytest.mark.asyncio
async def test_token_refresh():
    """Test token refresh mechanism."""
    client = MonarchAPIClient("test@example.com", "password")
    client.access_token = "old_token"
    client.refresh_token = "refresh_token"
    client.token_expiry = datetime.now() - timedelta(seconds=1)  # Expired

    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        result = await client.refresh_token_if_needed()
        assert result is True
        assert client.access_token == "new_token"

    await client.close()


@pytest.mark.asyncio
async def test_latency_metrics():
    """Test latency metric collection."""
    client = MonarchAPIClient("test@example.com", "password")
    client.access_token = "test_token"

    # Simulate some requests with mock latencies
    client.latency_samples = [0.1, 0.15, 0.12, 0.2, 0.09]
    client.request_count = 5

    metrics = client.get_metrics()
    assert metrics["total_requests"] == 5
    assert 100 < metrics["avg_latency_ms"] < 200  # ~120ms average
    assert metrics["min_latency_ms"] < metrics["avg_latency_ms"]
    assert metrics["max_latency_ms"] > metrics["avg_latency_ms"]

    await client.close()


@pytest.mark.asyncio
async def test_unauthenticated_request():
    """Test that requests fail without authentication."""
    client = MonarchAPIClient("test@example.com", "password")
    # Don't authenticate

    txns = await client.get_transactions()
    assert len(txns) == 0

    await client.close()
