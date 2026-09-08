from django.db.models import QuerySet
from apps.catalog.models import Category, Product, ProductVariant, Fason

def get_categories() -> QuerySet:
    return Category.objects.all().select_related("parent")

def get_products() -> QuerySet:
    return Product.objects.all().select_related("category").prefetch_related(
        "variants",
        "variants__images",
        "images"
    )

def get_product(pk) -> Product:
    return get_products().get(pk=pk)

def get_variants() -> QuerySet:
    return ProductVariant.objects.all().select_related("product").prefetch_related("images")

def get_fasons() -> QuerySet:
    return Fason.objects.all().prefetch_related("parts", "accessories")
