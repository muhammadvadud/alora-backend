"""`GET /api/v1/analytics/dashboard/` — sotuv dashboard'i (16.8)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

import pytest
from django.utils import timezone
from rest_framework import status

from apps.chat.models import Conversation
from apps.common.choices import OrderStatus
from apps.orders.models import Order
from apps.orders.services import confirm_order
from apps.usage.models import UsageDaily
from apps.usage.selectors import get_sales_dashboard, resolve_period

pytestmark = pytest.mark.django_db

DASHBOARD_URL = "/api/v1/analytics/dashboard/"

# orders app'ining lokal fixture'lari (variant, draft_payload, create_order) qayta ishlatiladi.
pytest_plugins = ["tests.orders.conftest"]


def _sold(order: Order, manager: Any) -> Order:
    return confirm_order(order=order, user=manager)


def _conversation(tenant: Any, user: Any, order: Order | None = None) -> Conversation:
    return Conversation.objects.create(
        tenant=tenant, user=user, session_id=str(uuid.uuid4()), title="t", order=order
    )


class TestResolvePeriod:
    def test_day_week_month_custom(self):
        today = timezone.localdate()
        assert resolve_period("day") == (today, today)
        assert resolve_period("week")[0] == today - dt.timedelta(days=today.weekday())
        assert resolve_period("month")[0] == today.replace(day=1)
        custom_from = today - dt.timedelta(days=10)
        assert resolve_period("custom", date_from=custom_from) == (custom_from, today)


class TestDashboardSelector:
    def test_aggregates_orders_sales_and_conversations(
        self, tenant_db, employee, manager, create_order
    ):
        draft = create_order(employee)
        sold1 = _sold(create_order(employee), manager)
        sold2 = _sold(create_order(manager), manager)
        cancelled = create_order(employee)
        cancelled.status = OrderStatus.CANCELLED
        cancelled.save(update_fields=["status"])
        _conversation(tenant_db, employee, order=sold1)
        _conversation(tenant_db, employee)
        UsageDaily.objects.create(
            tenant=tenant_db,
            user=employee,
            date=timezone.localdate(),
            tokens=1200,
            cost_uzs=Decimal("3500.00"),
            messages_count=4,
            conversations_count=2,
        )

        data = get_sales_dashboard(tenant_db, period="day")

        assert data["orders"]["created"] == 4
        assert data["orders"]["sold"] == 2
        assert data["orders"]["draft"] == 1
        assert data["orders"]["cancelled"] == 1
        assert data["orders"]["in_progress"] == 2
        assert data["orders"]["by_status"] == {"draft": 1, "confirmed": 2, "cancelled": 1}

        # Qoralama va bekor qilingan sotuvga kirmaydi.
        expected_revenue = sold1.total + sold2.total
        assert Decimal(data["sales"]["revenue"]) == expected_revenue
        assert Decimal(data["sales"]["average_check"]) == (expected_revenue / 2).quantize(
            Decimal("0.01")
        )
        assert Decimal(data["sales"]["prepayment"]) == sold1.prepayment + sold2.prepayment
        assert (
            draft.total > 0 and Decimal(data["sales"]["revenue"]) < draft.total + expected_revenue
        )

        assert data["conversations"] == {"total": 2, "with_order": 1, "conversion_rate": "50.00"}
        assert data["ai"] == {"tokens": 1200, "cost_uzs": "3500.00", "messages": 4}

        # Top mahsulot — fixture varianti, ikki sotilgan buyurtmada.
        assert len(data["top_products"]) == 1
        top = data["top_products"][0]
        assert top["sku"] == "P-V1-RED" and top["orders"] == 2
        assert Decimal(top["revenue"]) > 0

        by_user = {row["user_id"]: row for row in data["by_user"]}
        assert by_user[str(employee.id)]["orders"] == 3
        assert by_user[str(employee.id)]["sold"] == 1
        assert by_user[str(manager.id)]["sold"] == 1

        assert len(data["daily"]) == 1
        assert data["daily"][0]["orders_created"] == 4
        assert data["daily"][0]["orders_sold"] == 2

        assert data["previous"]["orders_created"] == 0
        assert data["previous"]["orders_change_pct"] is None

    def test_previous_period_comparison(self, tenant_db, employee, manager, create_order):
        old = _sold(create_order(employee), manager)
        yesterday = timezone.now() - dt.timedelta(days=1)
        Order.objects.filter(pk=old.pk).update(created_at=yesterday)
        _sold(create_order(employee), manager)
        _sold(create_order(employee), manager)

        data = get_sales_dashboard(tenant_db, period="day")

        assert data["orders"]["created"] == 2
        assert data["previous"]["orders_created"] == 1
        assert data["previous"]["orders_change_pct"] == "100.00"
        assert data["previous"]["revenue_change_pct"] == "100.00"

    def test_custom_period_fills_empty_days(self, tenant_db):
        today = timezone.localdate()
        data = get_sales_dashboard(
            tenant_db, period="custom", date_from=today - dt.timedelta(days=2), date_to=today
        )
        assert [d["date"] for d in data["daily"]] == [
            (today - dt.timedelta(days=i)).isoformat() for i in (2, 1, 0)
        ]
        assert all(d["revenue"] == "0.00" for d in data["daily"])

    def test_other_tenant_is_isolated(self, tenant_db, employee, manager, create_order):
        from apps.common.factories import TenantFactory

        _sold(create_order(employee), manager)
        assert get_sales_dashboard(TenantFactory(), period="day")["orders"]["created"] == 0


class TestDashboardAPI:
    def test_manager_gets_all_blocks(self, auth_client, manager, employee, create_order):
        _sold(create_order(employee), manager)
        response = auth_client(manager).get(DASHBOARD_URL, {"period": "week"})
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert set(body) == {
            "period",
            "date_from",
            "date_to",
            "orders",
            "sales",
            "conversations",
            "ai",
            "top_products",
            "by_user",
            "daily",
            "previous",
        }
        assert body["period"] == "week"
        assert body["orders"]["sold"] == 1

    def test_employee_forbidden(self, auth_client, employee):
        assert auth_client(employee).get(DASHBOARD_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_custom_requires_date_from(self, auth_client, manager):
        response = auth_client(manager).get(DASHBOARD_URL, {"period": "custom"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "date_from" in response.json()["errors"]

    def test_date_to_before_date_from_rejected(self, auth_client, manager):
        response = auth_client(manager).get(
            DASHBOARD_URL,
            {"period": "custom", "date_from": "2026-09-10", "date_to": "2026-09-01"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "date_to" in response.json()["errors"]
