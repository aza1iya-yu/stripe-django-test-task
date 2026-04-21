import json

import stripe
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView
from django.db.models import F
from .models import Item, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def payment_success(request: HttpRequest) -> HttpResponse:
    order_id = request.session.get("order_id")
    if order_id:
        order = get_object_or_404(
            Order.objects.prefetch_related("order_items__item"), pk=order_id
        )
        if not order.is_paid:
            for order_item in order.order_items.all():
                Item.objects.filter(pk=order_item.item_id).update(
                    stock=F("stock") - order_item.quantity
                )

            order.is_paid = True
            order.save()

        del request.session["order_id"]

    return render(request, "items/success.html")


@require_GET
def buy_item(request: HttpRequest, item_id: int) -> JsonResponse:
    item = get_object_or_404(Item, pk=item_id)
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "RUB",
                    "product_data": {
                        "name": item.name,
                        "description": item.description,
                    },
                    "unit_amount": int(round(item.price * 100)),
                },
                "quantity": 1,
            }
        ],
        success_url=request.build_absolute_uri(reverse("success")),
    )
    return JsonResponse({"session_id": session.id, "session_url": session.url})


@require_GET
def item_detail(request: HttpRequest, item_id: int) -> HttpResponse:
    item = get_object_or_404(Item, pk=item_id)
    context = {"item": item}
    return render(request, "items/item_detail.html", context=context)


class CartView(ListView):
    template_name = "items/cart.html"
    model = OrderItem
    context_object_name = "items"

    def get_queryset(self):
        order_id = self.request.session.get("order_id")
        if order_id:
            return OrderItem.objects.filter(
                order_id=order_id, order__is_paid=False
            ).select_related("item")
        else:
            return OrderItem.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.session.get("order_id")
        if order_id:
            order = get_object_or_404(
                Order.objects.prefetch_related("order_items__item"), pk=order_id
            )
            context["total_cost"] = order.total_cost()
            context["order_id"] = order_id
        else:
            context["total_cost"] = 0
            context["order_id"] = None
        return context


@csrf_exempt
@require_POST
def add_order(request: HttpRequest, item_id: int) -> JsonResponse:
    item = get_object_or_404(Item, pk=item_id)

    order_id = request.session.get("order_id")
    if not order_id:
        order = Order.objects.create()
        order_id = order.pk
        request.session["order_id"] = order_id
        request.session.modified = True
    else:
        order = get_object_or_404(Order, pk=order_id)

    try:
        data = json.loads(request.body)
        quantity = int(data.get("quantity", 1))
    except (json.JSONDecodeError, ValueError):
        quantity = 1

    if quantity > item.stock:
        return JsonResponse(
            {"error": f"There is not enough product. In stock: {item.stock}"},
            status=400,
        )

    order_item, created = OrderItem.objects.get_or_create(
        order=order, item=item, defaults={"quantity": quantity, "price": item.price}
    )
    if not created:
        order_item.quantity += quantity
        order_item.save()

    total_quantity = order.total_quantity()

    return JsonResponse({"total_quantity": total_quantity})


@require_GET
def buy_order(request: HttpRequest, order_id: int) -> JsonResponse:
    order = get_object_or_404(
        Order.objects.prefetch_related("order_items__item"), pk=order_id
    )
    items = order.order_items.all()

    if items.exists():
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "RUB",
                        "product_data": {
                            "name": item.item.name,
                            "description": item.item.description,
                        },
                        "unit_amount": int(round(item.price * 100)),
                    },
                    "quantity": item.quantity,
                }
                for item in items
            ],
            success_url=request.build_absolute_uri(reverse("success")),
        )
        return JsonResponse({"session_id": session.id, "session_url": session.url})
    else:
        return JsonResponse({"error": "Order is empty"}, status=400)
