"""Usage statistika va analitika API testlari."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status

from apps.common.factories import AdminFactory, EmployeeFactory, ManagerFactory, TenantFactory
from apps.usage.models import UsageDaily, UsageRecord

USAGE_SUMMARY_URL = "/api/v1/usage/summary/"
USAGE_BY_USER_URL = "/api/v1/usage/by-user/"
USAGE_CONVERSATIONS_URL = "/api/v1/usage/conversations/"
ANALYTICS_CONVERSION_URL = "/api/v1/analytics/conversion/"


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


class TestUsagePermissions:
    @pytest.mark.parametrize(
        "url",
        [USAGE_SUMMARY_URL, USAGE_BY_USER_URL, USAGE_CONVERSATIONS_URL, ANALYTICS_CONVERSION_URL],
    )
    def test_employee_cannot_access(self, auth_client, employee, url):
        client = auth_client(employee)
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_access_summary(self, auth_client, manager):
        client = auth_client(manager)
        response = client.get(USAGE_SUMMARY_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access(self, auth_client, admin):
        client = auth_client(admin)
        assert client.get(USAGE_SUMMARY_URL).status_code == status.HTTP_200_OK
        assert client.get(USAGE_BY_USER_URL).status_code == status.HTTP_200_OK
        assert client.get(USAGE_CONVERSATIONS_URL).status_code == status.HTTP_200_OK
        assert client.get(ANALYTICS_CONVERSION_URL).status_code == status.HTTP_200_OK


class TestUsageSummary:
    def test_summary_reads_from_usage_daily_not_raw(self, auth_client, manager, employee):
        today = timezone.localdate()
        UsageDaily.objects.create(
            tenant=manager.tenant,
            user=employee,
            date=today,
            tokens=100,
            cost_uzs=Decimal("5000.00"),
            messages_count=5,
            conversations_count=2,
        )
        # Xom yozuv summaga ta'sir qilmasligi kerak
        UsageRecord.objects.create(
            tenant=manager.tenant, user=employee, prompt_tokens=999, completion_tokens=999
        )

        client = auth_client(manager)
        response = client.get(USAGE_SUMMARY_URL, {"period": "day"})
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["tokens"] == 100
        assert data["cost_uzs"] == "5000.00"
        assert data["messages"] == 5
        assert data["conversations"] == 2

    def test_summary_filter_by_user(self, auth_client, manager, employee):
        today = timezone.localdate()
        other = EmployeeFactory(tenant=manager.tenant)
        UsageDaily.objects.create(
            tenant=manager.tenant, user=employee, date=today, tokens=50, messages_count=2
        )
        UsageDaily.objects.create(
            tenant=manager.tenant, user=other, date=today, tokens=300, messages_count=9
        )

        client = auth_client(manager)
        response = client.get(USAGE_SUMMARY_URL, {"period": "day", "user": str(employee.id)})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tokens"] == 50

    def test_week_and_month_aggregate(self, auth_client, manager, employee):
        today = timezone.localdate()
        UsageDaily.objects.create(tenant=manager.tenant, user=employee, date=today, tokens=10)
        response = auth_client(manager).get(USAGE_SUMMARY_URL, {"period": "week"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tokens"] == 10
        response = auth_client(manager).get(USAGE_SUMMARY_URL, {"period": "month"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tokens"] == 10


class TestUsageByUser:
    def test_ranking_ordered_by_cost(self, auth_client, manager, employee):
        today = timezone.localdate()
        worker_a = EmployeeFactory(tenant=manager.tenant, full_name="Zafar")
        worker_b = EmployeeFactory(tenant=manager.tenant, full_name="Aliya")
        UsageDaily.objects.create(
            tenant=manager.tenant,
            user=worker_a,
            date=today,
            tokens=100,
            cost_uzs=Decimal("1000.00"),
        )
        UsageDaily.objects.create(
            tenant=manager.tenant, user=worker_b, date=today, tokens=50, cost_uzs=Decimal("2000.00")
        )

        response = auth_client(manager).get(USAGE_BY_USER_URL, {"period": "day"})
        assert response.status_code == status.HTTP_200_OK
        rows = response.data
        assert rows[0]["user_id"] == str(worker_b.id)
        assert rows[0]["cost_uzs"] == "2000.00"


class TestUsageConversations:
    def test_expensive_conversations(self, auth_client, manager, employee):
        import uuid as uuid_lib

        conv_a = uuid_lib.uuid4()
        conv_b = uuid_lib.uuid4()
        for _ in range(3):
            UsageRecord.objects.create(
                tenant=manager.tenant,
                user=employee,
                conversation=conv_b,
                cost_uzs=Decimal("3000.00"),
            )
        UsageRecord.objects.create(
            tenant=manager.tenant, user=employee, conversation=conv_a, cost_uzs=Decimal("500.00")
        )

        response = auth_client(manager).get(USAGE_CONVERSATIONS_URL)
        assert response.status_code == status.HTTP_200_OK
        rows = response.data
        assert len(rows) == 2
        assert rows[0]["conversation_id"] == str(conv_b)
        assert rows[0]["cost_uzs"] == "9000.00"


class TestAnalyticsConversion:
    def test_returns_empty_when_models_missing(self, auth_client, manager):
        response = auth_client(manager).get(ANALYTICS_CONVERSION_URL)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["total_conversations"] == 0
        assert data["with_order"] == 0
        assert data["conversion_rate"] == "0.00"
