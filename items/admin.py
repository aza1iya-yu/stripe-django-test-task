from django.contrib import admin

from .models import Item, Order, OrderItem


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "price", "stock")
    search_fields = ("name", "description")
    list_editable = ("stock",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ("id", "created_at", "is_paid", "total_cost")
    list_filter = ("is_paid",)
