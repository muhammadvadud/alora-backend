from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    ChoicesRadioFilter,
    RangeDateTimeFilter,
)
from unfold.decorators import display

from .models import (
    Category,
    Fason,
    FasonAccessory,
    FasonPart,
    Product,
    ProductImage,
    ProductVariant,
)


def _fmt_uzs(value) -> str:
    return f"{value:,.2f} UZS" if value is not None else "—"


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "parent", "slug", "sort_order", "is_active", "created_at")
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("parent", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Kategoriya"),
            {"fields": ("name", "slug", "parent", "sort_order")},
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 0
    readonly_fields = ("created_at", "updated_at")

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser and "cost_price" in fields:
            fields.remove("cost_price")
        return fields


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "code", "category", "segment_badge", "is_active", "created_at")
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("segment", ChoicesDropdownFilter),
        ("category", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("name", "code")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProductVariantInline, ProductImageInline]
    fieldsets = (
        (
            _("Asosiy ma'lumotlar"),
            {"fields": ("category", "name", "code", "description", "segment")},
        ),
        (
            _("Texnik xususiyatlar"),
            {
                "fields": (
                    "fabric_type",
                    "pattern",
                    "style",
                    "transparency",
                    "density",
                    "composition",
                    "care",
                )
            },
        ),
        (
            _("Sotuv sozlamalari"),
            {
                "fields": (
                    "recommended_rooms",
                    "recommended_coef",
                    "default_width_m",
                    "is_sewing_required",
                    "tags",
                    "sort_order",
                )
            },
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(
        description=_("Segment"),
        label={"economy": "info", "standard": "primary", "premium": "warning"},
        empty_value="—",
    )
    def segment_badge(self, obj: Product) -> tuple[str, str]:
        return obj.segment, obj.get_segment_display()


@admin.register(ProductVariant)
class ProductVariantAdmin(ModelAdmin):
    list_display = (
        "sku",
        "product",
        "color_name",
        "price_display",
        "price_unit_badge",
        "is_active",
    )
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("price_unit", ChoicesDropdownFilter),
        ("product", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("sku", "product__name", "color_name")
    readonly_fields = ("created_at", "updated_at", "cost_price_display")
    fieldsets = (
        (
            _("Variant ma'lumotlari"),
            {
                "fields": (
                    "product",
                    "sku",
                    "color_name",
                    "color_hex",
                    "width_m",
                    "price",
                    "price_unit",
                    "old_price",
                )
            },
        ),
        (
            _("Tannarx (faqat admin)"),
            {"fields": ("cost_price", "cost_price_display")},
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser and "cost_price" in fields:
            fields.remove("cost_price")
        return fields

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display + ("cost_price",)
        return self.list_display

    @display(description=_("Tannarx"))
    def cost_price_display(self, obj: ProductVariant) -> str:
        return _fmt_uzs(obj.cost_price)

    @display(description=_("Narx"))
    def price_display(self, obj: ProductVariant) -> str:
        return _fmt_uzs(obj.price)

    @display(
        description=_("Narx birligi"),
        label={"per_sqm": "primary", "per_piece": "info", "per_meter": "warning"},
    )
    def price_unit_badge(self, obj: ProductVariant) -> tuple[str, str]:
        return obj.price_unit, obj.get_price_unit_display()


@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ("product", "variant", "is_primary", "sort_order", "is_active")
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("is_primary", ChoicesRadioFilter),
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Rasm"),
            {"fields": ("product", "variant", "image", "alt", "is_primary", "sort_order")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )


class FasonPartInline(TabularInline):
    model = FasonPart
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("name", "role", "width_share", "height_share", "default_coef", "sort_order")


class FasonAccessoryInline(TabularInline):
    model = FasonAccessory
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("category", "default_qty", "qty_formula")


@admin.register(Fason)
class FasonAdmin(ModelAdmin):
    list_display = ("name", "style", "part_count", "is_active", "created_at")
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("name", "style")
    readonly_fields = ("created_at", "updated_at")
    inlines = [FasonPartInline, FasonAccessoryInline]
    fieldsets = (
        (
            _("Fason ma'lumotlari"),
            {"fields": ("name", "style", "rooms", "image", "part_count")},
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )
