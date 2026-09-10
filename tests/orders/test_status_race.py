"""Buyurtma holatini o'zgartirishda poyga holati (race condition) testlari."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import connection

from apps.common.choices import OrderStatus
from apps.orders.services import change_order_status


@pytest.mark.django_db(transaction=True)
def test_concurrent_cancel_only_one_wins(
    pricing_defaults: Any, manager: Any, create_order: Any
) -> None:
    """Ikki oqim bir vaqtda bekor qilsa, faqat bittasi o'tadi.

    `cancelled` terminal holat: undan chiquvchi o'tish yo'q. Shuning uchun
    ikkinchi urinish `cancelled -> cancelled` sifatida rad etilishi kerak.

    Qulf (`select_for_update`) bo'lmasa ikkala oqim ham `confirmed` ni o'qiydi,
    ikkalasi ham validatsiyadan o'tadi va ikkalasi ham "ok" qaytaradi — test
    aynan shu regressiyani ushlaydi. `barrier` ikkala oqimni bir vaqtda
    boshlashga majbur qiladi, ya'ni tartib sun'iy ravishda belgilanmaydi.
    """

    order = create_order(user=manager)
    order = change_order_status(order=order, target=OrderStatus.CONFIRMED, user=manager)

    barrier = threading.Barrier(2)

    def attempt(_: int) -> str:
        try:
            barrier.wait(timeout=5)
            change_order_status(order=order, target=OrderStatus.CANCELLED, user=manager)
            return "ok"
        except ValidationError:
            return "rejected"
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, [1, 2]))

    assert sorted(results) == ["ok", "rejected"]

    order.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED
