"""buyurtmalar ilovasi modellari."""

from __future__ import annotations

from typing import ClassVar

from django.db import models
from django.db.models.expressions import Func, Value
from django.utils.translation import gettext_lazy as _

from apps.common.choices import CurtainPartRole, OrderStatus, PaymentStatus, PriceUnit
from apps.common.models import BaseModel, TenantScopedModel

#: Buyurtma tartib raqami uchun PostgreSQL sequence nomi.
ORDER_NUMBER_SEQUENCE = "orders_order_number_seq"


def order_number_seq_default() -> Func:
    """`nextval('orders_order_number_seq')` — DB darajasidagi poyga-holatsiz hisoblagich."""

    return Func(
        Value(ORDER_NUMBER_SEQUENCE),
        function="nextval",
        output_field=models.PositiveBigIntegerField(),
    )


class DiscountSource(models.TextChoices):
    """Chegirma manbai."""

    TIER = "tier", _("Bosqich bo'yicha")
    MANUAL = "manual", _("Qo'lda")


class Order(TenantScopedModel):
    """Buyurtma.

    Buyurtmadagi narx va nomlar snapshot qilinadi: katalogda narx o'zgarsa
    ham eski buyurtma o'zgarmaydi (TZ 3.6, rules 1.3).
    """

    number = models.CharField(max_length=20, unique=True, db_index=True, verbose_name=_("Raqam"))
    number_seq = models.PositiveBigIntegerField(
        editable=False,
        unique=True,
        db_index=True,
        db_default=order_number_seq_default(),
        verbose_name=_("Tartib raqami"),
    )
    conversation = models.ForeignKey(
        "chat.Conversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Suhbat"),
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("Sotuvchi"),
    )
    customer_name = models.CharField(max_length=255, verbose_name=_("Mijoz ismi"))
    customer_phone = models.CharField(max_length=20, verbose_name=_("Mijoz telefoni"))
    address = models.TextField(blank=True, verbose_name=_("Manzil"))
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
        db_index=True,
        verbose_name=_("Holat"),
    )
    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00", verbose_name=_("Yakuniy summa")
    )
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default="0.00", verbose_name=_("Chegirma foizi")
    )
    discount_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00", verbose_name=_("Chegirma summasi")
    )
    discount_source = models.CharField(
        max_length=10,
        choices=DiscountSource.choices,
        default=DiscountSource.TIER,
        verbose_name=_("Chegirma manbai"),
    )
    delivery_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00", verbose_name=_("Yetkazish narxi")
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00", verbose_name=_("Jami")
    )
    prepayment_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default="0.00", verbose_name=_("Avans foizi")
    )
    prepayment = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00", verbose_name=_("Avans summasi")
    )
    balance = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00", verbose_name=_("Qoldiq")
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
        verbose_name=_("To'lov holati"),
    )
    deadline_date = models.DateField(null=True, blank=True, verbose_name=_("Muddat"))
    note = models.TextField(blank=True, verbose_name=_("Izoh"))
    confirmed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_orders",
        verbose_name=_("Tasdiqlagan"),
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Tasdiqlangan vaqt"))

    class Meta:
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")
        ordering = ("-created_at",)
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["number"], name="orders_orde_number_idx")
        ]

    def __str__(self) -> str:
        return f"{self.number} — {self.customer_name}"


class OrderMeasurement(BaseModel):
    """Bitta buyurtmadagi bitta deraza/xona o'lchovi."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="measurements",
        verbose_name=_("Buyurtma"),
    )
    room_name = models.CharField(max_length=255, verbose_name=_("Xona nomi"))
    cornice_length_m = models.DecimalField(
        max_digits=8, decimal_places=3, verbose_name=_("Karniz uzunligi (m)")
    )
    height_m = models.DecimalField(max_digits=8, decimal_places=3, verbose_name=_("Balandlik (m)"))
    layers = models.JSONField(default=list, blank=True, verbose_name=_("Qatlamlar"))
    coefficient = models.DecimalField(
        max_digits=8, decimal_places=3, verbose_name=_("Burma koeffitsienti")
    )
    note = models.TextField(blank=True, verbose_name=_("Izoh"))

    class Meta:
        verbose_name = _("Buyurtma o'lchovi")
        verbose_name_plural = _("Buyurtma o'lchovlari")

    def __str__(self) -> str:
        return f"{self.room_name} ({self.order.number})"


class OrderCurtainPart(BaseModel):
    """Bitta pardadagi bitta mato bo'lagi (1..10 tagacha)."""

    measurement = models.ForeignKey(
        OrderMeasurement,
        on_delete=models.CASCADE,
        related_name="parts",
        verbose_name=_("O'lchov"),
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_parts",
        verbose_name=_("Variant"),
    )
    role = models.CharField(max_length=20, choices=CurtainPartRole.choices, verbose_name=_("Rol"))
    width_m = models.DecimalField(max_digits=8, decimal_places=3, verbose_name=_("Kenglik (m)"))
    height_m = models.DecimalField(max_digits=8, decimal_places=3, verbose_name=_("Balandlik (m)"))
    coefficient = models.DecimalField(
        max_digits=8, decimal_places=3, verbose_name=_("Burma koeffitsienti")
    )
    area_sqm = models.DecimalField(max_digits=8, decimal_places=3, verbose_name=_("Yuza (m²)"))
    price_per_sqm = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name=_("1 m² narxi")
    )
    total = models.DecimalField(max_digits=14, decimal_places=2, verbose_name=_("Summa"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Tartib"))

    class Meta:
        verbose_name = _("Buyurtma parda bo'lagi")
        verbose_name_plural = _("Buyurtma parda bo'laklari")
        ordering = ("sort_order",)

    def __str__(self) -> str:
        return f"{self.variant.sku} ({self.role})"


class OrderAccessory(BaseModel):
    """Pardaga qo'shiladigan bezak va furnitura."""

    measurement = models.ForeignKey(
        OrderMeasurement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="accessories",
        verbose_name=_("O'lchov"),
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_accessories",
        verbose_name=_("Variant"),
    )
    qty = models.DecimalField(max_digits=8, decimal_places=3, verbose_name=_("Miqdor"))
    unit = models.CharField(max_length=20, choices=PriceUnit.choices, verbose_name=_("Birlik"))
    unit_price = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name=_("Bir birlik narxi")
    )
    total = models.DecimalField(max_digits=14, decimal_places=2, verbose_name=_("Summa"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Tartib"))

    class Meta:
        verbose_name = _("Buyurtma aksessuari")
        verbose_name_plural = _("Buyurtma aksessuarlari")
        ordering = ("sort_order",)

    def __str__(self) -> str:
        return f"{self.variant.sku} x{self.qty}"


class OrderItem(BaseModel):
    """Xizmat qatori (tikuv, montaj, yetkazish, tasma, ilgich)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Buyurtma"),
    )
    measurement = models.ForeignKey(
        OrderMeasurement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="service_items",
        verbose_name=_("O'lchov"),
    )
    service_key = models.CharField(max_length=64, verbose_name=_("Xizmat kaliti"))
    name_snapshot = models.CharField(max_length=255, verbose_name=_("Nomi (snapshot)"))
    qty = models.DecimalField(max_digits=8, decimal_places=3, verbose_name=_("Miqdor"))
    unit = models.CharField(max_length=20, choices=PriceUnit.choices, verbose_name=_("Birlik"))
    unit_price = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name=_("Bir birlik narxi")
    )
    total = models.DecimalField(max_digits=14, decimal_places=2, verbose_name=_("Summa"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Tartib"))

    class Meta:
        verbose_name = _("Buyurtma xizmati")
        verbose_name_plural = _("Buyurtma xizmatlari")
        ordering = ("sort_order",)

    def __str__(self) -> str:
        return f"{self.name_snapshot} x{self.qty}"
