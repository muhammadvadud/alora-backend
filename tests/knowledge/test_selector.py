from __future__ import annotations

from typing import Any

import pytest

from apps.knowledge.models import KnowledgeRule
from apps.knowledge.selectors import select_matching_rules
from apps.knowledge.serializers import KnowledgeRuleSyncSerializer


@pytest.fixture()
def knowledge_rules(db: Any) -> list[KnowledgeRule]:
    """Selector testlari uchun qoidalarni yaratadi."""

    return [
        KnowledgeRule.objects.create(
            kind="room_style",
            condition={"room": "wedding", "style": "classic"},
            recommendation="Klassik oq drape tavsiya qilinadi.",
            priority=10,
            is_active=True,
        ),
        KnowledgeRule.objects.create(
            kind="room_style",
            condition={"room": "wedding"},
            recommendation="To'y xonasi uchun yumshoq ranglar mos.",
            priority=5,
            is_active=True,
        ),
        KnowledgeRule.objects.create(
            kind="room_style",
            condition={"room": "office"},
            recommendation="Ofis uchun minimal uslub qulay.",
            priority=20,
            is_active=True,
        ),
        KnowledgeRule.objects.create(
            kind="room_style",
            condition={"room": "wedding", "style": "modern"},
            recommendation="Modern variant ham mumkin.",
            priority=30,
            is_active=False,
        ),
    ]


def test_select_matching_rules_orders_by_priority(knowledge_rules: list[KnowledgeRule]) -> None:
    """Mos qoidalar ustuvorlik bo'yicha qaytishini tekshiradi."""

    matched = select_matching_rules(
        {"room": "wedding", "style": "classic", "budget": "medium"}, kind="room_style"
    )

    assert [rule.priority for rule in matched] == [10, 5]


def test_select_matching_rules_supports_nested_conditions(db: Any) -> None:
    """Ichma-ich JSON shartlarni ham solishtiradi."""

    KnowledgeRule.objects.create(
        kind="general",
        condition={"room": {"type": "living", "season": "winter"}},
        recommendation="Qalin mato tavsiya qilinadi.",
        priority=15,
        is_active=True,
    )

    matched = select_matching_rules(
        {"room": {"type": "living", "season": "winter", "floor": 12}}, kind="general"
    )

    assert len(matched) == 1
    assert matched[0].recommendation == "Qalin mato tavsiya qilinadi."


def test_knowledge_sync_serializer_exposes_stable_fields(
    knowledge_rules: list[KnowledgeRule],
) -> None:
    """Go sinxron formati barqaror ekanini tekshiradi."""

    serializer = KnowledgeRuleSyncSerializer(knowledge_rules[0])

    assert set(serializer.data) == {
        "id",
        "kind",
        "condition",
        "recommendation",
        "priority",
        "is_active",
        "updated_at",
    }
