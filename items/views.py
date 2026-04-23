import json
from collections import defaultdict
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView

from .models import Item, Order, OrderItem


def get_stripe_line_item(
    name: str,
    description: str,
    price: Decimal,
    quantity: int = 1,
    tax_rates: list[str] = None,
    currency: str = None,
) -> dict:
    product_data = {"name": name}
    if description:
        product_data["description"] = description

    line_item = {
        "price_data": {
            "currency": currency if currency else "USD",
            "product_data": product_data,
            "unit_amount": int(round(price * 100)),
        },
        "quantity": quantity,
    }

    if tax_rates:
        line_item["tax_rates"] = tax_rates

    return line_item


def get_tax_rate_for_item(item, currency):
    if not item.tax:
        return None

    if currency == "usd":
        tax_rate = item.tax.stripe_tax_rate_id_usd
    else:
        tax_rate = item.tax.stripe_tax_rate_id_eur

    return [tax_rate] if tax_rate else None


def create_stripe_session_for_items(request, currency, items, order):
    session_params = {
        "mode": "payment",
        "line_items": [
            get_stripe_line_item(
                item.item.name,
                item.item.description,
                item.price,
                item.quantity,
                tax_rates=get_tax_rate_for_item(item.item, currency),
                currency=currency,
            )
            for item in items
        ],
        "success_url": request.build_absolute_uri(reverse("success"))
        + "?session_id={CHECKOUT_SESSION_ID}",
        "allow_promotion_codes": True,
        "metadata": {
            "order_id": str(order.pk),
            "currency": currency,
        },
    }

    if order.discount:
        if currency == "usd":
            discount = order.discount.stripe_promotion_code_id_usd
        else:
            discount = order.discount.stripe_promotion_code_id_eur
        session_params["discounts"] = [{"promotion_code": discount}]

    api_key = settings.STRIPE_KEYS[currency]["secret"]

    return stripe.checkout.Session.create(api_key=api_key, **session_params)


def get_checkout_session(session_id: str):
    api_keys = []
    for currency_key in ("usd", "eur"):
        key = settings.STRIPE_KEYS.get(currency_key, {}).get("secret")
        if key and key not in api_keys:
            api_keys.append(key)

    for api_key in api_keys:
        try:
            return stripe.checkout.Session.retrieve(session_id, api_key=api_key)
        except stripe.error.InvalidRequestError:
            continue

    return None


def get_stripe_value(stripe_obj, key, default=None):
    try:
        return stripe_obj[key]
    except (KeyError, TypeError):
        return default


class ItemList(ListView):
    template_name = ("item_list.html",)
    model = (Item,)
    context_object_name = "items"

    def get_queryset(self):
        return Item.objects.filter(stock__gt=0)


def payment_success(request: HttpRequest) -> HttpResponse:
    session_id = request.GET.get("session_id")
    if not session_id:
        return render(request, "items/success.html")

    checkout_session = get_checkout_session(session_id)
    payment_status = get_stripe_value(checkout_session, "payment_status")
    if not checkout_session or payment_status != "paid":
        return render(request, "items/success.html")

    metadata = get_stripe_value(checkout_session, "metadata", {})
    metadata_order_id = get_stripe_value(metadata, "order_id")
    metadata_currency = get_stripe_value(metadata, "currency")

    checkout_order_id = request.session.get("checkout_order_id")
    checkout_currency = metadata_currency or request.session.get("checkout_currency")
    cart_order_id = request.session.get("order_id")
    order_id = metadata_order_id or checkout_order_id or cart_order_id
    if order_id:
        order = get_object_or_404(
            Order.objects.prefetch_related("order_items__item"), pk=order_id
        )
        if not order.is_paid and (
            checkout_order_id is None or str(checkout_order_id) == str(order.pk)
        ):
            order_items = order.order_items.filter(is_paid=False)
            if checkout_currency:
                order_items = order_items.filter(item__currency=checkout_currency)

            for order_item in order_items:
                Item.objects.filter(pk=order_item.item_id).update(
                    stock=F("stock") - order_item.quantity,
                )
                order_item.is_paid = True
                order_item.save()

            if not order.order_items.filter(is_paid=False).exists():
                order.is_paid = True
            order.save()

        if request.session.get("checkout_order_id") == order_id:
            del request.session["checkout_order_id"]
        if "checkout_currency" in request.session:
            del request.session["checkout_currency"]

        if request.session.get("order_id") == order_id:
            has_unpaid_items = order.order_items.filter(is_paid=False).exists()
            if not has_unpaid_items:
                del request.session["order_id"]

    return render(request, "items/success.html")


@require_GET
def buy_item(request: HttpRequest, item_id: int) -> JsonResponse:
    item = get_object_or_404(Item, pk=item_id)

    order = Order.objects.create()
    order_id = order.pk
    request.session["checkout_order_id"] = order_id
    request.session["checkout_currency"] = item.currency
    request.session.modified = True
    order_item = OrderItem.objects.create(
        order=order,
        item=item,
        quantity=1,
        price=item.price,
    )
    session = create_stripe_session_for_items(
        request=request,
        currency=item.currency,
        items=[order_item],
        order=order,
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

            items_by_currency = defaultdict(list)
            for order_item in order.order_items.all():
                if not order_item.is_paid:
                    currency = order_item.item.currency
                    items_by_currency[currency].append(order_item)

            currency_groups = []
            for currency, currency_items in items_by_currency.items():
                total = sum(item.subtotal_cost() for item in currency_items)
                currency_groups.append(
                    {
                        "currency": currency,
                        "currency_symbol": "$" if currency == "usd" else "€",
                        "items": currency_items,
                        "total": total,
                        "count": len(currency_items),
                    }
                )

            context["currency_groups"] = currency_groups
            context["has_multiple_currencies"] = len(currency_groups) > 1
            context["order_id"] = order_id
        else:
            context["currency_groups"] = []
            context["has_multiple_currencies"] = False
            context["order_id"] = None

        return context


@require_POST
@transaction.atomic
def add_order(request: HttpRequest, item_id: int) -> JsonResponse:
    item = get_object_or_404(Item, pk=item_id)

    order_id = request.session.get("order_id")
    order = None
    if order_id:
        order = Order.objects.filter(pk=order_id, is_paid=False).first()

    if not order:
        order = Order.objects.create()
        order_id = order.pk
        request.session["order_id"] = order_id
        request.session.modified = True

    try:
        data = json.loads(request.body)
        quantity = int(data.get("quantity", 1))
    except (json.JSONDecodeError, ValueError):
        quantity = 1

    if quantity < 1:
        return JsonResponse(
            {"error": "Quantity must be greater than or equal to 1"},
            status=400,
        )

    order_item, created = OrderItem.objects.get_or_create(
        order=order, item=item, defaults={"quantity": quantity, "price": item.price}
    )
    if created:
        final_quantity = quantity
    else:
        final_quantity = order_item.quantity + quantity

    if final_quantity > item.stock:
        return JsonResponse(
            {"error": f"There is not enough product. In stock: {item.stock}"},
            status=400,
        )

    if not created:
        order_item.quantity = final_quantity
        order_item.save()

    total_quantity = order.total_quantity()

    return JsonResponse({"total_quantity": total_quantity})


@require_GET
def buy_order(request: HttpRequest, order_id: int) -> JsonResponse:
    currency = request.GET.get("currency")
    session_order_id = request.session.get("order_id")

    if not session_order_id or session_order_id != order_id:
        return JsonResponse({"error": "Access denied for this order"}, status=403)

    order = get_object_or_404(
        Order.objects.prefetch_related("order_items__item"), pk=order_id
    )
    if order.is_paid:
        return JsonResponse({"error": "Order already paid"}, status=400)

    request.session["checkout_order_id"] = order.pk
    request.session.modified = True
    items = order.order_items.filter(is_paid=False)

    if not items.exists():
        return JsonResponse({"error": "Order is empty"}, status=400)

    if currency:
        items = items.filter(item__currency=currency)
        if not items.exists():
            return JsonResponse(
                {"error": f"No items in {currency} currency"}, status=400
            )

    items_by_currency = defaultdict(list)
    for order_item in items:
        currency = order_item.item.currency
        items_by_currency[currency].append(order_item)

    if currency or len(items_by_currency) == 1:
        target_currency = currency or list(items_by_currency.keys())[0]
        request.session["checkout_currency"] = target_currency
        request.session.modified = True
        currency_items = items_by_currency[target_currency]

        session = create_stripe_session_for_items(
            request, target_currency, currency_items, order
        )
        return JsonResponse({"session_id": session.id, "session_url": session.url})

    return JsonResponse(
        {
            "error": "Multiple currencies detected",
            "currencies": list(items_by_currency.keys()),
            "message": "Please select currency to pay",
        },
        status=400,
    )
