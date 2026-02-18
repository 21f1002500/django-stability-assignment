# Solution - Django Stability & Scale Assignment

**Candidate**: Aaysha Mishra
**Time Taken**: ~3-3.5 hours  
**Date**: February 18, 2026  
**Repo Link**: [https://github.com/21f1002500/django-stability-assignment]

---

## Mental Model

This Django service models a simple orders workflow (Customers → Orders → Order Items). My approach was to:

1. **Understand the system** - Review models, views, signals, and identify the data flow
2. **Identify stability issues** - Run tests to reproduce the intentional regression bug
3. **Fix with minimal changes** - Remove problematic code rather than rewrite
4. **Optimize performance** - Replace Python loops with database aggregations
5. **Add safe features** - Implement filtering without breaking existing behaviors
6. **Lock down with tests** - Ensure all changes are covered by automated tests

---

## Instability: Regression Bug

### Reproduction Steps

1. Create a customer and an order for that customer
2. Cancel the order via `POST /api/orders/<id>/cancel/`
3. Try to access the customer via `GET /api/customers/<id>/`
4. **Result**: 404 Not Found (customer was deleted!)

### Root Cause

**File**: `orders/signals.py` (lines 17-23)

```python
@receiver(post_save, sender=Order)
def on_order_saved(sender, instance: Order, created, **kwargs):
    if instance.status == Order.Status.CANCELLED:
        instance.customer.delete()  # ← CATASTROPHIC BUG
```

The signal handler **deletes the customer** whenever an order is cancelled. This is fundamentally wrong business logic.

### Fix Applied

**Minimal change**: Removed the destructive logic entirely.

```python
@receiver(post_save, sender=Order)
def on_order_saved(sender, instance: Order, created, **kwargs):
    # FIXED: Removed customer deletion when order is cancelled.
    pass
```

### Prevention

**Test added**: `orders/tests/test_regression_bug.py`
This test cancels an order and asserts the customer still exists.

---

## Feature Shipped: Order Filtering

### What I Built

Added query parameter filtering to `GET /api/orders/`:

- **Status filter**: `?status=paid|draft|shipped|cancelled`
- **Email filter**: `?email=<partial match, case-insensitive>`
- **Combined**: Both filters can be used together

### Implementation

**File**: `orders/views.py` - `OrderViewSet.get_queryset()`

```python
def get_queryset(self):
    qs = super().get_queryset()
    if self.action == "list":
        qs = qs.filter(is_archived=False)
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        
        # Filter by customer email (case-insensitive contains) if provided
        email_param = self.request.query_params.get('email')
        if email_param:
            qs = qs.select_related('customer').filter(customer__email__icontains=email_param)
    return qs
```

### Why This Approach?

- **Query efficient**: Uses `select_related('customer')` to prevent N+1 queries when filtering by email
- **Safe**: Filters only apply to list views, detail views unaffected

### Tests Added

**File**: `orders/tests/test_order_filters.py` (3 comprehensive test cases)
- `test_filter_by_status`
- `test_filter_by_email`
- `test_combined_filters`

**All tests pass**: `python manage.py test` → **5/5 tests passing**

---

## Performance Improvements

### 1. Summary Endpoint Optimization

**Endpoint**: `GET /api/orders/summary/?limit=50`

#### Before:
- **Query count**: ~100+ queries (N+1 problem with Python loops)
- **Aggregation**: Done in Python (inefficient)

#### After:
- **Query count**: **1 query** (using Django `annotate` with `Sum` and `Count`)
- **Aggregation**: Done in database (efficient)

#### Evidence:
- **Before**: 100+ queries, ~200-300ms
- **After**: **1 query**, **0.0041s (4ms)**
- **Improvement**: 99% reduction in query count, ~98% faster

### 2. Seed Endpoint Optimization

**Endpoint**: `POST /api/dev/seed/`

#### Before:
- **Total INSERTs**: 1,600+ statements (loops + signals)

#### After:
- **Strategy**: `bulk_create` + `bulk_update`
- **Total INSERTs**: ~3 bulk statements

#### Evidence:
- **Before**: ~4.0 - 5.0 seconds (estimated)
- **After**: **1.15 seconds** (measured)
- **Improvement**: ~75% faster execution time

---

## AWS Production Readiness

### Runtime Choice: **ECS Fargate**
- **Why**: Serverless containers, automatic scaling, pay-per-use, no OS management.

### Database: **RDS Postgres**
- **Connection Pooling**: Mandatory usage of **PgBouncer** (or RDS Proxy) because Django opens a connection per request.

### Metrics & Alerts (Day One)
1. **HTTP 5xx Error Rate** (Criticial > 1%)
2. **p95 Latency** (Performance > 500ms)
3. **DB CPU Utilization** (Scale > 80%)
4. **DB Connections** (Leak > 80%)
5. **ECS Task Health** (Availability)

### CI/CD Pipeline
- **GitHub Actions**: Lint -> Test -> Build Docker -> Push ECR -> Deploy Staging -> Deploy Prod (Manual Approval).

---

## Risks & Tradeoffs

### Regression Fix
- **Risk**: Minimal - the signal was purely destructive.

### Performance Optimizations
- **Tradeoff**: `bulk_create` (in seed endpoint) doesn't fire signals. Acceptable for dev/test tools.

### Filter Feature
- **Risk**: `icontains` on email performs full table scan.
- **Mitigation**: Add database index on `customer.email` for scale.

---

## AI Tool Usage

**Tools Used**: Claude

1. **Boilerplate Acceleration**: Used AI to quickly scaffold Django ORM syntax for complex aggregations (`Sum` with `filter` arguments), which I verified against official documentation.
2. **Test Data Scaffolding**: Leveraged AI to generate repetitive test data setup code (creating customers/orders), allowing me to focus on writing the actual assertion logic.
3. **Documentation Search**: Used AI to quickly lookup DRF pagination classes and signal dispatch mechanisms instead of browsing multiple docs pages.

**Impact**: AI acted as a "smart documentation search" and typing assistant, speeding up implementation by ~30%.

---

## Test Results & Reproducibility

```bash
$ python manage.py test
Found 5 test(s).
Creating test database for alias 'default'...\nSystem check identified no issues (0 silenced).
.....
----------------------------------------------------------------------
Ran 5 tests in 0.047s

OK
```

### How to Run
```bash
# Setup
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Run tests
python manage.py test
```
