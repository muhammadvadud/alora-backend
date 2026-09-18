from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesRadioFilter, RangeDateTimeFilter
from unfold.decorators import display

from apps.common.choices import PriceUnit

from .models import (
    CalcRule,
    DiscountPolicy,
    DiscountTier,
    ModelPricing,
    OrderDefaults,
    ServicePrice,
)


def _fmt_uzs(value) -> str:
    return f"{value:,.2f} UZS" if value is not None else "—"


def _fmt_usd(value) -> str:
    return f"${value:,.4f}" if value is not None else "—"


@admin.register(CalcRule)
class CalcRuleAdmin(ModelAdmin):
    list_display = ("key", "value", "unit", "is_active", "created_at")
    search_fields = ("key", "description")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Qoida"),
            {"fields": ("key", "value", "unit", "description", "applies_to")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ServicePrice)
class ServicePriceAdmin(ModelAdmin):
    list_display = ("key", "name", "price_display", "price_unit_badge", "is_active")
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("unit", ChoicesRadioFilter),
    )
    search_fields = ("key", "name")
    readonly_fields = ("created_at", "updated_at", "price_display")
    fieldsets = (
        (
            _("Xizmat"),
            {"fields": ("key", "name", "price", "price_display", "unit")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Narx"))
    def price_display(self, obj: ServicePrice) -> str:
        return _fmt_uzs(obj.price)

    @display(
        description=_("Birlik"),
        label={
            PriceUnit.PER_SQM: "primary",
            PriceUnit.PER_PIECE: "info",
            PriceUnit.PER_METER: "warning",
        },
    )
    def price_unit_badge(self, obj: ServicePrice) -> tuple[str, str]:
        return obj.unit, obj.get_unit_display()


@admin.register(DiscountTier)
class DiscountTierAdmin(ModelAdmin):
    list_display = ("min_amount", "percent_display", "is_active", "created_at")
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("created_at", RangeDateTimeFilter),
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Chegirma bosqichi"),
            {"fields": ("min_amount", "percent")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Foiz"))
    def percent_display(self, obj: DiscountTier) -> str:
        return f"{obj.percent:.2f}%"


@admin.register(DiscountPolicy)
class DiscountPolicyAdmin(ModelAdmin):
    list_display = (
        "employee_max_display",
        "manager_max_display",
        "stack_with_tier",
        "updated_at",
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Qo'lda chegirma chegaralari"),
            {
                "fields": (
                    "manual_max_percent_employee",
                    "manual_max_percent_manager",
                )
            },
        ),
        (
            _("Qo'shilish qoidalari"),
            {"fields": ("stack_with_tier",)},
        ),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Xodim chegarasi"))
    def employee_max_display(self, obj: DiscountPolicy) -> str:
        return f"{obj.manual_max_percent_employee:.2f}%"

    @display(description=_("Menejer chegarasi"))
    def manager_max_display(self, obj: DiscountPolicy) -> str:
        return f"{obj.manual_max_percent_manager:.2f}%"


@admin.register(OrderDefaults)
class OrderDefaultsAdmin(ModelAdmin):
    list_display = ("prepayment_percent", "delivery_amount", "deadline_days", "updated_at")
    readonly_fields = ("created_at", "updated_at", "delivery_amount_display")
    fieldsets = (
        (
            _("Standart qiymatlar"),
            {
                "fields": (
                    "prepayment_percent",
                    "delivery_amount",
                    "delivery_amount_display",
                    "deadline_days",
                )
            },
        ),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Yetkazish narxi"))
    def delivery_amount_display(self, obj: OrderDefaults) -> str:
        return _fmt_uzs(obj.delivery_amount)


@admin.register(ModelPricing)
class ModelPricingAdmin(ModelAdmin):
    list_display = ("provider", "model", "input_per_1m", "output_per_1m", "usd_to_uzs")
    list_filter = (
        ("provider", ChoicesRadioFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("model", "provider")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Model"),
            {"fields": ("provider", "model")},
        ),
        (
            _("Narxlar (USD)"),
            {
                "fields": (
                    "input_per_1m",
                    "output_per_1m",
                    "cached_input_per_1m",
                    "stt_per_minute",
                    "tts_per_1k_chars",
                )
            },
        ),
        (
            _("Kurs"),
            {"fields": ("usd_to_uzs",)},
        ),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )
