from django.test import TestCase
from rest_framework.test import APIClient
from orders.models import Customer, Order


class OrderFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = Customer.objects.create(name="Alice", email="alice@example.com")
        self.bob = Customer.objects.create(name="Bob", email="bob@test.com")
        
        # Create various orders
        self.paid = Order.objects.create(customer=self.alice, status=Order.Status.PAID)
        self.draft = Order.objects.create(customer=self.alice, status=Order.Status.DRAFT)
        self.shipped = Order.objects.create(customer=self.bob, status=Order.Status.SHIPPED)
        
        # One archived order (should never show up)
        self.archived = Order.objects.create(
            customer=self.alice, status=Order.Status.PAID, is_archived=True
        )

    def test_filter_by_status(self):
        """Verify we can filter by status (and archived stays hidden)."""
        # 1. Filter by PAID
        res = self.client.get("/api/orders/?status=paid")
        results = res.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.paid.id)
        
        # 2. Filter by DRAFT
        res = self.client.get("/api/orders/?status=draft")
        results = res.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.draft.id)

    def test_filter_by_email(self):
        """Verify we can filter by partial email match."""
        # 1. Search 'example' (should find Alice's 2 orders)
        res = self.client.get("/api/orders/?email=example")
        results = res.json()["results"]
        self.assertEqual(len(results), 2)
        ids = [o["id"] for o in results]
        self.assertIn(self.paid.id, ids)
        self.assertIn(self.draft.id, ids)
        self.assertNotIn(self.archived.id, ids)  # Safety check

        # 2. Search 'bob' (should find Bob's 1 order)
        res = self.client.get("/api/orders/?email=Bob") # Case insensitive check
        results = res.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.shipped.id)

    def test_combined_filters(self):
        """Verify status and email filters work together."""
        # Active Paid orders for Alice
        res = self.client.get("/api/orders/?email=alice&status=paid")
        results = res.json()["results"]
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.paid.id)

