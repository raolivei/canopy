# Performance Audit - Canopy Backend

**Date**: 2026-06-15  
**Auditor**: Claude Opus 4.8  
**Scope**: Backend services, database queries, memory usage

## 🚨 Critical Issues

### 1. Unbounded Query Results (P0 - Critical)

**Location**: `backend/services/assistant_service.py`  
**Issue**: 9 instances of `.scalars().all()` without LIMIT clauses

```python
# Line 335, 358, 382, 534, 561, 605, 697, 716, 757
transactions = self.db.execute(query).scalars().all()  # ⚠️ No LIMIT!
```

**Risk**: 
- With 100K+ transactions, loads entire table into memory (~500MB+)
- OOM kills on Raspberry Pi (8GB total, shared with other pods)
- API timeout (>30s response time)
- Database connection exhaustion

**Fix**:
```python
# Add pagination with default limits
query = query.order_by(desc(Transaction.date)).limit(1000)  # Last 1000 txs
# Or add date filtering (already done in some methods, but inconsistent)
```

**Affected Methods**:
- `get_transaction_summary()` - loads ALL transactions
- `get_spending_by_category()` - loads ALL expense transactions
- `get_portfolio_summary()` - loads ALL assets
- `spending_patterns()` - loads 3-12 months (could be 10K+ rows)
- `merchant_insights()` - loads 3-12 months
- `budget_status()` - loads 1 month (acceptable)
- `cashflow_summary()` - loads 1 month (acceptable)
- `recurring_analysis()` - loads 3-12 months

---

### 2. N+1 Query Pattern (P1 - High)

**Location**: `backend/services/assistant_service.py:625-717`  
**Issue**: `budget_status()` iterates over budgets and categories without JOIN

```python
# Line 625-717
for budget in budgets:  # Query 1
    for budget_cat in budget.categories:  # N queries (lazy load)
        # Process each category
```

**Risk**:
- 10 budgets × 20 categories = 200 queries
- 2-5s response time for a single API call

**Fix**:
```python
# Use eager loading
budgets = self.db.execute(
    select(BudgetModel)
    .options(joinedload(BudgetModel.categories))  # Eager load
    .where(BudgetModel.is_active == True)
).scalars().all()
```

---

### 3. Missing Indexes (P1 - High)

**Location**: Database schema  
**Issue**: Queries filter on `date`, `type`, `category`, `merchant` without composite indexes

**Recommended Indexes**:
```sql
-- Most common query pattern: date range + type
CREATE INDEX idx_transactions_date_type ON transactions(date DESC, type);

-- Merchant insights
CREATE INDEX idx_transactions_merchant_date ON transactions(merchant, date DESC) 
WHERE merchant IS NOT NULL;

-- Category analysis
CREATE INDEX idx_transactions_category_date ON transactions(category, date DESC);

-- Combined for spending patterns
CREATE INDEX idx_transactions_date_type_category 
ON transactions(date DESC, type, category);
```

**Estimate**: 10-50x query speedup on large datasets

---

## ⚠️ Medium Priority Issues

### 4. Duplicate Date Range Logic (P2 - Medium)

**Pattern Found**: Same date calculation logic repeated 6+ times

```python
# backend/services/assistant_service.py
today = datetime.now().date()
start_date = today - timedelta(days=30 * months)  # Repeated 6x
```

**Fix**: Already addressed by `query_builder.py` (agents working on it)

---

### 5. Inefficient Grouping (P2 - Medium)

**Location**: `spending_patterns()`, `merchant_insights()`  
**Issue**: Python-side grouping instead of SQL `GROUP BY`

```python
# Current: Load all rows, group in Python
for tx in transactions:  # 10K iterations
    monthly_category_totals[month_key][category] += amount
```

**Better**:
```python
# Use SQL aggregation
query = select(
    Transaction.category,
    func.date_trunc('month', Transaction.date).label('month'),
    func.sum(Transaction.amount).label('total')
).where(...).group_by(Transaction.category, 'month')
```

**Benefit**: 100x faster (DB-side aggregation), less memory

---

### 6. Missing Caching (P2 - Medium)

**Location**: `get_portfolio_summary()`, FX rates  
**Issue**: Recalculates portfolio on every call, no TTL cache

**Recommendation**:
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def _get_portfolio_cached(cache_key: str) -> dict:
    # cache_key includes user_id + timestamp rounded to 5min
    pass
```

---

## 🟢 Good Patterns Found

### ✅ Date Filtering
- `budget_status()` correctly filters to 1 month
- `cashflow_summary()` uses month boundaries

### ✅ Type Hints
- All methods have proper type annotations
- Pydantic models for request/response

### ✅ Error Handling
- Try/except blocks in API endpoints
- Graceful degradation when data missing

---

## Recommendations by Priority

### Immediate (P0 - This Week)
1. ✅ Add `query_builder.py` with `.limit()` defaults (agents working on this)
2. Add `LIMIT 1000` to all `.all()` queries as safety net
3. Add logging for query counts (warn if >100ms)

### Short-term (P1 - Next Sprint)
4. Create database indexes (migration)
5. Fix N+1 with `joinedload()`
6. Add SQL-side aggregation for grouping

### Medium-term (P2 - Next Month)
7. Add Redis caching layer for portfolio/FX
8. Implement pagination for assistant responses
9. Add query performance monitoring (Prometheus metrics)

---

## Testing Recommendations

### Load Testing
```bash
# Simulate 100K transactions
pytest backend/tests/test_assistant_performance.py --benchmark

# Expected: <200ms response time, <50MB memory
```

### Query Profiling
```python
# Add to development middleware
from sqlalchemy import event
@event.listens_for(Engine, "before_cursor_execute")
def log_queries(conn, cursor, statement, parameters, context, executemany):
    logger.info(f"Query: {statement[:200]}")
```

---

## Estimated Impact

| Issue | Lines Changed | Perf Gain | Risk |
|-------|---------------|-----------|------|
| Add LIMIT defaults | ~20 | 10-100x | Low |
| Add indexes | ~5 (migration) | 10-50x | Low |
| Fix N+1 | ~10 | 5-10x | Low |
| SQL aggregation | ~100 | 100x | Medium |
| Caching | ~50 | 5-20x | Medium |

**Total**: ~185 lines changed, **50-1000x speedup** on large datasets

---

## Action Items

- [ ] Review with team (Rafael)
- [ ] Prioritize fixes (P0 this week, P1 next sprint)
- [ ] Create issues for each fix (#82-#87)
- [ ] Add performance tests before implementing
- [ ] Deploy to staging, load test with 100K rows
- [ ] Monitor production metrics post-deploy

---

**Next Review**: After P0 fixes deployed (1 week)
