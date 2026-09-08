from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TenantScopedModel
from apps.common.choices import PriceUnit, CurtainPartRole, ProductSegment

class Category(TenantScopedModel):
    name = models.CharField(max_length=255, verbose_name=_("Nomi"))
    slug = models.SlugField(max_length=255, verbose_name=_("Slug"))
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children", verbose_name=_("Ota kategoriya")
    )
    sort_order = models.IntegerField(default=0, verbose_name=_("Tartib"))

    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")
        unique_together = (("tenant", "slug"),)
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name

class Product(TenantScopedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name=_("Kategoriya"))
    name = models.CharField(max_length=255, verbose_name=_("Nomi"))
    code = models.CharField(max_length=100, db_index=True, verbose_name=_("Artikul"))
    description = models.TextField(blank=True, verbose_name=_("Tavsifi"))
    
    fabric_type = models.CharField(max_length=100, blank=True, verbose_name=_("Mato turi"))
    pattern = models.CharField(max_length=100, blank=True, verbose_name=_("Naqsh/Gul"))
    style = models.CharField(max_length=100, blank=True, verbose_name=_("Uslub"))
    transparency = models.CharField(max_length=100, blank=True, verbose_name=_("Shaffoflik"))
    density = models.CharField(max_length=50, blank=True, verbose_name=_("Zichlik"))
    composition = models.CharField(max_length=255, blank=True, verbose_name=_("Tarkibi"))
    care = models.TextField(blank=True, verbose_name=_("Parvarish qilish"))
    
    recommended_rooms = models.JSONField(default=list, blank=True, verbose_name=_("Tavsiya etilgan xonalar"))
    recommended_coef = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_("Burma koeffitsienti"))
    default_width_m = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_("Standart kenglik (m)"))
    
    is_sewing_required = models.BooleanField(default=True, verbose_name=_("Tikuv talab etiladimi"))
    segment = models.CharField(max_length=50, blank=True, choices=ProductSegment.choices, db_index=True, verbose_name=_("Segment"))
    tags = models.JSONField(default=list, blank=True, verbose_name=_("Teglar"))
    sort_order = models.IntegerField(default=0, verbose_name=_("Tartib"))

    class Meta:
        verbose_name = _("Mahsulot")
        verbose_name_plural = _("Mahsulotlar")
        unique_together = (("tenant", "code"),)
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

class ProductVariant(TenantScopedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants", verbose_name=_("Mahsulot"))
    sku = models.CharField(max_length=100, db_index=True, verbose_name=_("SKU"))
    color_name = models.CharField(max_length=100, verbose_name=_("Rang nomi"))
    color_hex = models.CharField(max_length=20, blank=True, verbose_name=_("Rang kodi (HEX)"))
    width_m = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_("Kenglik (m)"))
    price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name=_("Narx"))
    price_unit = models.CharField(max_length=20, choices=PriceUnit.choices, default=PriceUnit.PER_SQM, verbose_name=_("Narx birligi"))
    old_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name=_("Eski narx"))
    cost_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name=_("Tannarx"))

    class Meta:
        verbose_name = _("Mahsulot varianti")
        verbose_name_plural = _("Mahsulot variantlari")
        unique_together = (("tenant", "sku"),)

    def __str__(self) -> str:
        return f"{self.product.name} - {self.color_name} ({self.sku})"

class ProductImage(TenantScopedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", null=True, blank=True, verbose_name=_("Mahsulot"))
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images", null=True, blank=True, verbose_name=_("Variant"))
    image = models.ImageField(upload_to="catalog/products/%Y/%m/", verbose_name=_("Rasm"))
    alt = models.CharField(max_length=255, blank=True, verbose_name=_("Muqobil matn"))
    sort_order = models.IntegerField(default=0, verbose_name=_("Tartib"))
    is_primary = models.BooleanField(default=False, verbose_name=_("Asosiy rasm"))

    class Meta:
        verbose_name = _("Mahsulot rasmi")
        verbose_name_plural = _("Mahsulot rasmlari")
        ordering = ("sort_order", "id")

class Fason(TenantScopedModel):
    name = models.CharField(max_length=255, verbose_name=_("Nomi"))
    style = models.CharField(max_length=100, blank=True, verbose_name=_("Uslub"))
    rooms = models.JSONField(default=list, blank=True, verbose_name=_("Xonalar"))
    image = models.ImageField(upload_to="catalog/fasons/%Y/%m/", null=True, blank=True, verbose_name=_("Namuna rasm"))
    part_count = models.IntegerField(default=1, verbose_name=_("Bo'laklar soni"))

    class Meta:
        verbose_name = _("Fason")
        verbose_name_plural = _("Fasonlar")

    def __str__(self) -> str:
        return self.name

class FasonPart(TenantScopedModel):
    fason = models.ForeignKey(Fason, on_delete=models.CASCADE, related_name="parts", verbose_name=_("Fason"))
    role = models.CharField(max_length=20, choices=CurtainPartRole.choices, verbose_name=_("Rol"))
    name = models.CharField(max_length=255, verbose_name=_("Nomi"))
    width_share = models.DecimalField(max_digits=8, decimal_places=3, default="1.000", verbose_name=_("Kenglik ulushi"))
    height_share = models.DecimalField(max_digits=8, decimal_places=3, default="1.000", verbose_name=_("Balandlik ulushi"))
    default_coef = models.DecimalField(max_digits=8, decimal_places=3, default="2.000", verbose_name=_("Standart burma koeffitsienti"))
    sort_order = models.IntegerField(default=0, verbose_name=_("Tartib"))

    class Meta:
        verbose_name = _("Fason bo'lagi")
        verbose_name_plural = _("Fason bo'laklari")
        ordering = ("sort_order",)

class FasonAccessory(TenantScopedModel):
    fason = models.ForeignKey(Fason, on_delete=models.CASCADE, related_name="accessories", verbose_name=_("Fason"))
    category = models.CharField(max_length=100, verbose_name=_("Kategoriya"))
    default_qty = models.DecimalField(max_digits=8, decimal_places=3, default="1.000", verbose_name=_("Standart miqdor"))
    qty_formula = models.CharField(max_length=255, blank=True, verbose_name=_("Miqdor formulasi"))

    class Meta:
        verbose_name = _("Fason aksessuari")
        verbose_name_plural = _("Fason aksessuarlari")
