"""System prompt versiyalari modellari (Bosqich 11)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class PromptVersion(BaseModel):
    """System promptning bitta versiyasi.

    Har bir versiya o'zgarmas audit yozuvi hisoblanadi: o'chirilmaydi va matni
    tahrirlanmaydi. Bir vaqtda faqat bitta versiya joriy (`is_current=True`)
    bo'ladi — bu DB darajasidagi qisman UniqueConstraint bilan kafolatlangan
    (11.1-band).
    """

    version = models.PositiveIntegerField(unique=True, verbose_name=_("Versiya raqami"))
    content = models.TextField(verbose_name=_("Matn"))
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="prompt_versions",
        verbose_name=_("Muallif"),
    )
    is_current = models.BooleanField(default=False, db_index=True, verbose_name=_("Joriy"))

    class Meta:
        verbose_name = _("System prompt versiyasi")
        verbose_name_plural = _("System prompt versiyalari")
        ordering = ("-version",)
        constraints = (
            models.UniqueConstraint(
                fields=("is_current",),
                condition=models.Q(is_current=True),
                name="prompt_version_single_current",
            ),
        )

    def __str__(self) -> str:
        return f"System prompt v{self.version}"
