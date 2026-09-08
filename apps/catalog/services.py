from decimal import Decimal
from typing import List, Literal
from django.db import transaction
from apps.catalog.models import ProductVariant, ProductImage, Product

def bulk_update_variant_prices(
    tenant_id: str,
    variant_ids: List[str],
    value: Decimal,
    type: Literal["percent", "amount"]
) -> int:
    variants = ProductVariant.objects.filter(id__in=variant_ids, tenant_id=tenant_id)
    updated_count = 0
    with transaction.atomic():
        for variant in variants:
            if type == "percent":
                variant.price = variant.price * (Decimal("1") + value / Decimal("100"))
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
    is_primary: bool = False
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
