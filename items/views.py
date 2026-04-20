import stripe
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import Item

stripe.api_key = settings.STRIPE_SECRET_KEY


def payment_success(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Оплата прошла успешно!")


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
    context = {"item": item, "stripe_public_key": settings.STRIPE_PUBLIC_KEY}
    return render(request, "item_detail.html", context=context)
