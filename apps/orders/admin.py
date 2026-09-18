from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateTimeFilter
from unfold.decorators import display

from apps.common.choices import OrderStatus, PaymentStatus

from .models import Order, OrderAccessory, OrderCurtainPart, OrderItem, OrderMeasurement


def _fmt_uzs(value) -> str:
    return f"{value:,.2f} UZS" if value is not None else "—"


class OrderMeasurementInline(TabularInline):
    model = OrderMeasurement
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "room_name",
        "cornice_length_m",
        "height_m",
        "coefficient",
        "layers",
        "note",
    )


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("service_key", "name_snapshot", "qty", "unit", "unit_price", "total", "sort_order")


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "number",
        "customer_name",
        "status_badge",
        "payment_badge",
        "total_display",
        "user",
        "created_at",
    )
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("payment_status", ChoicesDropdownFilter),
        ("discount_source", ChoicesDropdownFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("number", "customer_name", "customer_phone")
    readonly_fields = ("created_at", "updated_at", "number_seq")
    inlines = [OrderMeasurementInline, OrderItemInline]

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj is None:
            fields = tuple(f for f in fields if f != "number_seq")
        return fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None:
            return [
                (label, {**opts, "fields": tuple(f for f in opts["fields"] if f != "number_seq")})
                for label, opts in fieldsets
            ]
        return fieldsets

    fieldsets = (
        (
            _("Buyurtma"),
            {
                "fields": (
                    "number",
                    "number_seq",
                    "user",
                    "conversation",
                    "customer_name",
                    "customer_phone",
                    "address",
                )
            },
        ),
        (
            _("Holat"),
            {"fields": ("status", "payment_status", "deadline_date", "note")},
        ),
        (
            _("Summalar"),
            {
                "fields": (
                    "subtotal",
                    "discount_percent",
                    "discount_amount",
                    "discount_source",
                    "delivery_amount",
                    "total",
                    "prepayment_percent",
                    "prepayment",
                    "balance",
                )
            },
        ),
        (
            _("Tasdiqlash"),
            {"fields": ("confirmed_by", "confirmed_at")},
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(
        description=_("Holat"),
        label={
            OrderStatus.DRAFT: "default",
            OrderStatus.CONFIRMED: "primary",
            OrderStatus.MEASURING: "info",
            OrderStatus.PRODUCTION: "warning",
            OrderStatus.READY: "warning",
            OrderStatus.INSTALLING: "info",
            OrderStatus.COMPLETED: "success",
            OrderStatus.CANCELLED: "danger",
        },
    )
    def status_badge(self, obj: Order) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(
        description=_("To'lov"),
        label={
            PaymentStatus.UNPAID: "danger",
            PaymentStatus.PREPAID: "warning",
            PaymentStatus.PAID: "success",
        },
    )
    def payment_badge(self, obj: Order) -> tuple[str, str]:
        return obj.payment_status, obj.get_payment_status_display()

    @display(description=_("Jami"))
    def total_display(self, obj: Order) -> str:
        return _fmt_uzs(obj.total)


@admin.register(OrderMeasurement)
class OrderMeasurementAdmin(ModelAdmin):
    list_display = (
        "order",
        "room_name",
        "cornice_length_m",
        "height_m",
        "coefficient",
        "created_at",
    )
    list_filter = (("created_at", RangeDateTimeFilter),)
    search_fields = ("order__number", "room_name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("O'lchov"),
            {
                "fields": (
                    "order",
                    "room_name",
                    "cornice_length_m",
                    "height_m",
                    "coefficient",
                    "layers",
                    "note",
                )
            },
        ),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(OrderCurtainPart)
class OrderCurtainPartAdmin(ModelAdmin):
    list_display = ("measurement", "role", "variant", "area_sqm", "total", "sort_order")
    list_filter = (("role", ChoicesDropdownFilter),)
    search_fields = ("variant__sku", "measurement__room_name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Bo'lak"),
            {
                "fields": (
                    "measurement",
                    "variant",
                    "role",
                    "width_m",
                    "height_m",
                    "coefficient",
                    "area_sqm",
                    "price_per_sqm",
                    "total",
                    "sort_order",
                )
            },
        ),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(OrderAccessory)
class OrderAccessoryAdmin(ModelAdmin):
    list_display = ("measurement", "variant", "qty", "unit", "total")
    list_filter = (("unit", ChoicesDropdownFilter),)
    search_fields = ("variant__sku", "measurement__room_name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Aksessuar"),
            {
                "fields": (
                    "measurement",
                    "variant",
                    "qty",
                    "unit",
                    "unit_price",
                    "total",
                    "sort_order",
                )
            },
        ),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ("order", "service_key", "name_snapshot", "qty", "unit_price", "total")
    list_filter = (("unit", ChoicesDropdownFilter),)
    search_fields = ("order__number", "name_snapshot", "service_key")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Xizmat qatori"),
            {
                "fields": (
                    "order",
                    "measurement",
                    "service_key",
                    "name_snapshot",
                    "qty",
                    "unit",
                    "unit_price",
                    "total",
                    "sort_order",
                )
            },
        ),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )
