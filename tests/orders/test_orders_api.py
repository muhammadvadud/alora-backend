"""Buyurtma API testlari (8.9-8.15)."""

from __future__ import annotations

import re
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status

from apps.common.choices import OrderStatus
from apps.orders.models import Order, OrderCurtainPart, OrderItem
from apps.orders.services import order_lines_total

ORDERS_URL = "/api/v1/orders/"
ORDER_NUMBER_RE = re.compile(r"^ALR-\d{4}-\d{6}$")


class TestCreateOrder:
    """8.10 — POST /orders/ AI draft'idan buyurtma yaratish."""

    def test_employee_can_create_order_from_draft(self, auth_client, employee, draft_payload, variant):
        client = auth_client(employee)
        response = client.post(ORDERS_URL, draft_payload(), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        assert ORDER_NUMBER_RE.match(data["number"])
        assert data["status"] == OrderStatus.DRAFT
        assert data["subtotal"] == "78000.00"
        assert data["total"] == "78000.00"
        assert data["prepayment"] == "39000.00"
        assert data["balance"] == "39000.00"
        assert data["payment_status"] == "prepaid"
        assert data["customer_name"] == "Aziz Karimov"

        order = Order.objects.get(number=data["number"])
        assert order.user_id == employee.id
        assert order.tenant_id == employee.tenant_id

    def test_number_sequence_increments(self, auth_client, employee, draft_payload):
        client = auth_client(employee)
        first = client.post(ORDERS_URL, draft_payload(), format="json")
        second = client.post(ORDERS_URL, draft_payload(customer_phone="+998901234000"), format="json")
        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED
        codes = [first.data["number"], second.data["number"]]
        assert len(set(codes)) == 2
        assert Order.objects.filter(number__in=codes).count() == 2

    def test_snapshot_prices_saved_from_calculator(self, auth_client, employee, draft_payload):
        client = auth_client(employee)
        response = client.post(ORDERS_URL, draft_payload(), format="json")
        order = Order.objects.get(pk=response.data["id"])
        part = OrderCurtainPart.objects.get(measurement__order=order)
        assert str(part.area_sqm) == "2.400"
        assert str(part.price_per_sqm) == "20000.00"
        assert str(part.total) == "48000.00"

        sewing = OrderItem.objects.get(order=order, service_key="sewing")
        assert sewing.name_snapshot == "Tikuv"
        assert str(sewing.unit_price) == "12500.00"
        assert str(sewing.total) == "30000.00"

    def test_lines_total_matches_order_subtotal(self, auth_client, employee, draft_payload):
        client = auth_client(employee)
        response = client.post(ORDERS_URL, draft_payload(), format="json")
        order = Order.objects.get(pk=response.data["id"])
        assert order_lines_total(order) == order.subtotal
        assert order.subtotal == order.total

    def test_delivery_creates_delivery_item(self, auth_client, employee, draft_payload):
        client = auth_client(employee)
        response = client.post(ORDERS_URL, draft_payload(delivery=True), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        order = Order.objects.get(pk=response.data["id"])
        delivery = OrderItem.objects.get(order=order, service_key="delivery")
        assert delivery.name_snapshot == "Yetkazish"
        assert str(delivery.total) == "30000.00"
        assert str(order.total) == "108000.00"
        assert order_lines_total(order) == order.total

    def test_manual_discount_tracks_source(self, auth_client, employee, draft_payload):
        client = auth_client(employee)
        response = client.post(
            ORDERS_URL, draft_payload(discount_percent="5.00"), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        assert data["discount_source"] == "manual"
        assert data["discount_amount"] == "3900.00"
        assert data["subtotal"] == "78000.00"

    def test_unauthenticated_cannot_create(self, api_client, draft_payload):
        response = api_client.post(ORDERS_URL, draft_payload(), format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRetrieveAndPatchOrder:
    """8.11 — GET/PATCH /orders/{id}/."""

    def test_employee_can_patch_customer_info(self, auth_client, employee, create_order):
        order = create_order(employee)
        client = auth_client(employee)
        response = client.patch(
            f"{ORDERS_URL}{order.id}/",
            {"customer_name": "Aliya Saidova", "note": "Chaqiruvga qo'shildi"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["customer_name"] == "Aliya Saidova"
        assert response.data["note"] == "Chaqiruvga qo'shildi"
        order.refresh_from_db()
        assert order.total == Decimal("78000.00")

    def test_patch_measurements_recalculates_total(self, auth_client, employee, draft_payload, create_order):
        order = create_order(employee)
        client = auth_client(employee)
        payload = draft_payload()
        payload["measurements"][0]["parts"][0]["width_m"] = "3.000"
        payload["measurements"][0]["cornice_length_m"] = "3.000"

        response = client.patch(
            f"{ORDERS_URL}{order.id}/", {"measurements": payload["measurements"]}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total"] == "117000.00"
        assert response.data["prepayment"] == "58500.00"
        order.refresh_from_db()
        part = OrderCurtainPart.objects.get(measurement__order=order)
        assert str(part.area_sqm) == "3.600"
        assert str(part.total) == "72000.00"
        assert order_lines_total(order) == order.subtotal == order.total

    def test_patch_services_only_recalculates(self, auth_client, employee, create_order):
        order = create_order(employee)
        client = auth_client(employee)
        response = client.patch(
            f"{ORDERS_URL}{order.id}/",
            {"services": [], "delivery": True},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert not OrderItem.objects.filter(order=order, service_key="sewing").exists()
        assert OrderItem.objects.filter(order=order, service_key="delivery").exists()
        assert str(order.total) == "78000.00"

    def test_manager_can_patch_orders(self, auth_client, employee, manager, create_order):
        order = create_order(employee)
        response = auth_client(manager).patch(
            f"{ORDERS_URL}{order.id}/", {"address": "Yangilangan manzil"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["address"] == "Yangilangan manzil"


class TestConfirmOrder:
    """8.12 — POST /orders/{id}/confirm/."""

    def test_confirm_draft_order(self, auth_client, employee, create_order):
        order = create_order(employee)
        client = auth_client(employee)
        response = client.post(f"{ORDERS_URL}{order.id}/confirm/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == OrderStatus.CONFIRMED
        assert response.data["confirmed_by"]["id"] == str(employee.id)
        assert response.data["confirmed_at"] is not None

    def test_cannot_confirm_non_draft(self, auth_client, employee, create_order):
        order = create_order(employee)
        client = auth_client(employee)
        client.post(f"{ORDERS_URL}{order.id}/confirm/")
        response = client.post(f"{ORDERS_URL}{order.id}/confirm/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Faqat draft" in response.data["errors"]["status"]


class TestChangeStatus:
    """8.13 — POST /orders/{id}/status/."""

    def test_change_status_with_note_and_date(self, auth_client, employee, create_order):
        order = create_order(employee)
        client = auth_client(employee)
        client.post(f"{ORDERS_URL}{order.id}/confirm/")
        response = client.post(
            f"{ORDERS_URL}{order.id}/status/",
            {"status": "measuring", "note": "O'lchov kuni belgilandi", "action_date": "2026-09-20"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == OrderStatus.MEASURING
        assert response.data["deadline_date"] == "2026-09-20"

    def test_invalid_transition_rejected(self, auth_client, employee, create_order):
        order = create_order(employee)
        response = auth_client(employee).post(
            f"{ORDERS_URL}{order.id}/status/",
            {"status": "completed"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "holatdan" in response.data["errors"]["status"]
        assert "ruxsat etilmagan" in response.data["errors"]["status"]

    def test_invalid_status_value(self, auth_client, employee, create_order):
        order = create_order(employee)
        response = auth_client(employee).post(
            f"{ORDERS_URL}{order.id}/status/",
            {"status": "noma'lum"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestStatusesList:
    """8.14 — GET /orders/statuses/."""

    def test_employee_can_view_status_graph(self, auth_client, employee):
        response = auth_client(employee).get(f"{ORDERS_URL}statuses/")
        assert response.status_code == status.HTTP_200_OK
        graph = {item["value"]: item for item in response.data}
        assert OrderStatus.DRAFT in graph
        assert graph[OrderStatus.DRAFT]["allowed"] == ["cancelled", "confirmed"]
        assert graph[OrderStatus.COMPLETED]["allowed"] == []


class TestOrderFilters:
    """8.9 — GET /orders/ filtrlar: status, sana, xodim, ?search=."""

    def test_filter_by_status(self, auth_client, manager, employee, create_order):
        draft_order = create_order(employee)
        confirmed_order = create_order(employee, customer_phone="+998901234001")
        from apps.orders.services import change_order_status

        change_order_status(order=confirmed_order, target=OrderStatus.CONFIRMED, user=manager)

        response = auth_client(manager).get(ORDERS_URL, {"status": "confirmed"})
        assert response.status_code == status.HTTP_200_OK
        numbers = [row["number"] for row in response.data["results"]]
        assert confirmed_order.number in numbers
        assert draft_order.number not in numbers

    def test_filter_by_employee(self, auth_client, manager, employee, other_employee, create_order):
        create_order(employee)
        other_order = create_order(other_employee)
        response = auth_client(manager).get(ORDERS_URL, {"user": str(other_employee.id)})
        assert response.status_code == status.HTTP_200_OK
        numbers = [row["number"] for row in response.data["results"]]
        assert numbers == [other_order.number]

    def test_filter_by_date(self, auth_client, manager, employee, create_order):
        order = create_order(employee)
        today = timezone.localdate().isoformat()
        response = auth_client(manager).get(ORDERS_URL, {"date": today})
        assert response.status_code == status.HTTP_200_OK
        numbers = [row["number"] for row in response.data["results"]]
        assert order.number in numbers

    def test_search_by_customer(self, auth_client, manager, employee, create_order):
        order = create_order(employee, customer_name="Kamol Rahimov")
        response = auth_client(manager).get(ORDERS_URL, {"search": "Kamol"})
        assert response.status_code == status.HTTP_200_OK
        numbers = [row["number"] for row in response.data["results"]]
        assert order.number in numbers


class TestOrderPdf:
    """8.15 — GET /orders/{id}/pdf/."""

    def test_pdf_returns_503_when_library_missing(self, auth_client, employee, create_order, monkeypatch):
        from apps.orders import pdf as pdf_module

        monkeypatch.setattr(pdf_module, "_load_pdf_library", lambda: None)
        order = create_order(employee)
        response = auth_client(employee).get(f"{ORDERS_URL}{order.id}/pdf/")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data["code"] == "pdf_unavailable"
        assert "kutubxona" in response.data["detail"]

    def test_generate_order_pdf_raises_without_library(self, create_order, employee, monkeypatch):
        """Kutubxona topilmasa tushunarli xato chiqadi."""

        from apps.orders import pdf as pdf_module

        monkeypatch.setattr(pdf_module, "_load_pdf_library", lambda: None)
        order = create_order(employee)
        with pytest.raises(pdf_module.PdfUnavailableError):
            pdf_module.generate_order_pdf(order=order)

    def test_generate_order_pdf_returns_pdf_bytes(self, create_order, employee):
        """`reportlab` o'rnatilgani uchun haqiqiy PDF qaytadi (rules.md 17.2)."""

        from apps.orders.pdf import generate_order_pdf

        order = create_order(employee)
        content = generate_order_pdf(order=order)
        assert content.startswith(b"%PDF")
        assert len(content) > 1000

    def test_pdf_endpoint_returns_pdf(self, auth_client, employee, create_order):
        """8.15 — endpoint `application/pdf` qaytaradi."""

        order = create_order(employee)
        response = auth_client(employee).get(f"{ORDERS_URL}{order.id}/pdf/")
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"