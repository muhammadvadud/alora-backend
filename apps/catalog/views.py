from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.catalog.filters import ProductFilter
from apps.catalog.models import Category, Fason, Product, ProductImage, ProductVariant
from apps.catalog.permissions import IsManagerOrReadOnly
from apps.catalog.selectors import (
    get_categories,
    get_fasons,
    get_product_by_identifier,
    get_products,
    get_variants,
)
from apps.catalog.serializers import (
    BulkPriceSerializer,
    CatalogImportReportSerializer,
    CatalogImportSerializer,
    CategorySerializer,
    FasonReadSerializer,
    FasonWriteSerializer,
    ImageUploadSerializer,
    ProductImageSerializer,
    ProductReadSerializer,
    ProductVariantReadSerializer,
    ProductVariantWriteSerializer,
    ProductWriteSerializer,
)
from apps.catalog.services import bulk_update_variant_prices, upload_product_image
from apps.catalog.services.import_service import import_products
from apps.common.permissions import IsManager


class BaseCatalogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManagerOrReadOnly]


class CategoryViewSet(BaseCatalogViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()
        return get_categories(tenant_id=self.request.user.tenant_id)


class ProductViewSet(BaseCatalogViewSet):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()
        return get_products(tenant_id=self.request.user.tenant_id)

    def get_object(self):
        product = get_product_by_identifier(
            self.kwargs.get(self.lookup_url_kwarg or self.lookup_field),
            tenant_id=self.request.user.tenant_id,
        )
        self.check_object_permissions(self.request, product)
        return product

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ProductReadSerializer
        return ProductWriteSerializer

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsManager],
    )
    def images(self, request, pk=None):
        product = self.get_object()
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = upload_product_image(
            tenant=request.user.tenant,
            product=product,
            image_file=serializer.validated_data["image"],
            variant_id=serializer.validated_data.get("variant_id"),
            alt=serializer.validated_data.get("alt", ""),
            is_primary=serializer.validated_data.get("is_primary", False),
        )
        return Response(ProductImageSerializer(image).data, status=status.HTTP_201_CREATED)


class ProductVariantViewSet(BaseCatalogViewSet):
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ProductVariant.objects.none()
        return get_variants(tenant_id=self.request.user.tenant_id)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ProductVariantReadSerializer
        return ProductVariantWriteSerializer

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

    @action(detail=False, methods=["post"], permission_classes=[IsManager], url_path="bulk-price")
    def bulk_price(self, request):
        serializer = BulkPriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_count = bulk_update_variant_prices(
            tenant_id=request.user.tenant_id,
            variant_ids=serializer.validated_data["variant_ids"],
            value=serializer.validated_data["value"],
            type=serializer.validated_data["type"],
        )
        return Response({"updated": updated_count})


class ProductImageViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsManager]
    serializer_class = ProductImageSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ProductImage.objects.none()
        return ProductImage.objects.filter(tenant_id=self.request.user.tenant_id)


class FasonViewSet(BaseCatalogViewSet):
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Fason.objects.none()
        return get_fasons(tenant_id=self.request.user.tenant_id)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FasonReadSerializer
        return FasonWriteSerializer

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class CatalogImportView(viewsets.ViewSet):
    permission_classes = [IsManager]
    serializer_class = None
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        operation_id="catalog_import_csv",
        summary="CSV import",
        description="CSV fayldan katalog ma'lumotlarini import qilish.",
        responses={200: dict},
    )
    def _import(self, request):
        import dataclasses

        file = request.FILES.get("file")
        if not file:
            raise ValidationError({"file": "Fayl taqdim etilmadi"})

        dry_run = request.query_params.get("dry_run", "false").lower() == "true"
        if "dry_run" in request.data:
            dry_run = str(request.data["dry_run"]).lower() == "true"
        try:
            result = import_products(file=file, tenant=request.user.tenant, dry_run=dry_run)
        except ValueError as exc:
            raise ValidationError({"file": str(exc)}) from exc
        return Response(dataclasses.asdict(result))

    @extend_schema(request=CatalogImportSerializer, responses=CatalogImportReportSerializer)
    def create(self, request, *args, **kwargs):
        return self._import(request)

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser])
    def import_csv(self, request):
        return self._import(request)
