from django.contrib import admin

from .models import (
    CalcRule,
    DiscountPolicy,
    DiscountTier,
    ModelPricing,
    OrderDefaults,
    ServicePrice,
)


@admin.register(CalcRule)
class CalcRuleAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "unit", "created_at")
    search_fields = ("key",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(ServicePrice)
class ServicePriceAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "price", "unit", "is_active")
    list_filter = ("is_active", "unit")
    search_fields = ("key", "name")
    readonly_fields = ("created_at", "updated_at")

@admin.register(DiscountTier)
class DiscountTierAdmin(admin.ModelAdmin):
    list_display = ("min_amount", "percent", "is_active")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(DiscountPolicy)
class DiscountPolicyAdmin(admin.ModelAdmin):
    list_display = ("manual_max_percent_employee", "manual_max_percent_manager", "stack_with_tier")
    readonly_fields = ("created_at", "updated_at")

@admin.register(OrderDefaults)
class OrderDefaultsAdmin(admin.ModelAdmin):
    list_display = ("prepayment_percent", "delivery_amount", "deadline_days")
    readonly_fields = ("created_at", "updated_at")

@admin.register(ModelPricing)
class ModelPricingAdmin(admin.ModelAdmin):
    list_display = ("provider", "model", "input_per_1m", "output_per_1m")
    list_filter = ("provider",)
    search_fields = ("model", "provider")
    readonly_fields = ("created_at", "updated_at")
