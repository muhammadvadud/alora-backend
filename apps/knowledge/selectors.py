from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django.db.models import QuerySet

from apps.knowledge.models import KnowledgeRule


def _matches_condition(context: Mapping[str, Any], condition: Mapping[str, Any]) -> bool:
    """Kontekst shartga mos kelishini tekshiradi."""

    for key, expected in condition.items():
        actual = context.get(key)
        if isinstance(expected, Mapping):
            if not isinstance(actual, Mapping) or not _matches_condition(actual, expected):
                return False
            continue
        if isinstance(expected, Sequence) and not isinstance(expected, (str, bytes)):
            if actual not in expected:
                return False
            continue
        if actual != expected:
            return False
    return True


def select_matching_rules(context: Mapping[str, Any], *, kind: str | None = None) -> list[KnowledgeRule]:
    """Kontekstga mos qoidalarni priority bo'yicha qaytaradi."""

    queryset: QuerySet[KnowledgeRule] = KnowledgeRule.objects.filter(is_active=True)
    if kind:
        queryset = queryset.filter(kind=kind)
    queryset = queryset.order_by("-priority", "-created_at")
    matched: list[KnowledgeRule] = []
    for rule in queryset:
        condition = rule.condition or {}
        if not isinstance(condition, Mapping):
            continue
        if _matches_condition(context, condition):
            matched.append(rule)
    return matched
