"""Chat rate limit testlari (`check_rate_limit`, rules.md §12.4)."""

from __future__ import annotations

from unittest import mock

import pytest
from rest_framework.exceptions import Throttled

from apps.chat.services import check_rate_limit
from apps.common.choices import UserRole

pytestmark = pytest.mark.django_db


def _user(role: str) -> mock.Mock:
    return mock.Mock(id=f"user-{role}", role=role)


def _check(role: str, count: int) -> None:
    """`cache.incr` `count` ni qaytaradigan holda limitni tekshiradi."""

    with (
        mock.patch("apps.chat.services.cache.add", return_value=True),
        mock.patch("apps.chat.services.cache.incr", return_value=count),
    ):
        check_rate_limit(_user(role))


class TestFallbackLimits:
    """CalcRule yo'q bo'lgandagi zaxira (fallback) limitlar."""

    def test_employee_fallback_is_20(self) -> None:
        """Xodim zaxirasi 20 — tez yozadigan sotuvchi 429 olmasligi uchun."""
        _check(UserRole.EMPLOYEE, 20)  # chegarada — o'tadi

    def test_employee_fallback_throttles_over_20(self) -> None:
        with pytest.raises(Throttled):
            _check(UserRole.EMPLOYEE, 21)

    def test_manager_fallback_is_30(self) -> None:
        _check(UserRole.MANAGER, 30)
        with pytest.raises(Throttled):
            _check(UserRole.MANAGER, 31)

    def test_admin_fallback_is_100(self) -> None:
        _check(UserRole.ADMIN, 100)
        with pytest.raises(Throttled):
            _check(UserRole.ADMIN, 101)

    def test_unknown_role_uses_employee_fallback(self) -> None:
        """Noma'lum rol xodim chegarasiga tushadi (20), 10 emas."""
        _check("gost", 20)
        with pytest.raises(Throttled):
            _check("gost", 21)


class TestCalcRulePrecedence:
    """`CalcRule.chat_rate_limit_<role>` bazadagi qiymat ustun bo'lishi saqlanadi."""

    def test_calc_rule_wins_over_fallback(self) -> None:
        from apps.pricing.models import CalcRule

        CalcRule.objects.create(key="chat_rate_limit_employee", value=3)

        _check(UserRole.EMPLOYEE, 3)
        with pytest.raises(Throttled):
            _check(UserRole.EMPLOYEE, 4)

    def test_calc_rule_above_fallback_still_applies(self) -> None:
        """Bazadagi katta limit fallback'ni almashtiradi."""
        from apps.pricing.models import CalcRule

        CalcRule.objects.create(key="chat_rate_limit_employee", value=50)

        _check(UserRole.EMPLOYEE, 50)
        with pytest.raises(Throttled):
            _check(UserRole.EMPLOYEE, 51)

    def test_rule_for_other_role_does_not_affect(self) -> None:
        """Faqat o'z rolining kaliti hisobga olinadi."""
        from apps.pricing.models import CalcRule

        CalcRule.objects.create(key="chat_rate_limit_manager", value=2)

        _check(UserRole.EMPLOYEE, 20)
        with pytest.raises(Throttled):
            _check(UserRole.MANAGER, 3)
