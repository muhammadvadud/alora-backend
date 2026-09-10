"""Buyurtma service'lari uchun sinovlar (8.7, 8.8, 8.16, 8.18)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.common.choices import OrderStatus
from apps.orders.models import OrderCurtainPart, OrderItem
from apps.orders.services import (
    change_order_status,
    confirm_order,
    order_lines_total,
    recalculate_order,
)


class TestOrderStatusMachine:
    """8.8/8.13 — status o'tishlari."""

    def test_happy_path_transitions(self, create_order, employee, manager):
        order = create_order(employee)
        for target in (
            OrderStatus.CONFIRMED,
            OrderStatus.MEASURING,
            OrderStatus.PRODUCTION,
            OrderStatus.READY,
            OrderStatus.INSTALLING,
            OrderStatus.COMPLETED,
        ):
            change_order_status(order=order, target=target, user=manager)
            assert order.status == target

    def test_completed_is_terminal(self, create_order, employee, manager):
        order = create_order(employee)
        sequence = (
            OrderStatus.CONFIRMED,
            OrderStatus.MEASURING,
            OrderStatus.PRODUCTION,
            OrderStatus.READY,
            OrderStatus.INSTALLING,
            OrderStatus.COMPLETED,
        )
        for target in sequence:
            change_order_status(order=order, target=target, user=manager)
        with pytest.raises(ValidationError):
            change_order_status(order=order, target=OrderStatus.PRODUCTION, user=manager)

    def test_cancelled_allowed_until_terminal(self, create_order, employee, manager):
        order = create_order(employee)
        change_order_status(order=order, target=OrderStatus.CONFIRMED, user=manager)
        change_order_status(order=order, target=OrderStatus.CANCELLED, user=manager)
        assert order.status == OrderStatus.CANCELLED

    def test_invalid_transition_message_is_uzbek(self, create_order, employee):
        order = create_order(employee)
        with pytest.raises(ValidationError) as exc:
            change_order_status(order=order, target=OrderStatus.COMPLETED, user=employee)
        message = exc.value.message_dict["status"][0]
        assert "holatdan" in message
        assert "holatga" in message
        assert "ruxsat etilmagan" in message

    def test_note_and_action_date_saved(self, create_order, employee, manager):
        order = create_order(employee)
        change_order_status(
            order=order,
            target=OrderStatus.CONFIRMED,
            user=manager,
            note="Telefon tasdiqladi",
            action_date=date(2026, 9, 21),
        )
        order.refresh_from_db()
        assert order.note == "Telefon tasdiqladi"
        assert str(order.deadline_date) == "2026-09-21"
        assert order.confirmed_by_id == manager.pk


class TestConfirmOrder:
    """8.12 — confirm service."""

    def test_confirm_sets_fields(self, create_order, employee):
        order = create_order(employee)
        confirm_order(order=order, user=employee)
        order.refresh_from_db()
        assert order.status == OrderStatus.CONFIRMED
        assert order.confirmed_by_id == employee.pk
        assert order.confirmed_at is not None

    def test_confirm_only_from_draft(self, create_order, employee):
        order = create_order(employee)
        confirm_order(order=order, user=employee)
        with pytest.raises(ValidationError):
            confirm_order(order=order, user=employee)


class TestPriceSnapshot:
    """8.7 — snapshot tamoyili."""

    def test_katalog_narxi_keyin_ozgarsa_buyurtma_ozgarmaydi(
        self, auth_client, employee, variant, create_order
    ):
        order = create_order(employee)
        part = OrderCurtainPart.objects.get(measurement__order=order)
        assert part.price_per_sqm == Decimal("20000.00")

        variant.price = "99999.00"
        variant.save()
        part.refresh_from_db()
        assert part.price_per_sqm == Decimal("20000.00")
        assert str(part.total) == "48000.00"
        assert str(order.total) == "78000.00"

    def test_name_snapshot_kept_for_services(self, create_order, employee):
        order = create_order(employee)
        sewing = OrderItem.objects.get(order=order, service_key="sewing")
        assert sewing.name_snapshot == "Tikuv"
        assert str(sewing.unit_price) == "12500.00"


class TestOrderSums:
    """8.18 — qatorlar va jami summalar mosligi."""

    def test_lines_equal_subtotal_and_total(self, create_order, employee):
        order = create_order(employee)
        assert order_lines_total(order) == order.subtotal == order.total


class TestRecalculateOrder:
    """8.16 — recalculate_order."""

    def test_recalculate_uses_live_variant_price(self, create_order, employee, variant):
        order = create_order(employee)
        assert str(order.total) == "78000.00"

        variant.price = "30000.00"
        variant.save()
        result = recalculate_order(order=order, user_role=employee.role)

        order.refresh_from_db()
        assert str(order.total) == "102000.00"
        assert str(order.subtotal) == "102000.00"
        assert result["subtotal"] == result["total"]
