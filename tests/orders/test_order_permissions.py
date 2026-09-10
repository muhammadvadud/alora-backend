"""Buyurtma ruxsatlari testlari (8.17)."""

from __future__ import annotations

import pytest
from rest_framework import status

from apps.common.factories import TenantFactory
from apps.orders.services import create_order_from_draft

ORDERS_URL = "/api/v1/orders/"


class TestEmployeeVisibility:
    """8.17 — employee faqat o'z buyurtmasini ko'radi."""

    def test_employee_sees_only_own_orders(
        self, auth_client, employee, other_employee, draft_payload
    ):
        create_order_from_draft(payload=draft_payload(), user=employee)
        create_order_from_draft(
            payload=draft_payload(customer_phone="+998901234001"), user=other_employee
        )

        response = auth_client(employee).get(ORDERS_URL)
        assert response.status_code == status.HTTP_200_OK
        numbers = [row["number"] for row in response.data["results"]]
        assert len(numbers) == 1

    def test_employee_cannot_view_others_order(
        self, auth_client, employee, other_employee, draft_payload
    ):
        order, _ = create_order_from_draft(
            payload=draft_payload(customer_phone="+998901234001"), user=other_employee
        )
        response = auth_client(employee).get(f"{ORDERS_URL}{order.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_cannot_list(self, api_client):
        assert api_client.get(ORDERS_URL).status_code == status.HTTP_401_UNAUTHORIZED


class TestManagerVisibility:
    """8.17 — manager tenant ichidagi barcha buyurtmalarni ko'radi."""

    def test_manager_sees_all_tenant_orders(
        self, auth_client, manager, employee, other_employee, draft_payload
    ):
        create_order_from_draft(payload=draft_payload(), user=employee)
        create_order_from_draft(
            payload=draft_payload(customer_phone="+998901234001"), user=other_employee
        )

        response = auth_client(manager).get(ORDERS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_manager_cannot_access_other_tenant(self, auth_client, manager, emperor, draft_payload):
        order, _ = create_order_from_draft(payload=draft_payload(), user=emperor)
        response = auth_client(manager).get(f"{ORDERS_URL}{order.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.fixture()
def emperor():
    """Boshqa tenantdagi foydalanuvchi (tenantlararo ko'rinmaslik uchun)."""

    from apps.common.factories import EmployeeFactory

    return EmployeeFactory(tenant=TenantFactory())
