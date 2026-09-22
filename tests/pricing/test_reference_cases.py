from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.choices import UserRole
from apps.common.factories import TenantFactory
from apps.pricing.models import CalcRule, DiscountPolicy, DiscountTier, OrderDefaults, ServicePrice
from apps.pricing.services.calculator import calculate_preview

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "calc_cases.json"


def _load_fixture() -> dict[str, Any]:
    """Etalon JSON faylni o'qiydi."""

    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _seed_pricing_models(data: dict[str, Any]) -> None:
    """Pricing uchun kerakli model ma'lumotlarini yaratadi."""

    pricing_seed = data["pricing_seed"]
    for rule in pricing_seed["calc_rules"]:
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
    
    CalcRule.objects.update_or_create(
        key="max_cornice_length_m",
        defaults={"value": Decimal("100.000"), "unit": "m", "description": "", "is_active": True}
    )

    ServicePrice.objects.all().delete()
    for service in pricing_seed["service_prices"]:
        ServicePrice.objects.create(
            key=service["key"],
            name=service["name"],
            price=service["price"],
            unit=service["unit"],
            is_active=service["is_active"],
        )

    DiscountTier.objects.all().delete()
    for tier in pricing_seed["discount_tiers"]:
        DiscountTier.objects.create(**tier)

    DiscountPolicy.objects.all().delete()
    DiscountPolicy.objects.create(**pricing_seed["discount_policy"])

    OrderDefaults.objects.all().delete()
    OrderDefaults.objects.create(**pricing_seed["order_defaults"])


def _seed_catalog(data: dict[str, Any]) -> None:
    """Preview uchun kerakli katalog variantlarini yaratadi."""

    tenant = TenantFactory.create()
    category = Category.objects.create(
        tenant=tenant,
        name="Pardalar",
        slug="pardalar",
        sort_order=1,
    )
    product = Product.objects.create(
        tenant=tenant,
        category=category,
        name="Reference curtain",
        code="REF-CURTAIN",
    )
    for variant in data["catalog_seed"]["variants"]:
        ProductVariant.objects.create(
            id=UUID(variant["id"]),
            tenant=tenant,
            product=product,
            sku=variant["sku"],
            color_name=variant["sku"],
            price=variant["price"],
            price_unit=variant["unit"],
            is_active=True,
        )


@pytest.fixture()
def pricing_reference_data(db: Any) -> dict[str, Any]:
    """Reference case'lar uchun bazani tayyorlaydi."""

    data = _load_fixture()
    _seed_pricing_models(data)
    _seed_catalog(data)
    return data


@pytest.mark.parametrize("case_index", range(20), ids=lambda index: f"case-{index + 1:02d}")
def test_reference_cases_match_fixture(
    pricing_reference_data: dict[str, Any], case_index: int
) -> None:
    """JSON fayldagi 20 ta etalon misol bilan natijani bir xil qiladi."""

    case = pricing_reference_data["cases"][case_index]
    result = calculate_preview(case["input"], user_role=UserRole.MANAGER)

    assert result == case["expected"]


def test_reference_fixture_has_twenty_cases() -> None:
    """Go jamoasi bilan umumiy faylda 20 ta case borligini kafolatlaydi."""

    data = _load_fixture()

    assert data["schema_version"] == "alora.pricing.calc_cases.v1"
    assert len(data["cases"]) == 20


@pytest.mark.parametrize("case_index", range(20), ids=lambda index: f"case-{index + 1:02d}")
def test_aggregate_totals_invariant(
    pricing_reference_data: dict[str, Any], case_index: int
) -> None:
    """Har bir case'da yig'indi maydonlari subtotal bilan mos keladi."""

    case = pricing_reference_data["cases"][case_index]
    result = calculate_preview(case["input"], user_role=UserRole.MANAGER)

    parts_total = Decimal(result["parts_total"])
    accessories_total = Decimal(result["accessories_total"])
    services_total = Decimal(result["services_total"])
    assert Decimal(result["subtotal"]) == parts_total + accessories_total + services_total

    for measurement in result["measurements"]:
        assert Decimal(measurement["measurement_total"]) == (
            Decimal(measurement["parts_total"]) + Decimal(measurement["accessories_total"])
        )


def test_parts_total_matches_part_line_totals_on_multi_part_case(
    pricing_reference_data: dict[str, Any],
) -> None:
    """Ko'p bo'lakli holatda parts_total har bir bo'lak line_total yig'indisiga teng."""

    case = next(
        c
        for c in pricing_reference_data["cases"]
        if sum(len(m["parts"]) for m in c["input"]["measurements"]) > 1
    )
    result = calculate_preview(case["input"], user_role=UserRole.MANAGER)

    all_part_totals = sum(
        (
            Decimal(part["line_total"])
            for measurement in result["measurements"]
            for part in measurement["parts"]
        ),
        Decimal(0),
    )
    assert Decimal(result["parts_total"]) == all_part_totals
    assert sum(Decimal(m["parts_total"]) for m in result["measurements"]) == all_part_totals
