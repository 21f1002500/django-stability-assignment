from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Order, OrderItem
from .serializers import CustomerSerializer, OrderSerializer, OrderItemSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-id")
    serializer_class = CustomerSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Default behavior: hide archived orders in list views.
        # (Note: detail views should still retrieve by id.)
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

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return Response({"id": order.id, "status": order.status})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        order = self.get_object()
        order.is_archived = True
        order.save(update_fields=["is_archived", "updated_at"])
        return Response({"id": order.id, "is_archived": order.is_archived})

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all().order_by("-id")
    serializer_class = OrderItemSerializer

class OrdersSummaryView(APIView):
    """Returns top customers by total spent (paid orders only).
    
    Optimized to use database aggregation instead of Python loops.
    """

    def get(self, request):
        from django.db.models import Sum, Count, Q
        
        limit = int(request.query_params.get("limit", 50))

        customers = list(Customer.objects.filter(is_active=True).order_by("-id")[:limit])

        rows = []
        # INTENTIONAL PERF ISSUE:
        # - N+1: for each customer -> query orders; for each order -> query items; compute totals in Python.
        # for c in customers:
        #     paid_orders = Order.objects.filter(customer=c, status=Order.Status.PAID, is_archived=False)
        #     total = 0
        #     order_count = 0
        #     for o in paid_orders:
        #         order_count += 1
        #         # Another N+1:
        #         for item in OrderItem.objects.filter(order=o):
        #             total += item.line_total_cents()
        #     rows.append({
        #         "customer_id": c.id,
        #         "email": c.email,
        #         "order_count": order_count,
        #         "total_cents": total,
        #     })

        # rows.sort(key=lambda r: r["total_cents"], reverse=True)
        # return Response({"limit": limit, "rows": rows})

        # Optimized: Single query with aggregation instead of N+1 queries
        customers_data = (
            Customer.objects
            .filter(is_active=True)
            .annotate(
                total_cents=Sum(
                    'orders__total_cents',
                    filter=Q(orders__status=Order.Status.PAID, orders__is_archived=False),
                    default=0
                ),
                order_count=Count(
                    'orders',
                    filter=Q(orders__status=Order.Status.PAID, orders__is_archived=False)
                )
            )
            .order_by('-total_cents')
            [:limit]
        )
        
        rows = [
            {
                "customer_id": c.id,
                "email": c.email,
                "order_count": c.order_count,
                "total_cents": c.total_cents,
            }
            for c in customers_data
        ]

        return Response({"limit": limit, "rows": rows})
