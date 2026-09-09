"""Suhbat va xabarlar modellari."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.choices import ConversationMode, ConversationStage, MessageRole
from apps.common.models import BaseModel, TenantScopedModel


class ConversationStatus(models.TextChoices):
    ACTIVE = "active", _("Faol")
    ARCHIVED = "archived", _("Arxivlangan")


class Conversation(TenantScopedModel):
    """Suhbat modeli."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="conversations",
        verbose_name=_("Foydalanuvchi"),
    )
    session_id = models.CharField(
        max_length=255, unique=True, verbose_name=_("Sessiya ID")
    )
    title = models.CharField(
        max_length=255, blank=True, verbose_name=_("Suhbat sarlavhasi")
    )
    mode = models.CharField(
        max_length=20,
        choices=ConversationMode.choices,
        default=ConversationMode.SELLER,
        verbose_name=_("Rejim"),
    )
    status = models.CharField(
        max_length=20,
        choices=ConversationStatus.choices,
        default=ConversationStatus.ACTIVE,
        verbose_name=_("Holat"),
    )
    stage = models.CharField(
        max_length=20,
        choices=ConversationStage.choices,
        default=ConversationStage.NEED,
        verbose_name=_("Bosqich"),
    )
    context = models.JSONField(
        default=dict, blank=True, verbose_name=_("Kontekst")
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
        verbose_name=_("Buyurtma"),
    )
    started_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Boshlangan vaqti")
    )
    last_message_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Oxirgi xabar vaqti")
    )

    class Meta:
        verbose_name = _("Suhbat")
        verbose_name_plural = _("Suhbatlar")
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["tenant", "user"]),
        ]

    def __str__(self) -> str:
        return f"{self.title or 'Suhbat'} ({self.session_id})"


class Message(BaseModel):
    """Xabar modeli."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Suhbat"),
    )
    role = models.CharField(
        max_length=20, choices=MessageRole.choices, verbose_name=_("Rol")
    )
    content = models.TextField(blank=True, verbose_name=_("Matn"))
    tool_calls = models.JSONField(
        default=list, blank=True, verbose_name=_("Asbob chaqiruvlari")
    )
    tool_result = models.JSONField(
        default=dict, blank=True, verbose_name=_("Asbob natijasi")
    )
    audio_url = models.URLField(
        max_length=500, blank=True, verbose_name=_("Ovozli fayl havolasi")
    )
    tokens_in = models.IntegerField(default=0, verbose_name=_("Kiruvchi tokenlar"))
    tokens_out = models.IntegerField(default=0, verbose_name=_("Chiquvchi tokenlar"))

    class Meta:
        verbose_name = _("Xabar")
        verbose_name_plural = _("Xabarlar")
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:50]}"
