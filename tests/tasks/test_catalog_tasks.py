"""Katalog Celery tasklari testlari — 13.7, 13.8, 3.20 va 13.9."""

from __future__ import annotations

import io
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.catalog.models import Category, Product, ProductImage, ProductVariant
from apps.catalog.tasks import catalog_reindex, compress_image_task, stock_low_alert
from apps.common.choices import PriceUnit

pytestmark = pytest.mark.django_db


@pytest.fixture()
def category(tenant):
    return Category.objects.create(
        tenant=tenant,
        name="Kategoriya",
        slug=f"cat-{uuid.uuid4().hex[:8]}",
    )


@pytest.fixture()
def product(category):
    return Product.objects.create(
        tenant=category.tenant,
        code=f"P-{uuid.uuid4().hex[:8]}",
        name="Mato",
        category=category,
    )


@pytest.fixture()
def variant(product):
    return ProductVariant.objects.create(
        tenant=product.tenant,
        product=product,
        sku=f"SKU-{uuid.uuid4().hex[:8]}",
        color_name="Qizil",
        price="50000.00",
        price_unit=PriceUnit.PER_SQM,
    )


class TestStockLowAlert:
    """13.8 — `stock_low_alert` taski."""

    def test_flags_product_without_variants(self, product):
        assert stock_low_alert(tenant_id=str(product.tenant_id)) == 1

    def test_no_alert_when_active_variant_exists(self, product, variant):
        assert stock_low_alert(tenant_id=str(product.tenant_id)) == 0

    def test_inactive_variant_flagged(self, product, variant):
        variant.is_active = False
        variant.save(update_fields=["is_active"])
        assert stock_low_alert(tenant_id=str(product.tenant_id)) == 1

    def test_inactive_product_ignored(self, tenant, product, variant):
        product.is_active = False
        product.save(update_fields=["is_active"])
        assert stock_low_alert(tenant_id=str(tenant.id)) == 0


class TestCatalogReindex:
    """13.7 — `catalog_reindex` taski. Redis mock qilinadi (§11.5)."""

    def test_publishes_update_delta_per_product(self, product, monkeypatch):
        from apps.chat.grpc_server import catalog_service

        calls: list[tuple[str, str, str, str]] = []

        def fake_publish(*, tenant_id, entity, entity_id, action):
            calls.append((tenant_id, entity, entity_id, action))
            return 1

        monkeypatch.setattr(catalog_service, "publish_catalog_delta", fake_publish)

        count = catalog_reindex(tenant_id=str(product.tenant_id))

        assert count == 1
        assert calls == [
            (str(product.tenant_id), "product", str(product.id), "update"),
        ]

    def test_no_products_no_publish(self, tenant, monkeypatch):
        from unittest.mock import Mock

        from apps.chat.grpc_server import catalog_service

        mock_publish = Mock(return_value=1)
        monkeypatch.setattr(catalog_service, "publish_catalog_delta", mock_publish)

        count = catalog_reindex(tenant_id=str(tenant.id))

        assert count == 0
        mock_publish.assert_not_called()


class TestCompressImageTask:
    """3.20 — `compress_image_task` taski."""

    def test_name_matches_celery_route(self):
        assert compress_image_task.name == "apps.catalog.tasks.compress_image_task"

    def test_missing_image_is_noop(self):
        assert compress_image_task(str(uuid.uuid4())) is None

    def test_resizes_image_to_1200px(self, tmp_path, product):
        buffer = io.BytesIO()
        Image.new("RGB", (2400, 1800), "blue").save(buffer, format="JPEG")
        buffer.seek(0)
        uploaded = SimpleUploadedFile("katta.jpg", buffer.read(), content_type="image/jpeg")

        with override_settings(MEDIA_ROOT=str(tmp_path)):
            image = ProductImage.objects.create(
                tenant=product.tenant, product=product, image=uploaded
            )
            compress_image_task(str(image.id))
            image.refresh_from_db()

            with Image.open(image.image.path) as opened:
                assert opened.width <= 1200
                assert opened.height <= 1200


class TestRetryConfiguration:
    """13.9 — katalog tasklarida retry sozlamalari borligi."""

    def test_catalog_tasks_have_retry_config(self):
        for task in (compress_image_task, catalog_reindex, stock_low_alert):
            assert task.max_retries == 3
            assert task.retry_backoff is True
            assert Exception in task.autoretry_for
