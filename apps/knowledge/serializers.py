from __future__ import annotations

from rest_framework import serializers

from apps.knowledge.models import KnowledgeRule


class KnowledgeRuleReadSerializer(serializers.ModelSerializer):
    """Bilim qoidasi uchun o'qish serializer'i."""

    class Meta:
        model = KnowledgeRule
        fields = ("id", "kind", "condition", "recommendation", "priority", "is_active", "created_at", "updated_at")


class KnowledgeRuleWriteSerializer(serializers.ModelSerializer):
    """Bilim qoidasi uchun yozish serializer'i."""

    class Meta:
        model = KnowledgeRule
        fields = ("kind", "condition", "recommendation", "priority", "is_active")
        extra_kwargs = {
            "kind": {"required": True},
            "condition": {"required": False},
            "recommendation": {"required": True},
            "priority": {"required": False},
            "is_active": {"required": False},
        }


class KnowledgeRuleSyncSerializer(serializers.ModelSerializer):
    """Go bilan sinxronlash uchun serializatsiya formati."""

    class Meta:
        model = KnowledgeRule
        fields = ("id", "kind", "condition", "recommendation", "priority", "is_active", "updated_at")
