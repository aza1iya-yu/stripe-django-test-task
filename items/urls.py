from django.urls import path

from . import views

urlpatterns = [
    path("", views.ItemList.as_view(), name="item_list"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/add/<int:item_id>/", views.add_order, name="add_order"),
    path("buy/order/<int:order_id>/", views.buy_order, name="buy_order"),
    path("buy/<int:item_id>/", views.buy_item, name="buy_item"),
    path("item/<int:item_id>/", views.item_detail, name="item_detail"),
    path("success/", views.payment_success, name="success"),
]
