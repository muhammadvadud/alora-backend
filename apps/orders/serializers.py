"""Buyurtma serializerlari.

O'qish (`OrderReadSerializer`) — nested o'lchov/bo'lak/aksessuar/xizmat bilan;
yozish (`OrderWriteSerializer`) — AI draft formatidagi yassi yozma serializer.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.catalog.models import ProductVariant
from apps.common.choices import CurtainPartRole, OrderStatus, PaymentStatus
from apps.orders.models import (
    Order,
    OrderAccessory,
    OrderCurtainPart,
    OrderItem,
    OrderMeasurement,
)

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    """Buyurtma egalari uchun qisqa foydalanuvchi ma'lumoti."""

    class Meta:
        model = User
        fields = ("id", "full_name", "phone")


class VariantBriefSerializer(serializers.ModelSerializer):
    """Snapshot variantiga tegishli qisqa katalog ma'lumoti."""

    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductVariant
        fields = ("id", "sku", "color_name", "product_name", "price_unit")


class OrderPartReadSerializer(serializers.ModelSerializer):
    """Parda bo'lagi — o'qish uchun."""

    variant = VariantBriefSerializer(read_only=True)

    class Meta:
        model = OrderCurtainPart
        fields = (
            "id",
            "variant",
            "role",
            "width_m",
            "height_m",
            "coefficient",
            "area_sqm",
            "price_per_sqm",
            "total",
            "sort_order",
        )


class OrderAccessoryReadSerializer(serializers.ModelSerializer):
    """Aksessuar — o'qish uchun."""

    variant = VariantBriefSerializer(read_only=True)

    class Meta:
        model = OrderAccessory
        fields = (
            "id",
            "variant",
            "qty",
            "unit",
            "unit_price",
            "total",
            "sort_order",
        )


class OrderMeasurementReadSerializer(serializers.ModelSerializer):
    """O'lchov va uning bo'laklari/aksessuarlari — o'qish uchun."""

    parts = OrderPartReadSerializer(many=True, read_only=True)
    accessories = OrderAccessoryReadSerializer(many=True, read_only=True)

    class Meta:
        model = OrderMeasurement
        fields = (
            "id",
            "room_name",
            "cornice_length_m",
            "height_m",
            "layers",
            "coefficient",
            "note",
            "parts",
            "accessories",
        )


class OrderItemReadSerializer(serializers.ModelSerializer):
    """Xizmat qatori — o'qish uchun."""

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "service_key",
            "name_snapshot",
            "qty",
            "unit",
            "unit_price",
            "total",
            "sort_order",
        )


class OrderReadSerializer(serializers.ModelSerializer):
    """Buyurtma — to'liq o'qish serializer'i."""

    user = UserBriefSerializer(read_only=True)
    confirmed_by = UserBriefSerializer(read_only=True)
    measurements = OrderMeasurementReadSerializer(many=True, read_only=True)
    items = OrderItemReadSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )
    discount_source_display = serializers.CharField(
        source="get_discount_source_display", read_only=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "conversation",
            "customer_name",
            "customer_phone",
            "address",
            "status",
            "status_display",
            "subtotal",
            "discount_percent",
            "discount_amount",
            "discount_source",
            "discount_source_display",
            "delivery_amount",
            "total",
            "prepayment_percent",
            "prepayment",
            "balance",
            "payment_status",
            "payment_status_display",
            "deadline_date",
            "note",
            "confirmed_by",
            "confirmed_at",
            "user",
            "measurements",
            "items",
            "created_at",
            "updated_at",
        )


class OrderPartWriteSerializer(serializers.Serializer):
    """Parda bo'lagi — yozish (AI draft formati)."""

    variant_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=CurtainPartRole.choices)
    width_m = serializers.DecimalField(max_digits=8, decimal_places=3)
    height_m = serializers.DecimalField(max_digits=8, decimal_places=3)
    coefficient = serializers.DecimalField(
        max_digits=8, decimal_places=3, required=False, allow_null=True
    )
    coef = serializers.DecimalField(max_digits=8, decimal_places=3, required=False, allow_null=True)


class OrderAccessoryWriteSerializer(serializers.Serializer):
    """Aksessuar — yozish (AI draft formati)."""

    variant_id = serializers.UUIDField()
    qty = serializers.DecimalField(max_digits=8, decimal_places=3)


class OrderMeasurementWriteSerializer(serializers.Serializer):
    """O'lchov — yozish (AI draft formati)."""

    room_name = serializers.CharField(max_length=255)
    cornice_length_m = serializers.DecimalField(max_digits=8, decimal_places=3)
    height_m = serializers.DecimalField(max_digits=8, decimal_places=3)
    coefficient = serializers.DecimalField(
        max_digits=8, decimal_places=3, required=False, allow_null=True
    )
    layers = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    parts = OrderPartWriteSerializer(many=True, required=False, default=list)
    accessories = OrderAccessoryWriteSerializer(many=True, required=False, default=list)


class OrderWriteSerializer(serializers.Serializer):
    """Buyurtma yaratish/yangilash uchun yassi serializer.

    `partial=True` bo'lganda berilmagan maydonlar o'tkazib yuboriladi
    (DRF'da partial rejimda default qiymat qo'llanilmaydi).
    """

    customer_name = serializers.CharField(max_length=255)
    customer_phone = serializers.CharField(max_length=20)
    address = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")
    deadline_date = serializers.DateField(required=False, allow_null=True, default=None)
    prepayment_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True, default=None
    )
    payment_status = serializers.ChoiceField(choices=PaymentStatus.choices, required=False)
    discount_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default="0.00"
    )
    delivery = serializers.BooleanField(required=False, default=False)
    services = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True, default=list
    )
    measurements = OrderMeasurementWriteSerializer(many=True, required=False, default=list)
    conversation_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class OrderStatusActionSerializer(serializers.Serializer):
    """Status o'zgartirish amalining kirish ma'lumoti (8.13)."""

    status = serializers.ChoiceField(choices=OrderStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    action_date = serializers.DateField(required=False, allow_null=True, default=None)
