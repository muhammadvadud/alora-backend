"""Usage statistika serializerlari."""

from __future__ import annotations

from rest_framework import serializers


class PeriodQuerySerializer(serializers.Serializer):
    """Statistika endpointlari uchun umumiy davr parametri."""

    period = serializers.ChoiceField(
        choices=(("day", "day"), ("week", "week"), ("month", "month")),
        default="day",
        required=False,
    )


class SummaryQuerySerializer(PeriodQuerySerializer):
    """`/usage/summary/` uchun so'rov parametrlari."""

    user = serializers.UUIDField(required=False, allow_null=True)


class SummarySerializer(serializers.Serializer):
    """Foydalanish xulosasi formati."""

    period = serializers.CharField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    tokens = serializers.IntegerField()
    cost_uzs = serializers.CharField()
    messages = serializers.IntegerField()
    conversations = serializers.IntegerField()


class ByUserItemSerializer(serializers.Serializer):
    """Xodimlar reytingidagi bitta qator."""

    user_id = serializers.CharField()
    full_name = serializers.CharField(allow_null=True, required=False)
    tokens = serializers.IntegerField()
    cost_uzs = serializers.CharField()
    messages = serializers.IntegerField()
    conversations = serializers.IntegerField()


class ConversationStatSerializer(serializers.Serializer):
    """Eng qimmat suhbatlar ro'yxatidagi bitta qator."""

    conversation_id = serializers.CharField()
    cost_uzs = serializers.CharField()
    tokens = serializers.IntegerField()
    messages = serializers.IntegerField()


class ConversionSerializer(serializers.Serializer):
    """Suhbat → buyurtma konversiyasi formati."""

    total_conversations = serializers.IntegerField()
    with_order = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)