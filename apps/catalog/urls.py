from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.catalog.views import (
    CategoryViewSet, ProductViewSet, ProductVariantViewSet, 
    ProductImageViewSet, FasonViewSet, CatalogImportView
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("variants", ProductVariantViewSet, basename="variant")
router.register("images", ProductImageViewSet, basename="image")
router.register("fasons", FasonViewSet, basename="fason")
router.register("import", CatalogImportView, basename="import")

urlpatterns = [
    path("", include(router.urls)),
]
