from django.test import TestCase
from rest_framework.test import APIClient
from orders.models import Customer, Order, OrderItem

class SummaryEndpointTests(TestCase):
    def test_summary_endpoint_returns_rows(self):
        client = APIClient()

        c = Customer.objects.create(name="Bob", email="bob@example.com")
        o = Order.objects.create(customer=c, status=Order.Status.PAID)
        OrderItem.objects.create(order=o, sku="SKU-1", quantity=2, unit_price_cents=500)

        res = client.get("/api/orders/summary/?limit=10")
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertIn("rows", payload)
        self.assertGreaterEqual(len(payload["rows"]), 1)
