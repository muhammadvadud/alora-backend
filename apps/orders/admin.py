from django.contrib import admin

from .models import Order, OrderAccessory, OrderCurtainPart, OrderItem, OrderMeasurement


class OrderMeasurementInline(admin.TabularInline):
    model = OrderMeasurement
    extra = 0
    readonly_fields = ("created_at", "updated_at")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "status", "customer_name", "total", "tenant", "created_at")
    list_filter = ("status", "tenant")
    search_fields = ("number", "customer_name", "customer_phone")
    readonly_fields = ("created_at", "updated_at")
    inlines = [
        OrderMeasurementInline,
        OrderItemInline
    ]

@admin.register(OrderMeasurement)
class OrderMeasurementAdmin(admin.ModelAdmin):
    list_display = ("order", "room_name", "cornice_length_m", "height_m", "created_at")
    readonly_fields = ("created_at", "updated_at")

@admin.register(OrderCurtainPart)
class OrderCurtainPartAdmin(admin.ModelAdmin):
    list_display = ("measurement", "role", "variant")
    readonly_fields = ("created_at", "updated_at")

@admin.register(OrderAccessory)
class OrderAccessoryAdmin(admin.ModelAdmin):
    list_display = ("measurement", "variant", "qty")
    readonly_fields = ("created_at", "updated_at")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "service_key", "total")
    readonly_fields = ("created_at", "updated_at")
