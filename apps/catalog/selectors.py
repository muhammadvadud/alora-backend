from uuid import UUID

from django.db.models import QuerySet

from apps.catalog.models import Category, Fason, Product, ProductVariant


def get_categories(*, tenant_id: UUID) -> QuerySet[Category]:
    return Category.objects.filter(tenant_id=tenant_id, is_active=True).select_related("parent")

def get_products(*, tenant_id: UUID) -> QuerySet[Product]:
    return Product.objects.filter(tenant_id=tenant_id, is_active=True).select_related("category").prefetch_related(
        "variants",
        "variants__images",
        "images"
    )

def get_product(pk, *, tenant_id: UUID) -> Product:
    return get_products(tenant_id=tenant_id).get(pk=pk)

def get_variants(*, tenant_id: UUID) -> QuerySet[ProductVariant]:
    return ProductVariant.objects.filter(tenant_id=tenant_id, is_active=True).select_related("product").prefetch_related("images")

def get_fasons(*, tenant_id: UUID) -> QuerySet[Fason]:
    return Fason.objects.filter(tenant_id=tenant_id, is_active=True).prefetch_related("parts", "accessories")
