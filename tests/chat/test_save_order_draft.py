"""Backend.SaveOrderDraft uchun kontrakt testlari."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from django.core.cache import cache

from apps.catalog.models import Category, Product, ProductVariant
from apps.chat.grpc_server.backend_service import save_order_draft
from apps.chat.models import Conversation
from apps.common.choices import PriceUnit
from apps.common.factories import EmployeeFactory, TenantFactory
from apps.orders.models import Order, OrderCurtainPart


@pytest.fixture()
def draft_context(db):
    """Draft RPC uchun tenant, user, suhbat va faol variant yaratadi."""
    tenant = TenantFactory()
    user = EmployeeFactory(tenant=tenant)
    category = Category.objects.create(tenant=tenant, name="Parda", slug="parda")
    product = Product.objects.create(tenant=tenant, category=category, name="Velvet", code="V1")
    variant = ProductVariant.objects.create(
        tenant=tenant,
        product=product,
        sku="V1-RED",
        color_name="Qizil",
        price="20000.00",
        price_unit=PriceUnit.PER_SQM,
    )
    conversation = Conversation.objects.create(
        tenant=tenant, user=user, session_id="draft-session", title="Draft"
    )
    cache.clear()
    return user, conversation, variant


def _data(user, conversation, items, **extra):
    return {
        "session_id": "draft-session",
        "user_id": str(user.id),
        "conversation_id": str(conversation.id),
        "customer_name": "Aziz Karimov",
        "customer_phone": "+998901112233",
        "address": "Toshkent",
        "note": "",
        "items_json": json.dumps(items),
        **extra,
    }


def _items(variant):
    return {
        "measurements": [
            {
                "length": "2.000",
                "height": "1.000",
                "parts": [
                    {
                        "variant_id": str(variant.id),
                        "role": "portyera",
                        "width_m": "2.000",
                        "height_m": "1.000",
                        "coef": "1.000",
                    }
                ],
                "accessories": [],
            }
        ],
        "services": ["sewing"],
        "delivery": False,
        "discount_percent": "0",
    }


def test_save_order_draft_creates_order_and_conversation_link(draft_context):
    user, conversation, variant = draft_context

    result = save_order_draft(_data(user, conversation, _items(variant)))

    assert result["success"] is True
    order = Order.objects.get(id=result["order_id"])
    assert order.number.startswith("ALR-")
    assert conversation.__class__.objects.get(id=conversation.id).order_id == order.id
    assert OrderCurtainPart.objects.get(measurement__order=order).price_per_sqm == Decimal(
        "20000.00"
    )


def test_save_order_draft_rejects_invalid_json(draft_context):
    user, conversation, _ = draft_context

    result = save_order_draft(_data(user, conversation, {}, items_json="not-json"))

    assert result["success"] is False
    assert "items_json" in result["error"]


def test_save_order_draft_reports_missing_variant(draft_context):
    user, conversation, variant = draft_context
    items = _items(variant)
    items["measurements"][0]["parts"][0]["variant_id"] = "00000000-0000-0000-0000-000000000000"

    result = save_order_draft(_data(user, conversation, items))

    assert result["success"] is False
    assert "variant" in result["error"].lower()


def test_save_order_draft_is_idempotent_for_repeated_request(draft_context):
    user, conversation, variant = draft_context
    data = _data(user, conversation, _items(variant))

    first = save_order_draft(data)
    second = save_order_draft(data)

    assert second["order_id"] == first["order_id"]
    assert Order.objects.count() == 1
