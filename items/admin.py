from django.contrib import admin

from .models import Discount, Item, Order, OrderItem, Tax


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
    list_display = ("id", "created_at", "is_paid", "total_cost", "tax", "discount")
    list_filter = ("is_paid",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "stripe_coupon_id", "stripe_promotion_code_id")
    list_editable = ("amount",)
    readonly_fields = ("stripe_coupon_id", "stripe_promotion_code_id")


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "stripe_tax_rate_id")
    list_editable = ("rate",)
    readonly_fields = ("stripe_tax_rate_id",)
