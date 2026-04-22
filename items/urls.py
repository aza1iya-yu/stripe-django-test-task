from django.urls import path
from django.views.generic import ListView

from . import views
from .models import Item

urlpatterns = [
    path(
        "",
        ListView.as_view(
            template_name="item_list.html",
            model=Item,
            context_object_name="items",
        ),
        name="item_list",
    ),
    path("buy/order/<int:order_id>/", views.buy_order, name="buy_order"),
    path("buy/<int:item_id>/", views.buy_item, name="buy_item"),
    path("item/<int:item_id>/", views.item_detail, name="item_detail"),
    path("success/", views.payment_success, name="success"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("order/add/<int:item_id>/", views.add_order, name="add_order"),
]
