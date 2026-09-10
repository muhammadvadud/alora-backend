from django.contrib import admin

from .models import Category, Fason, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active", "created_at")
    list_filter = ("is_active", "tenant")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    readonly_fields = ("created_at", "updated_at")

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser and "cost_price" in fields:
            fields.remove("cost_price")
        return fields


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "tenant", "is_active", "created_at")
    list_filter = ("is_active", "category", "tenant")
    search_fields = ("name", "code")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProductVariantInline, ProductImageInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "tenant", "price", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("sku", "product__name")
    readonly_fields = ("created_at", "updated_at")

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if (
            not request.user.is_superuser
            and "cost_price" in fields
            and isinstance(fields, (list, tuple))
        ):
            fields = list(fields)
            fields.remove("cost_price")
        return fields


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "tenant", "is_active")
    list_filter = ("is_active", "tenant")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Fason)
class FasonAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active", "created_at")
    list_filter = ("is_active", "tenant")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
