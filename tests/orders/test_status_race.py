"""Buyurtma holatini o'zgartirishda poyga holati (race condition) testlari."""

from __future__ import annotations

from typing import Any

import pytest
from django.core.exceptions import ValidationError

from apps.common.choices import OrderStatus
from apps.orders.services import change_order_status


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_concurrent_status_change_only_one_wins(manager: Any, create_order: Any) -> None:
    """Ikki parallel so'rov bir vaqtda statusni o'zgartirsa, bittasi g'olib bo'lishi kerak."""

    from concurrent.futures import ThreadPoolExecutor

    from django.db import connection

    # Buyurtma yaratish va uni CONFIRMED holatiga o'tkazish
    order = create_order(user=manager)
    order = change_order_status(order=order, target=OrderStatus.CONFIRMED, user=manager)

    def attempt(target: str) -> str:
        import time
        if target == OrderStatus.MEASURING:
            time.sleep(0.1)  # Ensure cancelled gets the lock first
        try:
            change_order_status(order=order, target=target, user=manager)
            return "ok"
        except ValidationError:
            return "rejected"
        finally:
            connection.close()

    # Bir vaqtda measuring va cancelled holatlariga o'tkazishga urinish
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, [OrderStatus.MEASURING, OrderStatus.CANCELLED]))

    # Faqat bittasi muvaffaqiyatli bo'lishi kerak, ikkinchisi xato (ValidationError) berishi kerak
    assert sorted(results) == ["ok", "rejected"]
