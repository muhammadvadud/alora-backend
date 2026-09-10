"""Katalog uchun Celery tasklari — rasm siqish, reindex va ogohlantirishlar."""

from __future__ import annotations

import io
import os

import structlog
from celery import shared_task
from django.core.files.base import ContentFile
from django.db.models import Exists, OuterRef
from PIL import Image

from apps.catalog.models import Product, ProductImage, ProductVariant

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def compress_image_task(self, image_id: str) -> None:
    """Rasmni siqadi: to'liq o'lcham 1200px gacha. · 3.20"""
    try:
        img_obj = ProductImage.objects.get(id=image_id)
    except ProductImage.DoesNotExist:
        return

    if not img_obj.image:
        return

    try:
        image = Image.open(img_obj.image)
        if image.mode != "RGB":
            image = image.convert("RGB")

        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85)
        output.seek(0)

        file_name = os.path.basename(img_obj.image.name)
        new_name = os.path.splitext(file_name)[0] + ".jpg"

        img_obj.image.save(new_name, ContentFile(output.read()), save=False)
        img_obj.save(update_fields=["image"])
    except Exception as exc:  # noqa: BLE001
        logger.error("image_compress_failed", error=str(exc), image_id=image_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def catalog_reindex(self, tenant_id: str = "") -> int:
    """Katalog delta'larini Redis orqali qayta e'lon qiladi. · 13.7

    Go agent lokal cache'ini yangilashi uchun barcha faol mahsulotlar
    bo'yicha `update` deltasi yuboriladi. Redis — tashqi xizmat, testlarda
    mock qilinadi (§11.5).
    """
    from apps.chat.grpc_server.catalog_service import publish_catalog_delta

    products = Product.objects.filter(is_active=True).only("id", "tenant_id", "code", "name")
    if tenant_id:
        products = products.filter(tenant_id=tenant_id)

    count = 0
    for product in products.iterator(chunk_size=500):
        publish_catalog_delta(
            tenant_id=str(product.tenant_id),
            entity="product",
            entity_id=str(product.id),
            action="update",
        )
        count += 1

    logger.info("catalog_reindex_done", count=count)
    return count


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def stock_low_alert(self, tenant_id: str = "") -> int:
    """Sotilmaydigan mahsulotlar bo'yicha ogohlantiradi. · 13.8

    v1 da ombor qoldig'i yuritilmagani uchun (TZ: `stock_qty` v2 ga qoldirilgan)
    "zaxira tugagan" holat o'rniga faol varianti bo'lmagan mahsulotlar
    ogohlantiriladi — ularni sotib bo'lmaydi. Idempotent: faqat o'qish va log.
    """
    active_variant = ProductVariant.objects.filter(product_id=OuterRef("pk"), is_active=True)
    products = (
        Product.objects.filter(is_active=True)
        .annotate(has_active_variant=Exists(active_variant))
        .only("id", "tenant_id", "code", "name")
    )
    if tenant_id:
        products = products.filter(tenant_id=tenant_id)

    alerts = 0
    for product in products:
        if product.has_active_variant:
            continue
        alerts += 1
        logger.warning(
            "stock_low_alert",
            tenant_id=str(product.tenant_id),
            product_id=str(product.id),
            product_code=product.code,
            product_name=product.name,
        )

    logger.info("stock_low_check_done", alerts=alerts)
    return alerts
