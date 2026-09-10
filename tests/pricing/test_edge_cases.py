from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.choices import PriceUnit, UserRole
from apps.common.factories import TenantFactory
from apps.pricing.models import CalcRule, DiscountPolicy, DiscountTier, OrderDefaults, ServicePrice
from apps.pricing.serializers import ServicePriceWriteSerializer
from apps.pricing.services.calculator import calculate_preview


def _seed_minimal_pricing() -> None:
    """Kalkulyatsiya uchun minimal qoidalarni yaratadi."""

    calc_rules = [
        {
            "key": "coef_default",
            "value": "2.500",
            "unit": "coef",
            "description": "",
            "applies_to": {},
        },
        {
            "key": "seam_allowance",
            "value": "0.050",
            "unit": "m",
            "description": "",
            "applies_to": {},
        },
        {
            "key": "hem_allowance",
            "value": "0.150",
            "unit": "m",
            "description": "",
            "applies_to": {},
        },
        {"key": "hook_step", "value": "0.100", "unit": "m", "description": "", "applies_to": {}},
        {
            "key": "round_area_to",
            "value": "0.100",
            "unit": "m",
            "description": "",
            "applies_to": {},
        },
        {
            "key": "round_total_to",
            "value": "1000.000",
            "unit": "so'm",
            "description": "",
            "applies_to": {},
        },
        {
            "key": "min_order_amount",
            "value": "0.000",
            "unit": "so'm",
            "description": "",
            "applies_to": {},
        },
        {
            "key": "waste_warn_percent",
            "value": "15.000",
            "unit": "%",
            "description": "",
            "applies_to": {},
        },
    ]
    for rule in calc_rules:
        CalcRule.objects.update_or_create(
            key=rule["key"],
            defaults={
                "value": rule["value"],
                "unit": rule["unit"],
                "description": rule["description"],
                "applies_to": rule["applies_to"],
                "is_active": True,
            },
        )

    ServicePrice.objects.all().delete()
    ServicePrice.objects.create(
        key="sewing",
        name="Tikuv",
        price="25000.00",
        unit=PriceUnit.PER_SQM,
        is_active=True,
    )

    DiscountTier.objects.all().delete()
    DiscountTier.objects.create(min_amount="0.00", percent="0.00", is_active=True)
    DiscountPolicy.objects.all().delete()
    DiscountPolicy.objects.create(
        manual_max_percent_employee="4.00",
        manual_max_percent_manager="10.00",
        stack_with_tier=True,
    )
    OrderDefaults.objects.all().delete()
    OrderDefaults.objects.create(
        prepayment_percent="50.00", delivery_amount="50000.00", deadline_days=3
    )


@pytest.fixture()
def minimal_catalog(db: Any) -> dict[str, Any]:
    """Minimal katalog variantlarini yaratadi."""

    _seed_minimal_pricing()
    tenant = TenantFactory.create()
    category = Category.objects.create(
        tenant=tenant, name="Pardalar", slug="pardalar", sort_order=1
    )
    product = Product.objects.create(
        tenant=tenant, category=category, name="Reference", code="REF-01"
    )
    variant = ProductVariant.objects.create(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        tenant=tenant,
        product=product,
        sku="FAB-A",
        color_name="Oq",
        price="120000.00",
        price_unit=PriceUnit.PER_SQM,
        is_active=True,
    )
    return {"tenant": tenant, "variant": variant}


def test_ten_part_curtain_is_handled(minimal_catalog: dict[str, Any]) -> None:
    """10 bo'lakli parda hisobida xatolik chiqmasligini tekshiradi."""

    variant_id = str(minimal_catalog["variant"].id)
    payload = {
        "measurements": [
            {
                "length": "10.000",
                "height": "3.000",
                "parts": [
                    {
                        "variant_id": variant_id,
                        "role": "portyera",
                        "width_m": "1.000",
                        "height_m": "3.000",
                        "coef": "2.500",
                    }
                    for _ in range(10)
                ],
                "accessories": [],
            }
        ],
        "services": ["sewing"],
        "discount_percent": "0",
        "delivery": False,
    }

    result = calculate_preview(payload, user_role=UserRole.MANAGER)

    assert len(result["measurements"][0]["parts"]) == 10
    assert result["subtotal"] != "0.00"


def test_zero_dimension_does_not_crash(minimal_catalog: dict[str, Any]) -> None:
    """Nol o'lchamli bo'lak nol natija qaytarishini tekshiradi."""

    variant_id = str(minimal_catalog["variant"].id)
    payload = {
        "measurements": [
            {
                "length": "0.000",
                "height": "2.500",
                "parts": [
                    {
                        "variant_id": variant_id,
                        "role": "portyera",
                        "width_m": "0.000",
                        "height_m": "2.500",
                        "coef": "2.500",
                    }
                ],
                "accessories": [],
            }
        ],
        "services": ["sewing"],
        "discount_percent": "0",
        "delivery": False,
    }

    result = calculate_preview(payload, user_role=UserRole.MANAGER)

    assert result["subtotal"] == "0.00"
    assert result["total"] == "0.00"


def test_negative_price_is_rejected(db: Any) -> None:
    """Manfiy narx serializer darajasida rad etilishini tekshiradi."""

    serializer = ServicePriceWriteSerializer(
        data={
            "key": "bad-service",
            "name": "Bad",
            "price": Decimal("-1.00"),
            "unit": PriceUnit.PER_PIECE,
            "is_active": True,
        }
    )

    assert serializer.is_valid() is False
    assert "price" in serializer.errors
    assert "0 dan kichik" in str(serializer.errors["price"][0])
