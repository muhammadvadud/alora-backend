from __future__ import annotations

from typing import Any

from django.db import transaction
from django.http import HttpRequest
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, throttle_scope
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsManager
from apps.pricing.models import (
    CalcRule,
    DiscountPolicy,
    DiscountTier,
    ModelPricing,
    OrderDefaults,
    ServicePrice,
)
from apps.pricing.serializers import (
    CalcRuleSerializer,
    CalcRuleWriteSerializer,
    DiscountPolicySerializer,
    DiscountTierSerializer,
    ModelPricingSerializer,
    OrderDefaultsSerializer,
    PreviewRequestSerializer,
    PreviewResultSerializer,
    ServicePriceSerializer,
    ServicePriceWriteSerializer,
)
from apps.pricing.services import calculate_preview
from apps.pricing.services.crud import upsert_calc_rules, upsert_service_prices


class ManagerOnlyViewSetMixin:
    """Manager va admin uchun umumiy permission aralashmasi."""

    permission_classes = [IsManager]


class CalcRuleViewSet(ManagerOnlyViewSetMixin, viewsets.GenericViewSet):
    """Hisob qoidalari (CalcRule) uchun viewset."""

    queryset = CalcRule.objects.all()
    serializer_class = CalcRuleSerializer
    lookup_field = "key"

    def get_serializer_class(self) -> type[CalcRuleSerializer]:
        if self.action == "partial_update":
            return CalcRuleWriteSerializer
        return CalcRuleSerializer

    @extend_schema(
        responses={200: CalcRuleSerializer(many=True)}, summary="Hisob qoidalari ro'yxati"
    )
    def list(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(self.get_queryset().order_by("key"), many=True)
        return Response(serializer.data)

    @extend_schema(
        request=CalcRuleWriteSerializer(many=True),
        responses={200: CalcRuleSerializer(many=True)},
        summary="Hisob qoidalariini yangilash",
    )
    def partial_update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        serializer = CalcRuleWriteSerializer(data=self._normalize_payload(request.data), many=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            rules = upsert_calc_rules(serializer.validated_data)
        return Response(CalcRuleSerializer(rules, many=True).data)

    @extend_schema(responses={200: CalcRuleSerializer}, summary="Bitta hisob qoidasi")
    def retrieve(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        try:
            rule = self.get_queryset().get(key=self.kwargs.get(self.lookup_field))
        except CalcRule.DoesNotExist as exc:
            raise NotFound("Hisob qoidasi topilmadi") from exc
        return Response(self.get_serializer(rule).data)

    @staticmethod
    def _normalize_payload(payload: Any) -> Any:
        """Yakka yoki ro'yxat shaklidagi payload'ni standartlaydi."""

        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and "items" in payload:
            return payload["items"]
        return [payload]


class ServicePriceViewSet(ManagerOnlyViewSetMixin, viewsets.GenericViewSet):
    """Xizmat narxlari uchun viewset."""

    queryset = ServicePrice.objects.all()
    serializer_class = ServicePriceSerializer
    lookup_field = "key"

    def get_serializer_class(self) -> type[ServicePriceSerializer]:
        if self.action == "partial_update":
            return ServicePriceWriteSerializer
        return ServicePriceSerializer

    @extend_schema(
        responses={200: ServicePriceSerializer(many=True)}, summary="Xizmat narxlari ro'yxati"
    )
    def list(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(self.get_queryset().order_by("key"), many=True)
        return Response(serializer.data)

    @extend_schema(
        request=ServicePriceWriteSerializer(many=True),
        responses={200: ServicePriceSerializer(many=True)},
        summary="Xizmat narxlarini yangilash",
    )
    def partial_update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        serializer = ServicePriceWriteSerializer(
            data=self._normalize_payload(request.data), many=True
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            service_prices = upsert_service_prices(serializer.validated_data)
        return Response(ServicePriceSerializer(service_prices, many=True).data)

    @extend_schema(responses={200: ServicePriceSerializer}, summary="Bitta xizmat narxi")
    def retrieve(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        try:
            service_price = self.get_queryset().get(key=self.kwargs.get(self.lookup_field))
        except ServicePrice.DoesNotExist as exc:
            raise NotFound("Xizmat narxi topilmadi") from exc
        return Response(self.get_serializer(service_price).data)

    @staticmethod
    def _normalize_payload(payload: Any) -> Any:
        """Yakka yoki ro'yxat shaklidagi payload'ni standartlaydi."""

        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and "items" in payload:
            return payload["items"]
        return [payload]


class DiscountTierViewSet(ManagerOnlyViewSetMixin, viewsets.ModelViewSet):
    """Chegirma bosqichlari uchun viewset."""

    queryset = DiscountTier.objects.all()
    serializer_class = DiscountTierSerializer


class DiscountPolicyViewSet(ManagerOnlyViewSetMixin, viewsets.GenericViewSet):
    """Chegirma siyosati uchun singleton viewset."""

    queryset = DiscountPolicy.objects.all()
    serializer_class = DiscountPolicySerializer

    def get_object(self) -> DiscountPolicy:
        instance = self.get_queryset().order_by("created_at").first()
        if instance is None:
            raise NotFound("Chegirma siyosati topilmadi")
        return instance

    @extend_schema(responses={200: DiscountPolicySerializer}, summary="Chegirma siyosati")
    def retrieve(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(
        request=DiscountPolicySerializer,
        responses={200: DiscountPolicySerializer},
        summary="Chegirma siyosatini yangilash",
    )
    def partial_update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = DiscountPolicySerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OrderDefaultsViewSet(ManagerOnlyViewSetMixin, viewsets.GenericViewSet):
    """Buyurtma standartlari uchun singleton viewset."""

    queryset = OrderDefaults.objects.all()
    serializer_class = OrderDefaultsSerializer

    def get_object(self) -> OrderDefaults:
        instance = self.get_queryset().order_by("created_at").first()
        if instance is None:
            raise NotFound("Buyurtma standartlari topilmadi")
        return instance

    @extend_schema(responses={200: OrderDefaultsSerializer}, summary="Buyurtma standartlari")
    def retrieve(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(
        request=OrderDefaultsSerializer,
        responses={200: OrderDefaultsSerializer},
        summary="Buyurtma standartlarini yangilash",
    )
    def partial_update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = OrderDefaultsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ModelPricingViewSet(viewsets.ModelViewSet):
    """Model narxlari uchun admin-only CRUD."""

    permission_classes = [IsManager]
    queryset = ModelPricing.objects.all()
    serializer_class = ModelPricingSerializer


@extend_schema(
    request=PreviewRequestSerializer,
    responses=PreviewResultSerializer,
    summary="Kalkulyatsiya preview",
    description="Berilgan o'lchovlar va parametrlar asosida narxni oldindan hisoblaydi.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_scope("calc")
def calc_preview_view(request: HttpRequest) -> Response:
    """Kalkulyatsiya preview'i."""

    serializer = PreviewRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = calculate_preview(
        serializer.validated_data, user_role=getattr(request.user, "role", None)
    )
    return Response(PreviewResultSerializer(result).data, status=status.HTTP_200_OK)
