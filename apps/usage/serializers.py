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


# --- Sotuv dashboard'i (`/analytics/dashboard/`) -----------------------------


class DashboardQuerySerializer(serializers.Serializer):
    """`period=day|week|month|custom`; `custom` uchun `date_from` (va ixtiyoriy `date_to`)."""

    period = serializers.ChoiceField(
        choices=(("day", "day"), ("week", "week"), ("month", "month"), ("custom", "custom")),
        default="day",
        required=False,
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs: dict) -> dict:
        if attrs.get("period") == "custom" and not attrs.get("date_from"):
            raise serializers.ValidationError({"date_from": "custom davr uchun date_from majburiy"})
        date_from, date_to = attrs.get("date_from"), attrs.get("date_to")
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({"date_to": "date_to date_from dan oldin bo'lmasin"})
        if date_from and date_to and (date_to - date_from).days > 366:
            raise serializers.ValidationError({"date_to": "davr 366 kundan oshmasin"})
        return attrs


class DashboardOrdersSerializer(serializers.Serializer):
    """Buyurtmalar bloki."""

    created = serializers.IntegerField()
    sold = serializers.IntegerField()
    completed = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    draft = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())


class DashboardSalesSerializer(serializers.Serializer):
    """Sotuv summalari (so'm, 2 kasr, matn)."""

    revenue = serializers.CharField()
    prepayment = serializers.CharField()
    balance_due = serializers.CharField()
    discount_total = serializers.CharField()
    delivery_total = serializers.CharField()
    average_check = serializers.CharField()


class DashboardConversationsSerializer(serializers.Serializer):
    """Suhbatlar va konversiya."""

    total = serializers.IntegerField()
    with_order = serializers.IntegerField()
    conversion_rate = serializers.CharField()


class DashboardAISerializer(serializers.Serializer):
    """AI xarajati (UsageDaily)."""

    tokens = serializers.IntegerField()
    cost_uzs = serializers.CharField()
    messages = serializers.IntegerField()


class DashboardTopProductSerializer(serializers.Serializer):
    """Eng ko'p sotilgan mato varianti."""

    variant_id = serializers.CharField()
    sku = serializers.CharField()
    name = serializers.CharField()
    color_name = serializers.CharField(allow_blank=True)
    area_sqm = serializers.CharField()
    revenue = serializers.CharField()
    orders = serializers.IntegerField()


class DashboardByUserSerializer(serializers.Serializer):
    """Xodim bo'yicha sotuv."""

    user_id = serializers.CharField()
    full_name = serializers.CharField(allow_null=True, required=False)
    orders = serializers.IntegerField()
    sold = serializers.IntegerField()
    revenue = serializers.CharField()


class DashboardDailySerializer(serializers.Serializer):
    """Kunlik qator (grafik)."""

    date = serializers.DateField()
    orders_created = serializers.IntegerField()
    orders_sold = serializers.IntegerField()
    revenue = serializers.CharField()


class DashboardPreviousSerializer(serializers.Serializer):
    """Oldingi davr bilan taqqoslash."""

    date_from = serializers.DateField()
    date_to = serializers.DateField()
    orders_created = serializers.IntegerField()
    revenue = serializers.CharField()
    conversations = serializers.IntegerField()
    orders_change_pct = serializers.CharField(allow_null=True)
    revenue_change_pct = serializers.CharField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    """`GET /analytics/dashboard/` javobi."""

    period = serializers.CharField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    orders = DashboardOrdersSerializer()
    sales = DashboardSalesSerializer()
    conversations = DashboardConversationsSerializer()
    ai = DashboardAISerializer()
    top_products = DashboardTopProductSerializer(many=True)
    by_user = DashboardByUserSerializer(many=True)
    daily = DashboardDailySerializer(many=True)
    previous = DashboardPreviousSerializer()
