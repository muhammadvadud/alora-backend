from __future__ import annotations

from decimal import Decimal

import pytest

from apps.pricing.services.crud import (
    _as_decimal,
    _normalized_items,
    upsert_calc_rules,
    upsert_service_prices,
)


def test_as_decimal() -> None:
    """_as_decimal funksiyasini tekshiradi."""

    assert _as_decimal(Decimal("10.5")) == Decimal("10.5")
    assert _as_decimal("10.5") == Decimal("10.5")
    assert _as_decimal(10.5) == Decimal("10.5")
    assert _as_decimal(10) == Decimal(10)


def test_normalized_items() -> None:
    """_normalized_items funksiyasini turli ma'lumotlar bilan tekshiradi."""

    assert _normalized_items(None) == []
    assert _normalized_items({"key": "val"}) == [{"key": "val"}]
    assert _normalized_items({"items": [{"key": "val"}]}) == [{"key": "val"}]
    assert _normalized_items([{"key": "val"}]) == [{"key": "val"}]
    assert _normalized_items(({"key": "val"},)) == [{"key": "val"}]

    # Iterable tekshiruvi (generator)
    gen = ({"key": "val"} for _ in range(1))
    assert _normalized_items(gen) == [{"key": "val"}]

    # Dict kabi ishlaydigan obyekt
    class SingleObj:
        def keys(self) -> list[str]:
            return ["key"]

        def __getitem__(self, item: str) -> str:
            return "val"

    assert _normalized_items(SingleObj()) == [{"key": "val"}]


@pytest.mark.django_db
def test_upsert_calc_rules() -> None:
    """upsert_calc_rules orqali yangi va mavjud qoidalarni saqlashni tekshiradi."""

    rules = upsert_calc_rules([{"key": "test1", "value": "1.5"}])
    assert len(rules) == 1
    assert rules[0].key == "test1"
    assert rules[0].value == Decimal("1.5")

    rules = upsert_calc_rules(
        [{"key": "test1", "value": "2.0", "unit": "m", "description": "desc", "is_active": False}]
    )
    assert len(rules) == 1
    assert rules[0].key == "test1"
    assert rules[0].value == Decimal("2.0")
    assert rules[0].unit == "m"
    assert rules[0].description == "desc"
    assert rules[0].is_active is False


@pytest.mark.django_db
def test_upsert_service_prices() -> None:
    """upsert_service_prices orqali yangi va mavjud xizmat narxlarini saqlashni tekshiradi."""

    prices = upsert_service_prices([{"key": "svc1", "price": "100"}])
    assert len(prices) == 1
    assert prices[0].key == "svc1"
    assert prices[0].price == Decimal(100)

    prices = upsert_service_prices(
        [{"key": "svc1", "price": "200", "name": "Service 1", "unit": "m", "is_active": False}]
    )
    assert len(prices) == 1
    assert prices[0].key == "svc1"
    assert prices[0].price == Decimal(200)
    assert prices[0].name == "Service 1"
    assert prices[0].unit == "m"
    assert prices[0].is_active is False
