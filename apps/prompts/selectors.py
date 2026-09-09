"""System prompt versiyalarini o'qish selektorlari (Bosqich 11)."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.prompts.models import PromptVersion


def get_prompt_history() -> QuerySet[PromptVersion]:
    """Barcha versiyalarni yangisidan eskisiga tartibda qaytaradi.

    N+1 ning oldini olish uchun `author` oldindan yuklanadi (rules.md 4.10).
    """

    return PromptVersion.objects.select_related("author").order_by("-version")
