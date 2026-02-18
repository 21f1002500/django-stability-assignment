import random
import string

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from orders.models import Customer, Order, OrderItem

def _rand_email(i: int) -> str:
    return f"user{i}@example.com"

def _rand_name() -> str:
    return "User " + "".join(random.choices(string.ascii_uppercase, k=5))

class DevSeedView(APIView):
    """Dev-only seeding endpoint for the take-home repo.

    POST /api/dev/seed/ { customers, orders_per_customer, items_per_order }

    This is intentionally exposed to keep the take-home fast to run locally.
    """

    def post(self, request):
        customers = int(request.data.get("customers", 100))
        orders_per_customer = int(request.data.get("orders_per_customer", 5))
        items_per_order = int(request.data.get("items_per_order", 3))

        created_customers = 0
        created_orders = 0
        created_items = 0

        last_id = Customer.objects.order_by('-id').values_list('id', flat=True).first() or 0
        start_idx = int(last_id) + 1

        # for i in range(start_idx, start_idx + customers):
        #     c = Customer.objects.create(
        #         name=_rand_name(),
        #         email=_rand_email(i),
        #         is_active=True,
        #     )
        #     created_customers += 1

        #     for _ in range(orders_per_customer):
        #         status_choice = random.choices(
        #             [Order.Status.PAID, Order.Status.DRAFT, Order.Status.SHIPPED],
        #             weights=[0.55, 0.35, 0.10],
        #         )[0]
        #         o = Order.objects.create(customer=c, status=status_choice)
        #         created_orders += 1

        #         for j in range(items_per_order):
        #             sku = f"SKU-{random.randint(1, 200)}"
        #             qty = random.randint(1, 5)
        #             price = random.choice([199, 499, 999, 1499, 2499])
        #             OrderItem.objects.create(order=o, sku=sku, quantity=qty, unit_price_cents=price)
        #             created_items += 1

        # Optimized: Use bulk operations
        orders_to_create = []
        items_to_create = []
        
        for i in range(start_idx, start_idx + customers):
            c = Customer.objects.create(
                name=_rand_name(),
                email=_rand_email(i),
                is_active=True,
            )
            created_customers += 1

            for _ in range(orders_per_customer):
                status_choice = random.choices(
                    [Order.Status.PAID, Order.Status.DRAFT, Order.Status.SHIPPED],
                    weights=[0.55, 0.35, 0.10],
                )[0]
                o = Order(customer=c, status=status_choice)
                orders_to_create.append(o)

        # Bulk create orders
        Order.objects.bulk_create(orders_to_create)
        created_orders = len(orders_to_create)
        
        # Now create items for each order
        for o in orders_to_create:
            for j in range(items_per_order):
                sku = f"SKU-{random.randint(1, 200)}"
                qty = random.randint(1, 5)
                price = random.choice([199, 499, 999, 1499, 2499])
                items_to_create.append(
                    OrderItem(order=o, sku=sku, quantity=qty, unit_price_cents=price)
                )
        
        # Bulk create items
        OrderItem.objects.bulk_create(items_to_create)
        created_items = len(items_to_create)
        
        # Update order totals (bulk_create doesn't trigger save signals)
        for o in orders_to_create:
            total = sum(item.quantity * item.unit_price_cents for item in items_to_create if item.order_id == o.id)
            o.total_cents = total
        Order.objects.bulk_update(orders_to_create, ['total_cents'])

        return Response({
            "customers": created_customers,
            "orders": created_orders,
            "items": created_items,
        }, status=status.HTTP_201_CREATED)
