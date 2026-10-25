"""Narx qoidalari ATAYLAB global (tenant'siz).

Sabab: loyiha bitta do'kon uchun mo'ljallangan. Qaror sanasi: 2026-09-10.
Ikkinchi tenant qo'shilsa bu qaror qayta ko'rib chiqilishi SHART —
`docs/ADR-001-pricing-global.md` ga qarang.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.choices import PriceUnit
from apps.common.models import BaseModel

NON_NEGATIVE_MESSAGE = _("0 dan kichik bo'lishi mumkin emas")


class CalcRule(BaseModel):
    """Hisoblash qoidasi va koeffitsienti."""

    key = models.CharField(max_length=64, unique=True, verbose_name=_("Kalit"))
    value = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Qiymat"),
    )
    unit = models.CharField(max_length=32, verbose_name=_("Birlik"))
    description = models.TextField(blank=True, verbose_name=_("Izoh"))
    applies_to = models.JSONField(default=dict, blank=True, verbose_name=_("Qo'llanish sharti"))

    class Meta:
        verbose_name = _("Hisob qoidasi")
        verbose_name_plural = _("Hisob qoidalari")
        ordering = ("key",)

    def __str__(self) -> str:
        return f"{self.key}={self.value}"


class ServicePrice(BaseModel):
    """Xizmat narxi."""

    key = models.CharField(max_length=64, unique=True, verbose_name=_("Kalit"))
    name = models.CharField(max_length=255, verbose_name=_("Nomi"))
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Narx"),
    )
    unit = models.CharField(max_length=20, choices=PriceUnit.choices, verbose_name=_("Birlik"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Faol"))

    class Meta:
        verbose_name = _("Xizmat narxi")
        verbose_name_plural = _("Xizmat narxlari")
        ordering = ("key",)

    def __str__(self) -> str:
        return f"{self.key} ({self.price})"


class DiscountTier(BaseModel):
    """Summaga qarab o'sadigan chegirma bosqichi."""

    min_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Minimal summa"),
    )
    percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Foiz"),
    )
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Faol"))

    class Meta:
        verbose_name = _("Chegirma bosqichi")
        verbose_name_plural = _("Chegirma bosqichlari")
        ordering = ("min_amount",)

    def __str__(self) -> str:
        return f"{self.min_amount} -> {self.percent}%"


class DiscountPolicy(BaseModel):
    """Qo'lda chegirma qoidalari."""

    manual_max_percent_employee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Xodim uchun maksimal qo'lda chegirma"),
    )
    manual_max_percent_manager = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Menejer uchun maksimal qo'lda chegirma"),
    )
    stack_with_tier = models.BooleanField(
        default=True, verbose_name=_("Bosqichli chegirma bilan qo'shiladi")
    )

    class Meta:
        verbose_name = _("Chegirma siyosati")
        verbose_name_plural = _("Chegirma siyosati")

    def __str__(self) -> str:
        return "Chegirma siyosati"


class OrderDefaults(BaseModel):
    """Buyurtma uchun standart qiymatlar."""

    prepayment_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Avans foizi"),
    )
    delivery_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Yetkazish narxi"),
    )
    deadline_days = models.PositiveIntegerField(verbose_name=_("Muddat (kun)"))

    class Meta:
        verbose_name = _("Buyurtma sozlamalari")
        verbose_name_plural = _("Buyurtma sozlamalari")

    def __str__(self) -> str:
        return "Buyurtma sozlamalari"


class ModelPricing(BaseModel):
    """LLM, STT va TTS narxlari."""

    provider = models.CharField(max_length=64, verbose_name=_("Provayder"))
    model = models.CharField(max_length=128, verbose_name=_("Model"))
    input_per_1m = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Kirish narxi / 1M"),
    )
    output_per_1m = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Chiqish narxi / 1M"),
    )
    cached_input_per_1m = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("Kesh kirish narxi / 1M"),
    )
    stt_per_minute = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("STT narxi / daqiqa"),
    )
    tts_per_1k_chars = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("TTS narxi / 1K belgi"),
    )
    usd_to_uzs = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0), message=NON_NEGATIVE_MESSAGE)],
        verbose_name=_("USD/UZS kursi"),
    )

    class Meta:
        verbose_name = _("Model narxlari")
        verbose_name_plural = _("Model narxlari")
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "model"), name="pricing_modelpricing_provider_model_uniq"
            )
        ]
        ordering = ("provider", "model")

    def __str__(self) -> str:
        return f"{self.provider}:{self.model}"
