from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Category, Product, ProductImage, ProductVariant


def bulk_update_variant_prices(
    tenant_id: str, variant_ids: list[str], value: Decimal, type: Literal["percent", "amount"]
) -> int:
    variants = ProductVariant.objects.filter(id__in=variant_ids, tenant_id=tenant_id)
    updated_count = 0
    with transaction.atomic():
        for variant in variants:
            if type == "percent":
                variant.price = variant.price * (Decimal(1) + value / Decimal(100))
            elif type == "amount":
                variant.price = variant.price + value
            variant.save(update_fields=["price", "updated_at"])
            updated_count += 1
    return updated_count


def upload_product_image(
    tenant,
    product: Product,
    image_file,
    variant_id: str | None = None,
    alt: str = "",
    is_primary: bool = False,
) -> ProductImage:
    # 3.20 task dictates celery for image resizing, but for now we just create
    from apps.catalog.tasks import compress_image_task

    image = ProductImage.objects.create(
        tenant=tenant,
        product=product,
        variant_id=variant_id,
        image=image_file,
        alt=alt,
        is_primary=is_primary,
    )

    # Celery task to compress
    transaction.on_commit(lambda: compress_image_task.delay(str(image.id)))

    return image


@dataclass(frozen=True)
class ImportResult:
    created: int
    updated: int
    skipped: int
    errors: list[dict[str, Any]]


from collections.abc import Sequence


def _validate_headers(fieldnames: Sequence[str] | None) -> None:
    required = {"code", "name", "category_slug", "sku", "color_name", "price"}
    if not fieldnames or not required.issubset(set(fieldnames)):
        raise ValidationError(f"Kerakli ustunlar topilmadi. Talab etiladi: {required}")


def _upsert_row(*, tenant, row: dict[str, str]) -> tuple[ProductVariant, bool]:
    # Ensure required keys exist and aren't empty
    for key in ("code", "name", "category_slug", "sku", "color_name", "price"):
        if not row.get(key):
            raise ValidationError(f"{key} ko'rsatilmagan")

    price_str = row["price"].replace(",", ".")
    price = Decimal(price_str)

    category, _ = Category.objects.get_or_create(
        tenant=tenant,
        slug=row["category_slug"],
        defaults={"name": row.get("category_name") or row["category_slug"]},
    )
    product, _ = Product.objects.update_or_create(
        tenant=tenant, code=row["code"], defaults={"name": row["name"], "category": category}
    )
    variant, created = ProductVariant.objects.update_or_create(
        tenant=tenant,
        sku=row["sku"],
        defaults={
            "product": product,
            "color_name": row["color_name"],
            "price": price,
            "price_unit": row.get("price_unit") or "per_sqm",
        },
    )
    return variant, created


@transaction.atomic
def import_catalog_csv(*, tenant, file, dry_run: bool = False) -> ImportResult:
    """CSV dan mahsulot va variantlarni import qiladi.

    Xato satrlar butun importni yiqitmaydi — `errors` ro'yxatiga tushadi.
    """
    reader = csv.DictReader(io.TextIOWrapper(file, encoding="utf-8-sig"))
    _validate_headers(reader.fieldnames)
    created = updated = skipped = 0
    errors: list[dict[str, Any]] = []
    for row_no, row in enumerate(reader, start=2):
        try:
            _, was_created = _upsert_row(tenant=tenant, row=row)
            created += was_created
            updated += not was_created
        except (ValidationError, KeyError, InvalidOperation) as exc:
            skipped += 1
            # ValidationError might contain detail attribute, standard exceptions just str()
            err_msg = (
                exc.detail[0]
                if isinstance(exc, ValidationError)
                and hasattr(exc, "detail")
                and isinstance(exc.detail, list)
                else str(exc)
            )
            errors.append({"row": row_no, "code": row.get("code"), "error": err_msg})
    if dry_run:
        transaction.set_rollback(True)
    return ImportResult(created, updated, skipped, errors)
