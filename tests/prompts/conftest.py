"""System prompt testlari uchun lokal fixture'lar (tests/conftest.py ga tegilmaydi)."""

from __future__ import annotations

from typing import Any

import pytest

from apps.common.factories import AdminFactory, EmployeeFactory, ManagerFactory, TenantFactory


@pytest.fixture()
def tenant_db(db: Any) -> Any:
    """DB da saqlangan tenant."""

    return TenantFactory()


@pytest.fixture()
def admin(tenant_db: Any) -> Any:
    """DB da saqlangan admin foydalanuvchi."""

    return AdminFactory(tenant=tenant_db)


@pytest.fixture()
def manager(tenant_db: Any) -> Any:
    """DB da saqlangan menejer foydalanuvchi."""

    return ManagerFactory(tenant=tenant_db)


@pytest.fixture()
def employee(tenant_db: Any) -> Any:
    """DB da saqlangan xodim foydalanuvchi."""

    return EmployeeFactory(tenant=tenant_db)


@pytest.fixture()
def auth_client(client: Any) -> Any:
    """Berilgan foydalanuvchi uchun JWT Bearer bilan sozlangan APIClient qaytaradi."""

    from rest_framework_simplejwt.tokens import RefreshToken

    def _auth(user: Any) -> Any:
        token = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    return _auth
