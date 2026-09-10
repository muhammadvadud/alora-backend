"""Jamoa boshqaruvi (manager paneli) testlari — ruxsatlar matritsasi."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.common.factories import AdminFactory, EmployeeFactory, ManagerFactory, TenantFactory

User = get_user_model()

TEAM_LIST_URL = "/api/v1/team/employees/"


@pytest.fixture()
def tenant_db(db):
    return TenantFactory()


@pytest.fixture()
def manager(tenant_db):
    return ManagerFactory(tenant=tenant_db)


@pytest.fixture()
def admin(tenant_db):
    return AdminFactory(tenant=tenant_db)


@pytest.fixture()
def employee(tenant_db):
    return EmployeeFactory(tenant=tenant_db)


@pytest.fixture()
def auth_client(client):
    from rest_framework_simplejwt.tokens import RefreshToken

    def _auth(user):
        token = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    return _auth


class TestPermissions:
    def test_employee_cannot_list_team(self, auth_client, employee):
        response = auth_client(employee).get(TEAM_LIST_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_create_employee(self, auth_client, employee):
        response = auth_client(employee).post(TEAM_LIST_URL, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_patch_employee(self, auth_client, employee, manager):
        response = auth_client(employee).patch(
            f"{TEAM_LIST_URL}{manager.id}/", {"is_active": False}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_set_limit(self, auth_client, employee, manager):
        response = auth_client(employee).post(
            f"{TEAM_LIST_URL}{manager.id}/limit/", {"is_unlimited": True}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_view_conversations(self, auth_client, employee, manager):
        response = auth_client(employee).get(f"{TEAM_LIST_URL}{manager.id}/conversations/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_list_team(self, auth_client, manager):
        response = auth_client(manager).get(TEAM_LIST_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_list_team(self, auth_client, admin):
        response = auth_client(admin).get(TEAM_LIST_URL)
        assert response.status_code == status.HTTP_200_OK


class TestEmployeeManagement:
    def test_list_includes_today_activity(self, auth_client, manager, employee):
        from django.utils import timezone

        from apps.usage.models import UsageDaily

        UsageDaily.objects.create(
            tenant=manager.tenant,
            user=employee,
            date=timezone.localdate(),
            tokens=77,
            messages_count=3,
            conversations_count=1,
        )
        response = auth_client(manager).get(TEAM_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        rows = response.data
        target = next(row for row in rows if row["id"] == str(employee.id))
        assert target["today_tokens"] == 77
        assert target["today_messages"] == 3

    def test_manager_can_create_employee(self, auth_client, manager):
        response = auth_client(manager).post(
            TEAM_LIST_URL,
            {
                "phone": "+998901230000",
                "full_name": "Yangi Xodim",
                "password": "qattiq-parol-1",
                "role": "employee",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(phone="+998901230000").exists()

    def test_create_employee_assigns_tenant(self, auth_client, manager):
        response = auth_client(manager).post(
            TEAM_LIST_URL,
            {"phone": "+998901230001", "full_name": "Tenant Xodim", "password": "qattiq-parol-1"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        created = User.objects.get(phone="+998901230001")
        assert created.tenant_id == manager.tenant_id

    def test_manager_can_block_employee(self, auth_client, manager, employee):
        response = auth_client(manager).patch(
            f"{TEAM_LIST_URL}{employee.id}/", {"is_active": False}
        )
        assert response.status_code == status.HTTP_200_OK
        employee.refresh_from_db()
        assert employee.is_active is False

    def test_manager_can_change_role(self, auth_client, manager, employee):
        response = auth_client(manager).patch(f"{TEAM_LIST_URL}{employee.id}/", {"role": "manager"})
        assert response.status_code == status.HTTP_200_OK
        employee.refresh_from_db()
        assert employee.role == "manager"


class TestEmployeeLimit:
    def test_set_unlimited_limit(self, auth_client, manager, employee):
        response = auth_client(manager).post(
            f"{TEAM_LIST_URL}{employee.id}/limit/", {"is_unlimited": True}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["is_unlimited"] is True
        assert data["user_id"] == str(employee.id)

    def test_set_token_limit(self, auth_client, manager, employee):
        response = auth_client(manager).post(
            f"{TEAM_LIST_URL}{employee.id}/limit/",
            {"period": "daily", "max_tokens": 50000, "max_messages": 30, "on_exceed": "warn"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["max_tokens"] == 50000
        assert response.data["on_exceed"] == "warn"

    def test_limit_requires_valid_values(self, auth_client, manager, employee):
        response = auth_client(manager).post(
            f"{TEAM_LIST_URL}{employee.id}/limit/",
            {"period": "soatlik"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestEmployeeConversations:
    def test_returns_empty_when_conversation_model_missing(self, auth_client, manager, employee):
        response = auth_client(manager).get(f"{TEAM_LIST_URL}{employee.id}/conversations/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_manager_cannot_access_other_tenant(self, auth_client, manager):
        other_tenant = TenantFactory()
        outsider = EmployeeFactory(tenant=other_tenant)
        response = auth_client(manager).get(f"{TEAM_LIST_URL}{outsider.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
