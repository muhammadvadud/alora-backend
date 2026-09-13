from rest_framework import serializers

from apps.catalog.models import (
    Category,
    Fason,
    FasonAccessory,
    FasonPart,
    Product,
    ProductImage,
    ProductVariant,
)
from apps.common.choices import UserRole
from apps.common.validators import validate_image_file


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "parent",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        )


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "id",
            "product",
            "variant",
            "image",
            "alt",
            "sort_order",
            "is_primary",
            "is_active",
        )


class ProductVariantWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "sku",
            "color_name",
            "color_hex",
            "width_m",
            "price",
            "price_unit",
            "old_price",
            "cost_price",
            "is_active",
        )


class ProductVariantReadSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "color_name",
            "color_hex",
            "width_m",
            "price",
            "price_unit",
            "old_price",
            "cost_price",
            "is_active",
            "images",
            "created_at",
            "updated_at",
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")
        if (
            request
            and hasattr(request, "user")
            and getattr(request.user, "role", None) != UserRole.ADMIN
        ):
            ret.pop("cost_price", None)
        return ret


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "name",
            "code",
            "description",
            "fabric_type",
            "pattern",
            "style",
            "transparency",
            "density",
            "composition",
            "care",
            "recommended_rooms",
            "recommended_coef",
            "default_width_m",
            "is_sewing_required",
            "segment",
            "tags",
            "sort_order",
            "is_active",
        )


class ProductReadSerializer(serializers.ModelSerializer):
    category_data = CategorySerializer(source="category", read_only=True)
    variants = ProductVariantReadSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "category_data",
            "name",
            "code",
            "description",
            "fabric_type",
            "pattern",
            "style",
            "transparency",
            "density",
            "composition",
            "care",
            "recommended_rooms",
            "recommended_coef",
            "default_width_m",
            "is_sewing_required",
            "segment",
            "tags",
            "sort_order",
            "is_active",
            "variants",
            "images",
            "created_at",
            "updated_at",
        )


class FasonPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = FasonPart
        fields = ("id", "role", "name", "width_share", "height_share", "default_coef", "sort_order")


class FasonAccessorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FasonAccessory
        fields = ("id", "category", "default_qty", "qty_formula")


class FasonReadSerializer(serializers.ModelSerializer):
    parts = FasonPartSerializer(many=True, read_only=True)
    accessories = FasonAccessorySerializer(many=True, read_only=True)

    class Meta:
        model = Fason
        fields = (
            "id",
            "name",
            "style",
            "rooms",
            "image",
            "part_count",
            "is_active",
            "parts",
            "accessories",
            "created_at",
            "updated_at",
        )


class FasonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fason
        fields = ("id", "name", "style", "rooms", "image", "part_count", "is_active")


class BulkPriceSerializer(serializers.Serializer):
    variant_ids = serializers.ListField(child=serializers.UUIDField())
    value = serializers.DecimalField(max_digits=14, decimal_places=2)
    type = serializers.ChoiceField(choices=["percent", "amount"])


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(validators=[validate_image_file])
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    alt = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(default=False)


class CatalogImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    dry_run = serializers.BooleanField(required=False, default=False)


class CatalogImportReportSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    skipped = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.DictField())
