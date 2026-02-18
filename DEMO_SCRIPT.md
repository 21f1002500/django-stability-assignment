# 🎬 Video Recording Script (Target: 6-9 Minutes)

**Preparation:**
1. Open VS Code.
2. Close all random tabs.
3. Open these files in tabs (in order):
   - `SOLUTION.md`
   - `orders/signals.py`
   - `orders/views.py`
   - `api/views.py`
   - `orders/tests/test_order_filters.py`
4. Open the **Integrated Terminal** (`Ctrl + \``).
5. Have `DEMO_SCRIPT.md` open on the side (or printed).

---

## 1. Mental Model (Time: 0:00 - 1:00)
**[Action]**: Show `SOLUTION.md` (Top section).

**🗣️ Say:**
> "Hi, I'm Aayush. This is my submission for the Django Stability & Scale assignment.
> 
> **My Mental Model:**
> This system is a standard E-commerce backend with Customers, Orders, and Items. 
> My approach was to prioritize **Stability** first. I noticed the system had a critical bug where cancelling orders deleted customers. 
> 
> Once I fixed that, I moved to **Performance**, identifying N+1 query issues in the summary and seed endpoints. 
> Finally, I added the **Filtering Feature** safely.
> 
> I've documented everything here in `SOLUTION.md`, including my architecture decisions for AWS deployment."

---

## 2. Regression Bug (Time: 1:00 - 3:00)
**[Action]**: Switch to `orders/signals.py`.

**🗣️ Say:**
> "First, let's look at the critical regression.
> The root cause was in this signal handler. 
> 
> **The Bug:**
> When an order status was changed to `CANCELLED`, it was calling `instance.customer.delete()`. 
> This is a catastrophic logic error—cancelling an order should never wipe out a customer's entire account and history.
> 
> **The Fix:**
> I simply removed that destructive line. 
> (Highlight the empty/pass function).
> 
> **Prevention:**
> I also added a regression test case `test_regression_bug.py` to ensure this specific scenario—cancelling an order—is asserted to keep the customer alive."

---

## 3. Tests Passing (Time: 3:00 - 4:00)
**[Action]**: Open Terminal. clear it (`cls`).

**🗣️ Say:**
> "To prove the system is stable, I'll run the full test suite."

**[Action]**: Type `python manage.py test` and hit Enter.

**🗣️ Say:**
> "As you can see, **5 tests ran and passed** in under 0.1 seconds.
> This includes:
> 1. The regression fix test.
> 2. The new feature tests for filtering.
> 3. Performance verification tests.
> 
> The system is green and ready for deployment."

---

## 4. Performance Improvements (Time: 4:00 - 6:00)
**[Action]**: Switch to `orders/views.py` (Scroll to `OrdersSummaryView`).

**🗣️ Say:**
> "Next, let's talk about performance.
> The `Summary` endpoint was suffering from a massive N+1 query problem. It was looping through customers, then orders, then items in Python.
> 
> **The Optimization:**
> I refactored this to use Django's `annotate` with conditional `Sum` and `Count` aggregations.
> (Highlight `total_cents=Sum(..., filter=Q(...))`).
> 
> **The Result:**
> - Queries went from **100+** down to **1**.
> - Execution time dropped from **~300ms** to **4ms**."

**[Action]**: Switch to `api/views.py` (Scroll to `DevSeedView`).

**🗣️ Say:**
> "Similarly, the Seed endpoint was doing thousands of individual inserts.
> I replaced that with `bulk_create` and `bulk_update`.
> This reduced the time from **~5 seconds** to **1.15 seconds**, making the developer experience much snappier."

---

## 5. Feature Demo (Time: 6:00 - 7:30)
**[Action]**: Switch to `orders/views.py` (Scroll to `OrderViewSet`).

**🗣️ Say:**
> "For the required feature, I implemented Order Filtering.
> I added `status` and `email` filters here in `get_queryset`.
> 
> **Key Details:**
> - I used `icontains` for partial email matching.
> - I added `select_related('customer')` here to prevent N+1 queries when filtering by email (since we access customer fields).
> - This implementation is minimal and doesn't break existing consumers."

**[Action]**: Switch to Terminal. Run a curl command or just explain.
*(Optional: Run `curl http://127.0.0.1:8000/api/orders/?status=paid` if server is running)*

**🗣️ Say:**
> "I verified this with 3 new targeted tests in `test_order_filters.py` covering status, email, and combined filtering."

---

## 6. Next Steps & AWS (Time: 7:30 - 8:30)
**[Action]**: Switch back to `SOLUTION.md` (Scroll to AWS section).

**🗣️ Say:**
> "Finally, for Production Readiness:
> I tried to keep the infrastructure simple but scalable.
> 
> **Runtime:** I chose **ECS Fargate** because it's serverless and scales automatically without managing EC2 instances.
> **Database:** **RDS Postgres**, but crucially with **PgBouncer** for connection pooling, since Django opens a connection per request.
> 
> **Monitoring:** Day 1 alerts would focus on 5xx Error Rates and Latency spikes.
> 
> That concludes my walkthrough. The code is stable, tested, and high-performance. Thank you!"

---
**[Action]**: Stop Recording. 🏁
