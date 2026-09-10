from __future__ import annotations

from unittest.mock import patch

from apps.pricing.apps import check_single_tenant_assumption


def test_global_pricing_check_bitta_tenantda_ogohlantirmaydi() -> None:
    """Bitta tenant bo'lsa global pricing sozlamalari qabul qilinadi."""

    with patch("apps.accounts.models.Tenant.objects.count", return_value=1):
        assert check_single_tenant_assumption(None) == []


def test_global_pricing_check_ikkita_tenantda_ogohlantiradi() -> None:
    """Ikkinchi tenant global pricing qarorini qayta ko'rib chiqishni talab qiladi."""

    with patch("apps.accounts.models.Tenant.objects.count", return_value=2):
        warnings = check_single_tenant_assumption(None)

    assert len(warnings) == 1
    assert warnings[0].id == "pricing.W001"
