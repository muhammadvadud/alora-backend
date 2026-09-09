"""Suhbat serializerlari."""

from rest_framework import serializers

from apps.chat.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "id",
            "role",
            "content",
            "tool_calls",
            "tool_result",
            "audio_url",
            "created_at",
        )
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = (
            "id",
            "session_id",
            "title",
            "mode",
            "status",
            "stage",
            "order",
            "started_at",
            "last_message_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "session_id",
            "status",
            "stage",
            "started_at",
            "last_message_at",
            "created_at",
            "updated_at",
        )
