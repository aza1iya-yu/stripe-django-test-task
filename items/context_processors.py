from django.conf import settings

from .models import Order


def cart_count(request):
    order_id = request.session.get("order_id")

    if order_id:
        try:
            order = Order.objects.get(pk=order_id)
            cart_count = order.total_quantity()
            return {"cart_count": cart_count}
        except Order.DoesNotExist:
            pass
    return {"cart_count": 0}
