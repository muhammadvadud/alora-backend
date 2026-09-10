"""UsageRecord, UsageDaily va UsageLimit modellari testlari."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.common.factories import EmployeeFactory, TenantFactory
from apps.usage.models import UsageDaily, UsageLimit, UsageRecord


@pytest.fixture()
def employee(db):
    tenant = TenantFactory()
    return EmployeeFactory(tenant=tenant)


class TestUsageRecord:
    def test_created_at_indexed(self):
        field = UsageRecord._meta.get_field("created_at")
        assert field.db_index is True

    def test_conversation_nullable(self, employee):
        record = UsageRecord.objects.create(
            tenant=employee.tenant,
            user=employee,
            conversation=None,
            provider="deepseek",
            model="deepseek-v4-pro",
        )
        assert record.conversation is None

    def test_decimal_cost_fields(self, employee):
        record = UsageRecord.objects.create(
            tenant=employee.tenant,
            user=employee,
            cost_usd=Decimal("1.25"),
            cost_uzs=Decimal("16000.00"),
        )
        record.refresh_from_db()
        assert isinstance(record.cost_usd, Decimal)
        assert isinstance(record.cost_uzs, Decimal)

    def test_tool_calls_json_default(self, employee):
        record = UsageRecord.objects.create(tenant=employee.tenant, user=employee)
        assert record.tool_calls == []


class TestUsageDaily:
    def test_unique_user_date(self, employee):
        UsageDaily.objects.create(tenant=employee.tenant, user=employee, date="2026-09-08")
        with pytest.raises(IntegrityError):
            UsageDaily.objects.create(tenant=employee.tenant, user=employee, date="2026-09-08")

    def test_rollup_counts(self, employee):
        daily = UsageDaily.objects.create(
            tenant=employee.tenant,
            user=employee,
            date="2026-09-08",
            tokens=1234,
            cost_uzs=Decimal("15000.00"),
            messages_count=7,
            conversations_count=3,
        )
        assert daily.tokens == 1234
        assert daily.messages_count == 7
        assert daily.conversations_count == 3


class TestUsageLimit:
    def test_user_or_role_required(self, employee):
        with pytest.raises(IntegrityError):
            UsageLimit.objects.create(period="daily")

    def test_user_and_role_cannot_coexist(self, employee):
        with pytest.raises(IntegrityError):
            UsageLimit.objects.create(user=employee, role="employee", period="daily")

    def test_defaults(self, employee):
        limit = UsageLimit.objects.create(user=employee, period="daily")
        assert limit.is_unlimited is False
        assert limit.on_exceed == "block"
        assert limit.is_active is True

    def test_period_choices(self):
        values = {choice[0] for choice in UsageLimit._meta.get_field("period").choices}
        assert {"daily", "monthly"} <= values

    def test_unlimited_flag(self, employee):
        limit = UsageLimit.objects.create(user=employee, period="monthly", is_unlimited=True)
        assert limit.is_unlimited is True
