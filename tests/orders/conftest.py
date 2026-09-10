"""orders app testlari uchun lokal fixture'lar (8.18)."""

from __future__ import annotations

from typing import Any

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.choices import PriceUnit
from apps.common.factories import AdminFactory, EmployeeFactory, ManagerFactory, TenantFactory
from apps.orders.services import create_order_from_draft


@pytest.fixture()
def tenant_db(db: Any) -> Any:
    """Test bazasida saqlangan tenant."""

    return TenantFactory()


@pytest.fixture()
def employee(tenant_db: Any) -> Any:
    """Xodim foydalanuvchi."""

    return EmployeeFactory(tenant=tenant_db)


@pytest.fixture()
def other_employee(tenant_db: Any) -> Any:
    """Yana bir xodim (egasini tekshirish uchun)."""

    return EmployeeFactory(tenant=tenant_db)


@pytest.fixture()
def manager(tenant_db: Any) -> Any:
    """Menejer foydalanuvchi."""

    return ManagerFactory(tenant=tenant_db)


@pytest.fixture()
def admin(tenant_db: Any) -> Any:
    """Admin foydalanuvchi."""

    return AdminFactory(tenant=tenant_db)


@pytest.fixture()
def auth_client(client: Any) -> Any:
    """JWT Bearer bilan sozlangan APIClient."""

    from rest_framework_simplejwt.tokens import RefreshToken

    def _auth(user: Any) -> Any:
        token = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    return _auth


@pytest.fixture()
def variant(tenant_db: Any) -> Any:
    """Hisob uchun mos mahsulot varianti (per_sqm, 20000 so'm)."""

    category = Category.objects.create(tenant=tenant_db, name="Pardalar", slug="pardalar")
    product = Product.objects.create(
        tenant=tenant_db,
        category=category,
        name="Velvet Parda",
        code="P-V1",
    )
    return ProductVariant.objects.create(
        tenant=tenant_db,
        product=product,
        sku="P-V1-RED",
        color_name="Qizil",
        price="20000.00",
        price_unit=PriceUnit.PER_SQM,
    )


@pytest.fixture()
def draft_payload(variant: Any) -> Any:
    """AI draft'i formatidagi standart buyurtma payload'i."""

    def _payload(**overrides: Any) -> dict[str, Any]:
        data: dict[str, Any] = {
            "customer_name": "Aziz Karimov",
            "customer_phone": "+998901112233",
            "address": "Toshkent shahar",
            "measurements": [
                {
                    "room_name": "Mehmonxona",
                    "cornice_length_m": "2.000",
                    "height_m": "1.000",
                    "coefficient": "1.000",
                    "layers": [],
                    "parts": [
                        {
                            "variant_id": str(variant.id),
                            "role": "portyera",
                            "width_m": "2.000",
                            "height_m": "1.000",
                            "coefficient": "1.000",
                        }
                    ],
                    "accessories": [],
                }
            ],
            "services": ["sewing"],
            "delivery": False,
        }
        data.update(overrides)
        return data

    return _payload


@pytest.fixture()
def create_order(draft_payload: Any) -> Any:
    """Service orqali berilgan foydalanuvchiga buyurtma yaratadi."""

    def _create(user: Any, **overrides: Any) -> Any:
        order, _ = create_order_from_draft(payload=draft_payload(**overrides), user=user)
        return order

    return _create
