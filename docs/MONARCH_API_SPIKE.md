# Monarch Money API Spike - Viability Assessment

**Date:** 2026-06-12  
**Purpose:** Evaluate if live Monarch API sync is viable for production  
**Current approach:** CSV imports (working, low maintenance)  
**Tested approach:** Live API sync (potential future, high maintenance)

## Executive Summary

This spike tests the feasibility of implementing live Monarch Money API integration for scheduled transaction/balance syncing. **Recommendation pending actual API testing with credentials.**

### Key Questions
1. How complex is Monarch authentication?
2. What are the rate limits?
3. How stable is the API (latency, errors)?
4. Is the maintenance burden acceptable?
5. **Decision:** Yes (implement live sync) or No (keep CSV-only at cutover)?

## Context

**Canopy's Monarch Parity Plan:**
- **Learn phase (2026):** Use CSV imports + Monarch MCP to understand features
- **Parallel phase (2026-2027):** Both Canopy + Monarch active
- **Cutover (2027):** Cancel Monarch, keep all data in Canopy
- **After cutover:** No Monarch MCP in routine workflow

**CSV import is production-ready.** This spike tests whether a scheduled live sync job would be better than manual monthly CSV exports.

## Spike Implementation

### Monarch API Client (`backend/services/monarch_api_client.py`)

Created a spike client that tests:

1. **Authentication**
   ```python
   client = MonarchAPIClient(email, password)
   await client.authenticate()
   ```
   Tests email/password login, token response, token storage.

2. **Data Fetching**
   ```python
   transactions = await client.get_transactions(limit=50)
   accounts = await client.get_accounts()
   ```
   Tests API endpoints, response format, data completeness.

3. **Rate Limiting**
   Handles 429 responses gracefully, respects `Retry-After` header.

4. **Token Refresh**
   ```python
   await client.refresh_token_if_needed()
   ```
   Tests token expiration, refresh flow, token rotation.

5. **Latency Tracking**
   Measures response times, calculates avg/p95/p99 latencies.

### Test Suite (`backend/tests/test_monarch_api_client.py`)

- `test_authentication_success/failure` - Auth flow
- `test_get_transactions/accounts` - Data fetching
- `test_rate_limiting` - 429 handling
- `test_token_refresh` - Token rotation
- `test_latency_metrics` - Performance tracking
- `test_unauthenticated_request` - Security (requests fail without token)

## How to Run the Spike

### Prerequisites
```bash
# Install dependencies (if not already installed)
pip install httpx pytest-asyncio

# Set environment variables with your Monarch credentials
export MONARCH_EMAIL="your@email.com"
export MONARCH_PASSWORD="your_password"
```

### Run Tests (Mocked)
```bash
cd /Users/roliveira/WORKSPACE/raolivei/canopy
docker-compose exec api pytest backend/tests/test_monarch_api_client.py -v
```

### Run Against Live API (Optional)
```bash
docker-compose exec api python -c "
import asyncio
import os
from backend.services.monarch_api_client import run_spike_test

asyncio.run(run_spike_test(
    os.getenv('MONARCH_EMAIL'),
    os.getenv('MONARCH_PASSWORD')
))
"
```

## Findings (Template - Fill After Testing)

### Authentication Complexity
- **Rating:** 1-10 (1 = simple, 10 = complex)
- **Findings:** [Test results here]
- **Risk:** [High/Medium/Low]

### Rate Limits
- **Requests/min:** [TBD]
- **Daily quotas:** [TBD]
- **Concerns:** [TBD]

### Latency
- **Average:** [TBD ms]
- **P95:** [TBD ms]
- **P99:** [TBD ms]
- **Assessment:** [Acceptable/Concerning]

### Token Refresh
- **Mechanism:** [OAuth2/custom/other]
- **Stability:** [Reliable/Unreliable]
- **Concerns:** [TBD]

### API Reliability
- **Uptime estimate:** [TBD]
- **Error patterns:** [TBD]
- **Timeout behavior:** [TBD]

### Maintenance Burden
- **Complexity:** 1-10 (1 = trivial, 10 = nightmare)
- **Estimated effort:** [Low/Medium/High]
- **Ongoing ops:** [TBD]

## Recommendation

**Based on testing results:**

### YES - Implement Live Sync If:
- ✅ Authentication is simple (< 5/10)
- ✅ Rate limits are generous (> 100 req/min)
- ✅ Latency acceptable (< 500ms avg)
- ✅ Token refresh is reliable
- ✅ API stability high (< 1% error rate)
- ✅ Maintenance burden is acceptable

### NO - Keep CSV-Only If:
- ❌ Authentication is complex (> 6/10)
- ❌ Rate limits restrictive (< 50 req/min)
- ❌ Latency high (> 1000ms avg)
- ❌ Token refresh unreliable
- ❌ API frequently errors or timeouts
- ❌ Maintenance burden too high

## Next Steps

1. **Run spike with live Monarch credentials**
   - Fill in findings above
   - Document any surprises

2. **Decision point:**
   - If YES: Create P1 issue for scheduled sync job
   - If NO: Document CSV-only approach as final plan

3. **Integration (if approved):**
   - Implement `MonarchSyncJob` in `backend/tasks/`
   - Celery task: run every 6 hours
   - Dedup transactions, update balances
   - Error handling, logging, monitoring

4. **Testing:**
   - Integration tests with sandbox Monarch account
   - Test sync reliability over 1-2 weeks
   - Verify deduplication (don't create duplicates on re-import)
   - Test error recovery (network failure, token expiration)

## Related Code

- CSV importer (current): `backend/services/monarch/`
- Spike client (new): `backend/services/monarch_api_client.py`
- Tests: `backend/tests/test_monarch_api_client.py`

## References

- [Monarch Money MCP](https://github.com/monarch-money/monarch-money-mcp) - Reference for API patterns
- [Canopy CLAUDE.md](../CLAUDE.md) - Main development guide
- [Monarch Parity Memory](../ollie/memory/project_canopy_monarch_parity.md) - Strategy doc

---

**Status:** Spike created, awaiting credential testing  
**Owner:** Canopy team  
**Timeline:** Complete by 2026-06-15 to unblock P1 feature prioritization
