"""Usage Celery tasklari testlari — 13.1, 13.4, 13.6 va 13.9."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.common.choices import UsagePeriod
from apps.usage.models import UsageDaily, UsageLimit, UsageRecord
from apps.usage.tasks import check_limits_and_notify, daily_usage_rollup, save_usage_record

pytestmark = pytest.mark.django_db


class TestSaveUsageRecord:
    """13.1 — `save_usage_record` taski."""

    def _payload(self, employee, **overrides):
        payload = {
            "user_id": str(employee.id),
            "tenant_id": str(employee.tenant_id),
            "conversation_id": str(uuid.uuid4()),
            "message_id": str(uuid.uuid4()),
            "provider": "openai",
            "model": "gpt-4o-mini",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "tool_calls_json": '[{"name": "search"}]',
            "cost_usd": 0.01,
            "cost_uzs": 130.5,
        }
        payload.update(overrides)
        return payload

    def test_creates_record_with_parsed_fields(self, employee):
        record = save_usage_record(**self._payload(employee))
        assert record is not None
        assert record.user_id == employee.id
        assert record.provider == "openai"
        assert record.prompt_tokens == 100
        assert record.tool_calls == [{"name": "search"}]
        assert record.cost_usd == Decimal("0.01")
        assert record.cost_uzs == Decimal("130.50")

    def test_idempotent_with_message_id(self, employee):
        """Bir xil message_id ikki marta kelsa bitta yozuv qoladi (13.9)."""
        payload = self._payload(employee)
        first = save_usage_record(**payload)
        second = save_usage_record(**payload)
        assert first.id == second.id
        assert UsageRecord.objects.filter(message_id=first.message_id).count() == 1

    def test_unknown_user_is_noop(self):
        result = save_usage_record(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            message_id=str(uuid.uuid4()),
        )
        assert result is None
        assert UsageRecord.objects.count() == 0

    def test_unknown_tenant_is_noop(self, employee):
        result = save_usage_record(
            user_id=str(employee.id),
            tenant_id=str(uuid.uuid4()),
            message_id=str(uuid.uuid4()),
        )
        assert result is None
        assert UsageRecord.objects.count() == 0


class TestDailyUsageRollup:
    """13.4 — `daily_usage_rollup` taski."""

    @staticmethod
    def _local_datetime(year: int, month: int, day: int, hour: int = 10) -> dt.datetime:
        return dt.datetime(year, month, day, hour, tzinfo=timezone.get_current_timezone())

    def _create_record(self, employee, created_at, *, conversation=None, prompt_tokens=10, cost="100.00"):
        record = UsageRecord.objects.create(
            tenant=employee.tenant,
            user=employee,
            conversation=conversation,
            prompt_tokens=prompt_tokens,
            cost_uzs=Decimal(cost),
        )
        UsageRecord.objects.filter(pk=record.pk).update(created_at=created_at)
        return record

    def test_aggregates_usage_into_daily(self, employee):
        target_date = timezone.localdate()
        start = self._local_datetime(target_date.year, target_date.month, target_date.day)
        self._create_record(employee, start, conversation=uuid.uuid4(), prompt_tokens=100, cost="1200.00")
        self._create_record(employee, start, conversation=uuid.uuid4(), prompt_tokens=15, cost="800.00")

        updated = daily_usage_rollup(date=str(target_date))

        assert updated == 1
        daily = UsageDaily.objects.get(user=employee, date=target_date)
        assert daily.tokens == 115
        assert daily.cost_uzs == Decimal("2000.00")
        assert daily.messages_count == 2
        assert daily.conversations_count == 2

    def test_idempotent(self, employee):
        """Rollup ikki marta ishlasa bitta to'g'ri yozuv qoladi (13.9)."""
        target_date = timezone.localdate()
        start = self._local_datetime(target_date.year, target_date.month, target_date.day)
        self._create_record(employee, start, prompt_tokens=10)

        daily_usage_rollup(date=str(target_date))
        daily_usage_rollup(date=str(target_date))

        assert UsageDaily.objects.filter(user=employee, date=target_date).count() == 1
        daily = UsageDaily.objects.get(user=employee, date=target_date)
        assert daily.tokens == 10

    def test_defaults_to_yesterday(self, employee):
        yesterday = timezone.localdate() - dt.timedelta(days=1)
        start = self._local_datetime(yesterday.year, yesterday.month, yesterday.day)
        self._create_record(employee, start, prompt_tokens=7)

        updated = daily_usage_rollup()

        assert updated == 1
        assert UsageDaily.objects.filter(user=employee, date=yesterday).exists()

    def test_excludes_other_days(self, employee):
        today = timezone.localdate()
        self._create_record(employee, self._local_datetime(today.year, today.month, today.day), prompt_tokens=5)

        other_day = today - dt.timedelta(days=10)
        self._create_record(employee, self._local_datetime(other_day.year, other_day.month, other_day.day), prompt_tokens=99)

        updated = daily_usage_rollup(date=str(today))

        assert updated == 1
        assert UsageDaily.objects.get(user=employee, date=today).tokens == 5


class FakeLogger:
    """structlog logger o'rnini bosuvchi oddiy ob'ekt."""

    def __init__(self) -> None:
        self.warnings: list[tuple[str, dict]] = []

    def warning(self, event: str, **kwargs) -> None:
        self.warnings.append((event, kwargs))

    def info(self, *args, **kwargs) -> None:
        pass


class TestCheckLimitsAndNotify:
    """13.6 — `check_limits_and_notify` taski."""

    def test_exceeded_limit_logs_warning(self, employee, monkeypatch):
        UsageLimit.objects.create(user=employee, period=UsagePeriod.DAILY, max_tokens=10)
        UsageRecord.objects.create(tenant=employee.tenant, user=employee, prompt_tokens=100)

        from apps.usage import tasks as usage_tasks

        fake_logger = FakeLogger()
        monkeypatch.setattr(usage_tasks, "logger", fake_logger)

        result = check_limits_and_notify()

        assert result == {"checked": 1, "blocked": 1}
        assert len(fake_logger.warnings) == 1
        event, kwargs = fake_logger.warnings[0]
        assert event == "usage_limit_exceeded"
        assert kwargs["user_id"] == str(employee.id)
        assert "Tokenlar" in kwargs["reason"]

    def test_within_limit_no_warning(self, employee, monkeypatch):
        UsageLimit.objects.create(user=employee, period=UsagePeriod.DAILY, max_tokens=1000)
        UsageRecord.objects.create(tenant=employee.tenant, user=employee, prompt_tokens=5)

        from apps.usage import tasks as usage_tasks

        fake_logger = FakeLogger()
        monkeypatch.setattr(usage_tasks, "logger", fake_logger)

        result = check_limits_and_notify()

        assert result == {"checked": 1, "blocked": 0}
        assert fake_logger.warnings == []

    def test_role_limit_checked(self, employee, monkeypatch):
        UsageLimit.objects.create(role=employee.role, period=UsagePeriod.DAILY, max_tokens=10)
        UsageRecord.objects.create(tenant=employee.tenant, user=employee, prompt_tokens=100)

        from apps.usage import tasks as usage_tasks

        fake_logger = FakeLogger()
        monkeypatch.setattr(usage_tasks, "logger", fake_logger)

        result = check_limits_and_notify()

        assert result == {"checked": 1, "blocked": 1}
        assert fake_logger.warnings[0][1]["user_id"] == str(employee.id)


class TestRetryConfiguration:
    """13.9 — usage tasklarida retry sozlamalari borligi."""

    def test_usage_tasks_have_retry_config(self):
        for task in (save_usage_record, daily_usage_rollup, check_limits_and_notify):
            assert task.max_retries == 3
            assert task.retry_backoff is True
            assert Exception in task.autoretry_for