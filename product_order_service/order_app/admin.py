from django.contrib import admin
from django.contrib.admin import ModelAdmin

from order_app.models import Product, Price, Order, Position


class PriceInline(admin.TabularInline):
    """ Информация о товаре """
    model = Price
    extra = 1
    list_display = ("product", "provider", "price")


class PositionInline(admin.TabularInline):
    """Позиции на странице заказов"""
    model = Position
    extra = 1
    list_display = ("product", "provider", "quantity")


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    """Продукты"""
    list_display = ("name", "description")
    inlines = [PriceInline]


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    """Заказы"""
    list_display = ("user",)
    readonly_fields = ("total", "count")
    inlines = [PositionInline]
