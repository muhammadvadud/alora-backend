import json
from unittest.mock import MagicMock, patch

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.factories import TenantFactory
from apps.knowledge.models import KnowledgeRule
from apps.pricing.models import CalcRule

pytestmark = pytest.mark.django_db


@patch("apps.chat.grpc_server.catalog_service.redis.from_url")
def test_product_save_and_delete_publishes_delta(mock_redis_from_url):
    mock_redis = MagicMock()
    mock_redis_from_url.return_value = mock_redis
    mock_redis.incr.return_value = 1

    tenant = TenantFactory()
    category = Category.objects.create(tenant=tenant, name="Test Cat", slug="test-cat")

    product = Product.objects.create(
        tenant=tenant,
        category=category,
        name="Test Product",
        code="P001",
    )

    assert mock_redis.publish.called
    args, _kwargs = mock_redis.publish.call_args
    channel, message_json = args
    assert channel == "alora:catalog:deltas"

    message = json.loads(message_json)
    assert message["entity"] == "product"
    assert message["entity_id"] == str(product.id)
    assert message["action"] == "create"
    assert message["tenant_id"] == str(tenant.id)

    mock_redis.publish.reset_mock()
    product.name = "Updated"
    product.save()

    args, _kwargs = mock_redis.publish.call_args
    message = json.loads(args[1])
    assert message["action"] == "update"

    mock_redis.publish.reset_mock()
    product.delete()
    args, _kwargs = mock_redis.publish.call_args
    message = json.loads(args[1])
    assert message["action"] == "delete"


@patch("apps.chat.grpc_server.catalog_service.redis.from_url")
def test_product_variant_signals(mock_redis_from_url):
    mock_redis = MagicMock()
    mock_redis_from_url.return_value = mock_redis
    mock_redis.incr.return_value = 1

    tenant = TenantFactory()
    category = Category.objects.create(tenant=tenant, name="Test Cat", slug="test-cat")
    product = Product.objects.create(tenant=tenant, category=category, name="P1", code="C1")

    mock_redis.publish.reset_mock()
    ProductVariant.objects.create(
        tenant=tenant,
        product=product,
        sku="SKU1",
        color_name="Red",
        price=10.0,
    )

    args, _kwargs = mock_redis.publish.call_args
    message = json.loads(args[1])
    assert message["entity"] == "variant"
    assert message["action"] == "create"


@patch("apps.chat.grpc_server.catalog_service.redis.from_url")
def test_calc_rule_signals(mock_redis_from_url):
    mock_redis = MagicMock()
    mock_redis_from_url.return_value = mock_redis
    mock_redis.incr.return_value = 1

    CalcRule.objects.create(
        key="test_rule",
        value=1.5,
        unit="test"
    )

    args, _kwargs = mock_redis.publish.call_args
    message = json.loads(args[1])
    assert message["entity"] == "calc_rule"
    assert message["action"] == "create"
    assert message["tenant_id"] == ""


@patch("apps.chat.grpc_server.catalog_service.redis.from_url")
def test_knowledge_rule_signals(mock_redis_from_url):
    mock_redis = MagicMock()
    mock_redis_from_url.return_value = mock_redis
    mock_redis.incr.return_value = 1

    KnowledgeRule.objects.create(
        kind="general",
        recommendation="test rec"
    )

    args, _kwargs = mock_redis.publish.call_args
    message = json.loads(args[1])
    assert message["entity"] == "knowledge_rule"
    assert message["action"] == "create"
    assert message["tenant_id"] == ""


@patch("apps.chat.grpc_server.catalog_service.redis.from_url")
def test_version_increment(mock_redis_from_url):
    mock_redis = MagicMock()
    mock_redis_from_url.return_value = mock_redis
    mock_redis.get.return_value = b"5"
    mock_redis.incr.return_value = 6

    from apps.chat.grpc_server.catalog_service import get_catalog_version, increment_catalog_version

    assert get_catalog_version() == 5
    assert increment_catalog_version() == 6
    mock_redis.incr.assert_called_with("alora:catalog:version")

