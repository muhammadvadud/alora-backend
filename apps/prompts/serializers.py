"""System prompt versiyalari uchun serializerlar (Bosqich 11)."""

from __future__ import annotations

from rest_framework import serializers

from apps.prompts.models import PromptVersion


class PromptReadSerializer(serializers.ModelSerializer):
    """System prompt versiyasi uchun o'qish serializer'i."""

    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = PromptVersion
        fields = ("id", "version", "content", "author", "author_name", "is_current", "created_at")
        read_only_fields = fields


class PromptWriteSerializer(serializers.ModelSerializer):
    """Yangi system prompt versiyasi uchun yozish serializer'i."""

    class Meta:
        model = PromptVersion
        fields = ("content",)
        extra_kwargs = {
            "content": {"required": True},
        }
