"""seed_dev_catalog management buyrug'i testlari.

Buyruq idempotent, REF (etalon) mahsulotlarga tegmaydi va DEBUG=False +
`--force` bo'lmasa `CommandError` beradi.
"""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.accounts.models import Tenant
from apps.catalog.models import Category, Fason, FasonPart, Product, ProductVariant
from apps.knowledge.models import KnowledgeRule


@pytest.fixture()
def seed_tenant(db):
    return Tenant.objects.create(name="Test Filial", phone="+998901234500")


@pytest.fixture()
def ref_etalon(seed_tenant):
    category, _ = Category.objects.get_or_create(
        tenant=seed_tenant, slug="etalon", defaults={"name": "Etalon"}
    )
    product = Product.objects.create(
        tenant=seed_tenant,
        name="REF-ETALON",
        code="REF-ETALON",
        category=category,
        style="classic",
    )
    ProductVariant.objects.create(
        tenant=seed_tenant,
        product=product,
        sku="REF-ETALON-STD",
        color_name="Oq",
        price="100000.00",
    )
    return product


def _run(force: bool = False) -> StringIO:
    out = StringIO()
    kwargs = {"stdout": out}
    if force:
        kwargs["force"] = True
    call_command("seed_dev_catalog", **kwargs)
    return out


@pytest.fixture()
def mock_redis():
    with patch("apps.chat.grpc_server.catalog_service.redis.from_url") as from_url:
        client = MagicMock()
        client.incr.return_value = 5
        from_url.return_value = client
        yield client


@override_settings(DEBUG=True)
def test_seed_is_idempotent(mock_redis, seed_tenant, ref_etalon):
    categories_before = Category.objects.count()
    products_before = Product.objects.count()
    variants_before = ProductVariant.objects.count()

    _run()

    assert Product.objects.count() == products_before + 14
    assert ProductVariant.objects.count() == variants_before + 19
    assert Category.objects.count() == categories_before + 6
    assert Fason.objects.count() == 3
    assert FasonPart.objects.count() == 6
    assert Fason.objects.get(name="Klassik uch qismli").part_count == 3
    assert KnowledgeRule.objects.count() == 4

    run2 = _run()

    assert Product.objects.count() == products_before + 14
    assert ProductVariant.objects.count() == variants_before + 19
    assert Category.objects.count() == categories_before + 6
    assert Fason.objects.count() == 3
    assert FasonPart.objects.count() == 6
    assert KnowledgeRule.objects.count() == 4
    assert "Katalog yaratildi" in run2.getvalue()
    assert mock_redis.publish.called
    mock_redis.publish.reset_mock()
    _run()
    assert mock_redis.publish.call_count == 0


@override_settings(DEBUG=True)
def test_seed_does_not_touch_ref_products(mock_redis, seed_tenant, ref_etalon):
    _run()

    ref = Product.objects.get(code="REF-ETALON")
    assert ref.name == "REF-ETALON"
    assert ref.style == "classic"
    assert ref.variants.count() == 1
    variant = ref.variants.first()
    assert variant is not None
    assert variant.sku == "REF-ETALON-STD"
    assert variant.price == 100000


@override_settings(DEBUG=True)
def test_seed_publishes_catalog_delta_once(mock_redis, seed_tenant):
    _run()

    assert mock_redis.publish.call_count == 1
    args, kwargs = mock_redis.publish.call_args
    assert kwargs == {}
    channel, message = args
    assert channel == "alora:catalog:deltas"
    assert '"action": "update"' in message
    assert '"entity": "catalog"' in message


@override_settings(DEBUG=False)
def test_seed_requires_debug_or_force(seed_tenant):
    with pytest.raises(CommandError):
        call_command("seed_dev_catalog", stdout=StringIO())


@override_settings(DEBUG=False)
def test_seed_force_works_without_debug(mock_redis, seed_tenant):
    out = _run(force=True)

    assert Product.objects.count() == 14
    assert "Katalog yaratildi" in out.getvalue()
