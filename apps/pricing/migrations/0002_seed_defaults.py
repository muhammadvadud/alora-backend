from __future__ import annotations

from decimal import Decimal

from django.db import migrations

DEFAULT_RULES: list[dict[str, object]] = [
    {
        "key": "coef_default",
        "value": Decimal("2.500"),
        "unit": "coef",
        "description": "Agar bo'lak koeffitsienti berilmasa ishlatiladi.",
        "applies_to": {},
    },
    {
        "key": "seam_allowance",
        "value": Decimal("0.050"),
        "unit": "m",
        "description": "Yon chok uchun qo'shimcha.",
        "applies_to": {},
    },
    {
        "key": "hem_allowance",
        "value": Decimal("0.150"),
        "unit": "m",
        "description": "Pastki buklama uchun qo'shimcha.",
        "applies_to": {},
    },
    {
        "key": "hook_step",
        "value": Decimal("0.100"),
        "unit": "m",
        "description": "Ilgaklar orasidagi qadamlash.",
        "applies_to": {},
    },
    {
        "key": "round_area_to",
        "value": Decimal("0.100"),
        "unit": "m2",
        "description": "Yuzani yaxlitlash qadami.",
        "applies_to": {},
    },
    {
        "key": "round_total_to",
        "value": Decimal("1000.000"),
        "unit": "so'm",
        "description": "Buyurtma jami yaxlitlash qadami.",
        "applies_to": {},
    },
    {
        "key": "min_order_amount",
        "value": Decimal("0.000"),
        "unit": "so'm",
        "description": "Minimal buyurtma summasi.",
        "applies_to": {},
    },
    {
        "key": "waste_warn_percent",
        "value": Decimal("15.000"),
        "unit": "%",
        "description": "Chiqindi uchun ogohlantirish chegarasi.",
        "applies_to": {},
    },
]

DEFAULT_SERVICES: list[dict[str, object]] = [
    {
        "key": "sewing",
        "name": "Tikuv",
        "price": Decimal("12500.00"),
        "unit": "per_sqm",
        "is_active": True,
    },
    {
        "key": "install",
        "name": "Montaj",
        "price": Decimal("20000.00"),
        "unit": "per_piece",
        "is_active": True,
    },
    {
        "key": "tape",
        "name": "Tasma",
        "price": Decimal("5000.00"),
        "unit": "per_meter",
        "is_active": True,
    },
    {
        "key": "hook",
        "name": "Ilgich",
        "price": Decimal("1500.00"),
        "unit": "per_piece",
        "is_active": True,
    },
    {
        "key": "delivery",
        "name": "Yetkazish",
        "price": Decimal("30000.00"),
        "unit": "per_piece",
        "is_active": True,
    },
]


def forwards(apps, schema_editor) -> None:
    """Boshlang'ich hisob qoidalarini yaratadi."""

    CalcRule = apps.get_model("pricing", "CalcRule")
    DiscountPolicy = apps.get_model("pricing", "DiscountPolicy")
    OrderDefaults = apps.get_model("pricing", "OrderDefaults")
    ServicePrice = apps.get_model("pricing", "ServicePrice")

    for rule in DEFAULT_RULES:
        CalcRule.objects.update_or_create(key=rule["key"], defaults=rule)

    for service in DEFAULT_SERVICES:
        ServicePrice.objects.update_or_create(key=service["key"], defaults=service)

    DiscountPolicy.objects.update_or_create(
        defaults={
            "manual_max_percent_employee": Decimal("5.00"),
            "manual_max_percent_manager": Decimal("10.00"),
            "stack_with_tier": True,
        },
        pk=None,
    )
    OrderDefaults.objects.update_or_create(
        defaults={
            "prepayment_percent": Decimal("50.00"),
            "delivery_amount": Decimal("30000.00"),
            "deadline_days": 3,
        },
        pk=None,
    )


def backwards(apps, schema_editor) -> None:
    """Boshlang'ich hisob qoidalarini va singleton sozlamalarni o'chiradi."""

    CalcRule = apps.get_model("pricing", "CalcRule")
    DiscountPolicy = apps.get_model("pricing", "DiscountPolicy")
    OrderDefaults = apps.get_model("pricing", "OrderDefaults")
    ServicePrice = apps.get_model("pricing", "ServicePrice")

    CalcRule.objects.filter(key__in=[rule["key"] for rule in DEFAULT_RULES]).delete()
    ServicePrice.objects.filter(key__in=[service["key"] for service in DEFAULT_SERVICES]).delete()
    DiscountPolicy.objects.all().delete()
    OrderDefaults.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("pricing", "0001_initial")]

    operations = [migrations.RunPython(forwards, backwards)]
