from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.common.choices import CurtainPartRole
from apps.pricing.models import (
    CalcRule,
    DiscountPolicy,
    DiscountTier,
    ModelPricing,
    OrderDefaults,
    ServicePrice,
)

ZERO = Decimal(0)


class CalcRuleSerializer(serializers.ModelSerializer):
    """Hisob qoidasi uchun o'qish serializer'i."""

    class Meta:
        model = CalcRule
        fields = (
            "id",
            "key",
            "value",
            "unit",
            "description",
            "applies_to",
            "is_active",
            "created_at",
            "updated_at",
        )


class CalcRuleWriteSerializer(serializers.ModelSerializer):
    """Hisob qoidasi uchun yozish serializer'i."""

    class Meta:
        model = CalcRule
        fields = ("key", "value", "unit", "description", "applies_to", "is_active")
        extra_kwargs = {
            "key": {"required": True},
            "value": {"required": False},
            "unit": {"required": False},
            "description": {"required": False, "allow_blank": True},
            "applies_to": {"required": False},
            "is_active": {"required": False},
        }


class ServicePriceSerializer(serializers.ModelSerializer):
    """Xizmat narxi uchun o'qish serializer'i."""

    class Meta:
        model = ServicePrice
        fields = ("id", "key", "name", "price", "unit", "is_active", "created_at", "updated_at")


class ServicePriceWriteSerializer(serializers.ModelSerializer):
    """Xizmat narxi uchun yozish serializer'i."""

    price = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=ZERO,
        error_messages={"min_value": "0 dan kichik bo'lishi mumkin emas"},
    )

    class Meta:
        model = ServicePrice
        fields = ("key", "name", "price", "unit", "is_active")
        extra_kwargs = {
            "key": {"required": True},
            "name": {"required": False, "allow_blank": True},
            "unit": {"required": False},
            "is_active": {"required": False},
        }


class DiscountTierSerializer(serializers.ModelSerializer):
    """Chegirma bosqichi uchun serializer."""

    class Meta:
        model = DiscountTier
        fields = ("id", "min_amount", "percent", "is_active", "created_at", "updated_at")


class DiscountPolicySerializer(serializers.ModelSerializer):
    """Chegirma siyosati serializer'i."""

    class Meta:
        model = DiscountPolicy
        fields = (
            "id",
            "manual_max_percent_employee",
            "manual_max_percent_manager",
            "stack_with_tier",
            "created_at",
            "updated_at",
        )


class OrderDefaultsSerializer(serializers.ModelSerializer):
    """Buyurtma standartlari serializer'i."""

    class Meta:
        model = OrderDefaults
        fields = (
            "id",
            "prepayment_percent",
            "delivery_amount",
            "deadline_days",
            "created_at",
            "updated_at",
        )


class ModelPricingSerializer(serializers.ModelSerializer):
    """Model narxlari serializer'i."""

    class Meta:
        model = ModelPricing
        fields = (
            "id",
            "provider",
            "model",
            "input_per_1m",
            "output_per_1m",
            "cached_input_per_1m",
            "stt_per_minute",
            "tts_per_1k_chars",
            "usd_to_uzs",
            "is_active",
            "created_at",
            "updated_at",
        )


class PreviewPartInputSerializer(serializers.Serializer):
    """Kalkulyatsiya bo'lagi kirish ma'lumoti."""

    variant_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=CurtainPartRole.choices)
    width_m = serializers.DecimalField(max_digits=8, decimal_places=3, min_value=ZERO)
    height_m = serializers.DecimalField(
        max_digits=8,
        decimal_places=3,
        min_value=ZERO,
        required=False,
        allow_null=True,
    )
    coef = serializers.DecimalField(
        max_digits=8, decimal_places=3, min_value=ZERO, required=False, allow_null=True
    )


class PreviewAccessoryInputSerializer(serializers.Serializer):
    """Kalkulyatsiya aksessuar kirish ma'lumoti."""

    variant_id = serializers.UUIDField()
    qty = serializers.DecimalField(max_digits=8, decimal_places=3, min_value=ZERO)


class PreviewMeasurementInputSerializer(serializers.Serializer):
    """Bitta o'lchov uchun kirish serializer'i."""

    length = serializers.DecimalField(max_digits=8, decimal_places=3, min_value=ZERO)
    height = serializers.DecimalField(max_digits=8, decimal_places=3, min_value=ZERO)
    parts = PreviewPartInputSerializer(many=True)
    accessories = PreviewAccessoryInputSerializer(many=True, required=False, default=list)


class PreviewRequestSerializer(serializers.Serializer):
    """Preview endpoint kirish formati."""

    measurements = PreviewMeasurementInputSerializer(many=True)
    services = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True, default=list
    )
    discount_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=ZERO,
        required=False,
        default=ZERO,
    )
    delivery = serializers.BooleanField(required=False, default=False)


class PreviewResultSerializer(serializers.Serializer):
    """Preview javob formati."""

    measurements = serializers.ListField(child=serializers.DictField())
    services = serializers.ListField(child=serializers.DictField())
    subtotal = serializers.CharField()
    tier_discount_percent = serializers.CharField()
    manual_discount_percent = serializers.CharField()
    discount_percent = serializers.CharField()
    discount_amount = serializers.CharField()
    delivery_amount = serializers.CharField()
    total = serializers.CharField()
    warnings = serializers.ListField(child=serializers.CharField())
