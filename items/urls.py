from django.conf import settings
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
            extra_context={"stripe_public_key": settings.STRIPE_PUBLIC_KEY},
        ),
        name="item_list",
    ),
    path("buy/<int:item_id>/", views.buy_item, name="buy_item"),
    path("item/<int:item_id>/", views.item_detail, name="item_detail"),
    path("success/", views.payment_success, name="success"),
]
