"""Usage limit mantiqi va xarajat hisobi testlari."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.common.choices import OnExceed, UsagePeriod
from apps.common.factories import EmployeeFactory, TenantFactory
from apps.pricing.models import ModelPricing
from apps.usage.models import UsageRecord
from apps.usage.services import (
    UsageLimitExceeded,
    calculate_cost,
    check_usage_limit,
    enforce_usage_limit,
    get_user_period_usage,
    resolve_usage_limit,
    set_user_usage_limit,
)


@pytest.fixture()
def employee(db: None):
    tenant = TenantFactory()
    return EmployeeFactory(tenant=tenant)


@pytest.fixture()
def role_limit(db: None):
    from apps.usage.models import UsageLimit

    return UsageLimit.objects.create(
        role="employee",
        period=UsagePeriod.DAILY,
        max_messages=10,
        max_tokens=10_000,
        on_exceed=OnExceed.BLOCK,
    )


class TestResolveUsageLimit:
    def test_personal_limit_priority_over_role(self, employee, role_limit):
        from apps.usage.models import UsageLimit

        personal = UsageLimit.objects.create(
            user=employee, period=UsagePeriod.DAILY, max_messages=1, on_exceed=OnExceed.BLOCK
        )
        limit = resolve_usage_limit(employee)
        assert limit.id == personal.id

    def test_role_limit_when_no_personal(self, employee, role_limit):
        limit = resolve_usage_limit(employee)
        assert limit is not None
        assert limit.role == "employee"

    def test_no_limit_returns_none(self, employee):
        assert resolve_usage_limit(employee) is None

    def test_unlimited_personal_wins(self, employee, role_limit):
        from apps.usage.models import UsageLimit

        UsageLimit.objects.create(user=employee, period=UsagePeriod.DAILY, is_unlimited=True)
        limit = resolve_usage_limit(employee)
        assert limit.is_unlimited is True


class TestCheckUsageLimit:
    def test_role_limit_blocked_when_messages_exceeded(self, employee, role_limit):
        for _ in range(11):
            UsageRecord.objects.create(
                tenant=employee.tenant, user=employee, provider="test", model="test-model"
            )
        result = check_usage_limit(employee)
        assert result.blocked is True

    def test_unlimited_never_blocks(self, employee):
        set_user_usage_limit(employee, {"is_unlimited": True})
        for _ in range(50):
            UsageRecord.objects.create(
                tenant=employee.tenant, user=employee, provider="test", model="test-model"
            )
        result = check_usage_limit(employee)
        assert result.blocked is False

    def test_warn_mode_does_not_block(self, employee):
        from apps.usage.models import UsageLimit

        UsageLimit.objects.create(
            user=employee, period=UsagePeriod.DAILY, max_messages=1, on_exceed=OnExceed.WARN
        )
        UsageRecord.objects.create(
            tenant=employee.tenant, user=employee, provider="test", model="test-model"
        )
        result = check_usage_limit(employee)
        assert result.blocked is False

    def test_token_threshold_blocks(self, employee):

        set_user_usage_limit(employee, {"max_tokens": 100, "on_exceed": OnExceed.BLOCK})
        UsageRecord.objects.create(
            tenant=employee.tenant,
            user=employee,
            provider="test",
            model="test-model",
            prompt_tokens=150,
        )
        assert check_usage_limit(employee).blocked is True

    def test_cost_threshold_blocks(self, employee):

        set_user_usage_limit(
            employee, {"max_cost_uzs": Decimal("500.00"), "on_exceed": OnExceed.BLOCK}
        )
        UsageRecord.objects.create(
            tenant=employee.tenant,
            user=employee,
            provider="test",
            model="test-model",
            cost_uzs=Decimal("600.00"),
        )
        assert check_usage_limit(employee).blocked is True

    def test_no_limit_never_blocks(self, employee):
        assert check_usage_limit(employee).blocked is False


class TestEnforceUsageLimit:
    def test_raises_when_blocked(self, employee):
        set_user_usage_limit(employee, {"max_messages": 1, "on_exceed": OnExceed.BLOCK})
        UsageRecord.objects.create(
            tenant=employee.tenant, user=employee, provider="test", model="test-model"
        )
        with pytest.raises(UsageLimitExceeded) as exc_info:
            enforce_usage_limit(employee)
        assert exc_info.value.status_code == 429

    def test_no_raise_when_unlimited(self, employee):
        set_user_usage_limit(employee, {"is_unlimited": True})
        UsageRecord.objects.create(
            tenant=employee.tenant, user=employee, provider="test", model="test-model"
        )
        enforce_usage_limit(employee)


class TestPeriodUsage:
    def test_tokens_aggregated_for_period(self, employee):
        UsageRecord.objects.create(
            tenant=employee.tenant,
            user=employee,
            provider="test",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=20,
            cached_tokens=30,
            reasoning_tokens=40,
        )
        usage = get_user_period_usage(employee, UsagePeriod.DAILY)
        assert usage.tokens == 100
        assert usage.messages == 1


class TestSetUserUsageLimit:
    def test_is_unlimited_toggle(self, employee):
        limit = set_user_usage_limit(employee, {"is_unlimited": True})
        assert limit.is_unlimited is True
        assert limit.user_id == employee.id
        assert limit.role is None

    def test_updates_existing_limit(self, employee):
        first = set_user_usage_limit(employee, {"is_unlimited": True})
        second = set_user_usage_limit(employee, {"max_tokens": 50})
        assert second.id == first.id
        assert second.is_unlimited is True
        assert second.max_tokens == 50


class TestCalculateCost:
    @pytest.fixture()
    def pricing(self, db):
        return ModelPricing.objects.create(
            provider="deepseek",
            model="deepseek-v4-pro",
            input_per_1m=Decimal("0.50"),
            output_per_1m=Decimal("1.50"),
            cached_input_per_1m=Decimal("0.10"),
            stt_per_minute=Decimal("0.10"),
            tts_per_1k_chars=Decimal("0.02"),
            usd_to_uzs=Decimal("13000.00"),
        )

    def test_cost_usd_uzs_correct(self, pricing):
        usd, uzs = calculate_cost(
            "deepseek",
            "deepseek-v4-pro",
            prompt_tokens=1_000_000,
            completion_tokens=100_000,
            cached_tokens=500_000,
        )
        assert usd == Decimal("0.50") + Decimal("0.15") + Decimal("0.05")
        assert uzs == usd * Decimal("13000.00")

    def test_stt_tts_components(self, pricing):
        usd, _ = calculate_cost(
            "deepseek",
            "deepseek-v4-pro",
            prompt_tokens=0,
            completion_tokens=0,
            stt_seconds=60,
            tts_chars=1000,
        )
        assert usd == Decimal("0.10") + Decimal("0.02")

    def test_no_pricing_returns_zero(self, db):
        usd, uzs = calculate_cost("noma'lum", "noma'lum-model", prompt_tokens=100)
        assert usd == Decimal(0)
        assert uzs == Decimal(0)
