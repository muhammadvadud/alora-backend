"""Bilim qoidalari ATAYLAB global (tenant'siz).

Sabab: loyiha bitta do'kon uchun mo'ljallangan. Qaror sanasi: 2026-09-10.
Ikkinchi tenant qo'shilsa bu qaror qayta ko'rib chiqilishi SHART —
`docs/ADR-001-pricing-global.md` ga qarang.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class KnowledgeRule(BaseModel):
    """Sotuv bilimlari uchun qoida."""

    class Kind(models.TextChoices):
        """Qoidalar turlari."""

        ROOM_STYLE = "room_style", _("Xona va uslub")
        LIGHT = "light", _("Yorug'lik")
        COLOR = "color", _("Rang")
        CONSTRUCTION = "construction", _("Konstruktsiya")
        OBJECTION = "objection", _("E'tiroz")
        GENERAL = "general", _("Umumiy")

    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True, verbose_name=_("Turi"))
    condition = models.JSONField(default=dict, blank=True, verbose_name=_("Shart"))
    recommendation = models.TextField(verbose_name=_("Tavsiya"))
    priority = models.PositiveIntegerField(default=0, db_index=True, verbose_name=_("Ustuvorlik"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Faol"))

    class Meta:
        verbose_name = _("Bilim qoidasi")
        verbose_name_plural = _("Bilim qoidalari")
        ordering = ("-priority", "-created_at")

    def __str__(self) -> str:
        return f"{self.kind}#{self.priority}"
