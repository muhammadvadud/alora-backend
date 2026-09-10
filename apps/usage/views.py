"""Usage statistika va analitika ViewSet'lari.

Faqat manager va admin uchun ochiq; `IsManager` permission'i
employee rolini avtomatik rad etadi.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsManager
from apps.usage import selectors
from apps.usage.serializers import (
    ByUserItemSerializer,
    ConversationStatSerializer,
    ConversionSerializer,
    PeriodQuerySerializer,
    SummaryQuerySerializer,
    SummarySerializer,
)


class UsageViewSet(viewsets.GenericViewSet):
    """Foydalanish statistikasi uchun ViewSet."""

    permission_classes = (IsManager,)

    @extend_schema(
        summary="Kunlik / haftalik / oylik xulosa",
        responses={200: SummarySerializer},
    )
    @action(detail=False, methods=["get"])
    def summary(self, request: HttpRequest) -> Response:
        """Kunlik / haftalik / oylik xulosa."""

        query = SummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        user = None
        if params.get("user"):
            User = get_user_model()
            user = User.objects.filter(pk=params["user"]).first()

        data = selectors.get_summary(request.user.tenant, period=params["period"], user=user)
        return Response(SummarySerializer(data).data)

    @extend_schema(
        summary="Xodimlar bo'yicha reyting",
        responses={200: ByUserItemSerializer},
    )
    @action(detail=False, methods=["get"], url_path="by-user")
    def by_user(self, request: HttpRequest) -> Response:
        """Xodimlar bo'yicha reyting."""

        query = PeriodQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = selectors.get_by_user(request.user.tenant, period=query.validated_data["period"])
        return Response(ByUserItemSerializer(data, many=True).data)

    @extend_schema(
        summary="Eng qimmat suhbatlar",
        responses={200: ConversationStatSerializer},
    )
    @action(detail=False, methods=["get"])
    def conversations(self, request: HttpRequest) -> Response:
        """Eng qimmat suhbatlar."""

        data = selectors.get_most_expensive_conversations(request.user.tenant)
        return Response(ConversationStatSerializer(data, many=True).data)


class AnalyticsViewSet(viewsets.GenericViewSet):
    """Analitika uchun ViewSet."""

    permission_classes = (IsManager,)

    @extend_schema(
        summary="Suhbatdan buyurtmaga konversiya",
        responses={200: ConversionSerializer},
    )
    @action(detail=False, methods=["get"])
    def conversion(self, request: HttpRequest) -> Response:
        """Suhbatdan buyurtmaga konversiya."""

        data = selectors.get_conversion_stats(request.user.tenant)
        return Response(ConversionSerializer(data).data)
