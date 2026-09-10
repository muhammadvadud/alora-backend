"""Pytest umumiy fixture'lari."""

from __future__ import annotations

from typing import Any

import pytest

from apps.common.factories import AdminFactory, EmployeeFactory, ManagerFactory, TenantFactory


@pytest.fixture()
def api_client() -> Any:
    """DRF APIClient instance."""

    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture()
def client() -> Any:
    """DRF APIClient — pytest-django klassik Client o'rniga.

    Katalog va account testlari `client.credentials(HTTP_AUTHORIZATION=...)`
    ishlatgani uchun APIClient kerak.
    """

    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture()
def auth_client(client: Any) -> Any:
    """Berilgan foydalanuvchi uchun JWT Bearer bilan sozlangan APIClient qaytaradi."""

    from rest_framework_simplejwt.tokens import RefreshToken

    def _auth(user: Any) -> Any:
        token = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    return _auth


@pytest.fixture()
def tenant() -> Any:
    """Tenant uchun umumiy test obyekt."""

    return TenantFactory.build()


@pytest.fixture()
def employee_user(tenant: Any) -> Any:
    """Xodim foydalanuvchi testi uchun obyekt."""

    return EmployeeFactory.build(tenant=tenant)


@pytest.fixture()
def manager_user(tenant: Any) -> Any:
    """Menejer foydalanuvchi testi uchun obyekt."""

    return ManagerFactory.build(tenant=tenant)


@pytest.fixture()
def admin_user(tenant: Any) -> Any:
    """Admin foydalanuvchi testi uchun obyekt."""

    return AdminFactory.build(tenant=tenant)


@pytest.fixture
def pricing_defaults(db):
    """Narx sozlamalari seed'ini kafolatlaydi.

    `CalcRule`, `ServicePrice`, `DiscountPolicy` va `OrderDefaults` migratsiya
    seed'idan (`pricing.0002_seed_defaults`) keladi. `transaction=True` bilan
    ishlaydigan testlar bazani to'liq tozalagani uchun bu satrlar yo'qoladi va
    keyingi transaksiyali test "Sozlama topilmadi" xatosiga uchraydi.

    Seed ma'lumoti bu yerda takrorlanmaydi — migratsiyaning o'z funksiyasi
    chaqiriladi, ya'ni seed o'zgarsa fixture avtomatik mos qoladi.
    """

    from importlib import import_module

    from django.apps import apps as django_apps

    migration = import_module("apps.pricing.migrations.0002_seed_defaults")
    migration.forwards(django_apps, None)
