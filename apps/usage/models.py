"""Usage ilovasi modellari — tokenlar, xarajat va limitlar."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.choices import OnExceed, UsagePeriod, UserRole
from apps.common.models import BaseModel, TenantScopedModel

MONEY_MAX_DIGITS = 14
MONEY_DECIMAL_PLACES = 2


class UsageRecord(TenantScopedModel):
    """Bitta AI chaqiruvining token va xarajat qaydnomasi."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_records",
        verbose_name=_("Foydalanuvchi"),
    )
    # Bosqich 7 dagi Conversation modeli hozircha mavjud emas.
    # Kuchli FK o'rniga suhbat UUID si saqlanadi va kerak bo'lganda
    # apps.get_model orqali kech bog'lanadi.
    conversation = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Suhbat ID"),
    )
    message_id = models.UUIDField(null=True, blank=True, verbose_name=_("Xabar ID"))
    provider = models.CharField(max_length=64, blank=True, default="", verbose_name=_("Provayder"))
    model = models.CharField(max_length=128, blank=True, default="", verbose_name=_("Model"))
    prompt_tokens = models.PositiveIntegerField(default=0, verbose_name=_("Kirish tokenlari"))
    completion_tokens = models.PositiveIntegerField(default=0, verbose_name=_("Chiqish tokenlari"))
    cached_tokens = models.PositiveIntegerField(default=0, verbose_name=_("Kesh tokenlari"))
    reasoning_tokens = models.PositiveIntegerField(default=0, verbose_name=_("Fikrlash tokenlari"))
    stt_seconds = models.PositiveIntegerField(default=0, verbose_name=_("STT soniyalari"))
    tts_chars = models.PositiveIntegerField(default=0, verbose_name=_("TTS belgilari"))
    tool_calls = models.JSONField(default=list, blank=True, verbose_name=_("Asbob chaqiruvlari"))
    latency_ms = models.PositiveIntegerField(default=0, verbose_name=_("Kechikish (ms)"))
    cost_usd = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal(0),
        verbose_name=_("Xarajat (USD)"),
    )
    cost_uzs = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal(0),
        verbose_name=_("Xarajat (UZS)"),
    )

    class Meta:
        verbose_name = _("Foydalanish qaydnomasi")
        verbose_name_plural = _("Foydalanish qaydnomalari")
        ordering = ("-created_at",)
        constraints = (
            models.UniqueConstraint(
                fields=("user", "message_id"),
                condition=models.Q(message_id__isnull=False),
                name="usage_user_message_uniq",
            ),
        )

    def __str__(self) -> str:
        return f"{self.user_id} · {self.model} · {self.cost_uzs} UZS"


class UsageDaily(TenantScopedModel):
    """Kunlik yig'ma (rollup) jadvali — statistika shundan o'qiladi."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_daily",
        verbose_name=_("Foydalanuvchi"),
    )
    date = models.DateField(verbose_name=_("Sana"))
    tokens = models.PositiveBigIntegerField(default=0, verbose_name=_("Tokenlar"))
    cost_uzs = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal(0),
        verbose_name=_("Xarajat (UZS)"),
    )
    messages_count = models.PositiveIntegerField(default=0, verbose_name=_("Xabarlar soni"))
    conversations_count = models.PositiveIntegerField(default=0, verbose_name=_("Suhbatlar soni"))

    class Meta:
        verbose_name = _("Kunlik yig'ma")
        verbose_name_plural = _("Kunlik yig'malar")
        ordering = ("-date",)
        constraints = (
            models.UniqueConstraint(fields=("user", "date"), name="usage_daily_user_date_uniq"),
        )

    def __str__(self) -> str:
        return f"{self.user_id} · {self.date} · {self.tokens} token"


class UsageLimit(BaseModel):
    """Xodim yoki rol uchun global foydalanish limiti.

    Bu model ataylab tenantsiz qolgan: loyiha hozircha bitta do'kon uchun.
    Ikkinchi tenant qo'shilsa qaror qayta ko'rib chiqilishi shart —
    `docs/ADR-001-pricing-global.md` ga qarang.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="usage_limits",
        verbose_name=_("Foydalanuvchi"),
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        blank=True,
        null=True,
        verbose_name=_("Rol"),
    )
    period = models.CharField(
        max_length=20,
        choices=UsagePeriod.choices,
        default=UsagePeriod.DAILY,
        verbose_name=_("Davr"),
    )
    is_unlimited = models.BooleanField(default=False, verbose_name=_("Cheksiz"))
    max_tokens = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("Maksimal tokenlar")
    )
    max_cost_uzs = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        null=True,
        blank=True,
        verbose_name=_("Maksimal xarajat (UZS)"),
    )
    max_messages = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Maksimal xabarlar")
    )
    on_exceed = models.CharField(
        max_length=20,
        choices=OnExceed.choices,
        default=OnExceed.BLOCK,
        verbose_name=_("Oshganda"),
    )
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Faol"))

    class Meta:
        verbose_name = _("Foydalanish limiti")
        verbose_name_plural = _("Foydalanish limitlari")
        ordering = ("-created_at",)
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, role__isnull=True)
                    | models.Q(user__isnull=True, role__isnull=False)
                ),
                name="usage_limit_user_or_role",
            ),
        )

    def __str__(self) -> str:
        target = f"@{self.user_id}" if self.user_id else f"@role:{self.role}"
        return f"{self.period} · {target}"
