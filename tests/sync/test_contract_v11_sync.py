"""Kontrakt 1.1: pricing/fason/prompt delta'lari va Snapshot'ning yangi maydonlari."""

import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.apps import apps as django_apps

from apps.catalog.models import Category, Fason, FasonAccessory, FasonPart, Product, ProductVariant
from apps.chat.grpc_server.catalog_service import CatalogServicer
from apps.common.factories import AdminFactory, TenantFactory
from apps.pricing.models import DiscountPolicy, DiscountTier, OrderDefaults, ServicePrice
from apps.prompts.models import PromptVersion

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_redis():
    with patch("apps.chat.grpc_server.catalog_service.redis.from_url") as from_url:
        client = MagicMock()
        client.incr.return_value = 7
        client.get.return_value = b"7"
        from_url.return_value = client
        yield client


def _last_delta(client: MagicMock) -> dict:
    args, _kwargs = client.publish.call_args
    return json.loads(args[1])


def _payload(client: MagicMock) -> dict:
    return json.loads(_last_delta(client)["payload_json"])


# ── Signallar ──────────────────────────────────────────────────────────────


def test_service_price_signal_carries_decimal_payload(mock_redis):
    ServicePrice.objects.create(key="cornice", name="Karniz", price="45000.50", unit="per_meter")

    delta = _last_delta(mock_redis)
    assert delta["entity"] == "service_price"
    assert delta["action"] == "create"
    assert delta["tenant_id"] == ""
    assert _payload(mock_redis) == {
        "key": "cornice",
        "name": "Karniz",
        "price": "45000.50",
        "unit": "per_meter",
        "is_active": True,
    }


def test_discount_tier_delete_has_empty_payload(mock_redis):
    tier = DiscountTier.objects.create(min_amount="5000000.00", percent="3.00")
    assert _payload(mock_redis)["percent"] == "3.00"

    tier.delete()
    delta = _last_delta(mock_redis)
    assert delta["entity"] == "discount_tier"
    assert delta["action"] == "delete"
    assert delta["payload_json"] == "{}"


def test_discount_policy_and_order_defaults_signals(mock_redis):
    DiscountPolicy.objects.create(
        manual_max_percent_employee="5.00",
        manual_max_percent_manager="15.00",
        stack_with_tier=False,
    )
    assert _last_delta(mock_redis)["entity"] == "discount_policy"
    assert _payload(mock_redis)["manual_max_percent_employee"] == "5.00"
    assert _payload(mock_redis)["stack_with_tier"] is False

    OrderDefaults.objects.create(
        prepayment_percent="50.00", delivery_amount="30000.00", deadline_days=14
    )
    assert _last_delta(mock_redis)["entity"] == "order_defaults"
    assert _payload(mock_redis)["deadline_days"] == 14


def test_fason_child_change_republishes_whole_fason(mock_redis):
    tenant = TenantFactory()
    fason = Fason.objects.create(tenant=tenant, name="Klassik", style="classic", rooms=["living"])
    assert _last_delta(mock_redis)["entity"] == "fason"
    assert _last_delta(mock_redis)["action"] == "create"

    FasonPart.objects.create(
        tenant=tenant,
        fason=fason,
        role="portyera",
        name="Asosiy",
        width_share="1.000",
        height_share="1.000",
        default_coef="2.500",
    )
    delta = _last_delta(mock_redis)
    assert delta["entity"] == "fason"
    assert delta["action"] == "update"
    assert delta["entity_id"] == str(fason.id)
    payload = _payload(mock_redis)
    assert payload["parts"][0]["role"] == "portyera"
    assert payload["parts"][0]["default_coef"] == "2.500"

    FasonAccessory.objects.create(tenant=tenant, fason=fason, category="podxvat", default_qty="2")
    assert _payload(mock_redis)["accessories"][0]["default_qty"] == "2.000"

    fason.delete()
    assert _last_delta(mock_redis)["action"] == "delete"


def test_prompt_signal_only_for_current_version(mock_redis):
    author = AdminFactory()
    PromptVersion.objects.create(version=1, content="eski", author=author, is_current=False)
    assert not mock_redis.publish.called

    PromptVersion.objects.create(version=2, content="yangi", author=author, is_current=True)
    delta = _last_delta(mock_redis)
    assert delta["entity"] == "prompt"
    assert _payload(mock_redis)["version"] == 2
    assert _payload(mock_redis)["content"] == "yangi"


def test_product_and_variant_payloads_include_data_go_needs(mock_redis):
    tenant = TenantFactory()
    category = Category.objects.create(tenant=tenant, name="Mato", slug="mato")
    product = Product.objects.create(tenant=tenant, category=category, name="Velvet", code="V1")
    assert _payload(mock_redis)["name"] == "Velvet"
    assert _payload(mock_redis)["variants"] == []

    variant = ProductVariant.objects.create(
        tenant=tenant, product=product, sku="V1-G", color_name="grafit", price="180000.00"
    )
    payload = _payload(mock_redis)
    assert payload["product_id"] == str(product.id)
    assert payload["price"] == 180000.0
    assert "cost_price" not in payload  # tannarx AI'ga yuborilmaydi (rules §4.11)

    variant.delete()
    delta = _last_delta(mock_redis)
    assert delta["action"] == "delete"
    assert json.loads(delta["payload_json"]) == {"product_id": str(product.id)}


# ── Snapshot ───────────────────────────────────────────────────────────────


def _seed_pricing():
    migration = __import__("apps.pricing.migrations.0002_seed_defaults", fromlist=["forwards"])
    migration.forwards(django_apps, None)


def test_snapshot_first_page_contains_pricing_fasons_prompt(mock_redis):
    from grpc_gen import alora_pb2

    _seed_pricing()
    tenant = TenantFactory()
    fason = Fason.objects.create(tenant=tenant, name="Klassik", style="classic")
    FasonPart.objects.create(tenant=tenant, fason=fason, role="tul", name="Tul", default_coef="3")
    PromptVersion.objects.create(
        version=1, content="Sen Alora", author=AdminFactory(), is_current=True
    )
    category = Category.objects.create(tenant=tenant, name="Mato", slug="mato")
    for i in range(3):
        Product.objects.create(tenant=tenant, category=category, name=f"P{i}", code=f"C{i}")

    servicer = CatalogServicer()
    first = servicer._build_snapshot(page_token="", page_size=2, pb2=alora_pb2)

    assert first.version == 7
    assert first.total_count == 3
    assert first.next_page_token == "2"
    assert len(first.products) == 2
    assert {s.key for s in first.service_prices} >= {
        "sewing",
        "tape",
        "hook",
        "install",
        "delivery",
    }
    sewing = next(s for s in first.service_prices if s.key == "sewing")
    assert Decimal(sewing.price) == Decimal(
        ServicePrice.objects.get(key="sewing").price
    )  # decimal matn, aniqlik yo'qolmagan
    assert first.discount_policy.manual_max_percent_employee != ""
    assert first.order_defaults.deadline_days > 0
    assert first.fasons[0].name == "Klassik"
    assert first.fasons[0].parts[0].role == "tul"
    assert first.prompt.version == 1
    assert first.prompt.content == "Sen Alora"
    assert len(first.calc_rules) > 0

    second = servicer._build_snapshot(page_token="2", page_size=2, pb2=alora_pb2)
    assert len(second.products) == 1
    assert second.next_page_token == ""
    # Mahsulotdan boshqa hamma narsa faqat birinchi sahifada
    assert len(second.service_prices) == 0
    assert len(second.fasons) == 0
    assert len(second.calc_rules) == 0
    assert not second.HasField("prompt")


def test_snapshot_without_prompt_and_policy_does_not_fail(mock_redis):
    from grpc_gen import alora_pb2

    DiscountPolicy.objects.all().delete()
    OrderDefaults.objects.all().delete()
    snapshot = CatalogServicer()._build_snapshot(page_token="", page_size=10, pb2=alora_pb2)
    assert not snapshot.HasField("prompt")
    assert not snapshot.HasField("discount_policy")
    assert not snapshot.HasField("order_defaults")
    assert snapshot.total_count == 0
