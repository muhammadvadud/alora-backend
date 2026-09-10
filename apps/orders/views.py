"""Buyurtma ViewSet'lari (Bosqich 8).

Qatlam: view -> service -> selector/model. View ichida biznes-mantiq yo'q —
barcha amallar `apps.orders.services` ga delegatsiya qilinadi.
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpRequest, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.common.choices import UserRole
from apps.common.pagination import StandardCursorPagination
from apps.common.permissions import IsOwnerOrManager
from apps.orders import selectors
from apps.orders.filters import OrderFilter
from apps.orders.models import Order
from apps.orders.pdf import PdfUnavailableError, generate_order_pdf
from apps.orders.serializers import (
    OrderReadSerializer,
    OrderStatusActionSerializer,
    OrderWriteSerializer,
)
from apps.orders.services import (
    change_order_status,
    confirm_order,
    create_order_from_draft,
    get_status_graph,
    update_order_from_draft,
)


def _django_validation_detail(exc: DjangoValidationError) -> dict[str, str]:
    """Django ValidationError'ni DRF yagona formatiga o'giradi."""

    if getattr(exc, "message_dict", None):
        return exc.message_dict  # type: ignore[no-any-return]
    return {"detail": str(exc)}


@extend_schema_view(
    list=extend_schema(
        responses={200: OrderReadSerializer},
        summary="Buyurtmalar ro'yxati",
    ),
    create=extend_schema(
        request=OrderWriteSerializer,
        responses={201: OrderReadSerializer},
        summary="Buyurtma yaratish",
    ),
    retrieve=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        responses={200: OrderReadSerializer},
        summary="Buyurtma tafsilotlari",
    ),
    partial_update=extend_schema(
        request=OrderWriteSerializer,
        responses={200: OrderReadSerializer},
        summary="Buyurtmani qisman yangilash",
    ),
    confirm=extend_schema(
        summary="Buyurtmani tasdiqlash",
        responses={200: OrderReadSerializer},
    ),
    status=extend_schema(
        request=OrderStatusActionSerializer,
        responses={200: OrderReadSerializer},
        summary="Buyurtma statusini o'zgartirish",
    ),
    statuses=extend_schema(
        summary="Status ro'yxati va ruxsat etilgan o'tishlar",
        responses={200: dict},
    ),
    pdf=extend_schema(
        summary="Kommercheskiy taklif PDF",
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
    ),
)
class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Buyurtmalar CRUD va qo'shimcha amallar.

    - `GET /orders/` (8.9) — filtr: status, sana, xodim, `?search=`
    - `POST /orders/` (8.10) — AI draft'idan yaratish
    - `GET/PATCH /orders/{id}/` (8.11)
    - `POST /orders/{id}/confirm/` (8.12)
    - `POST /orders/{id}/status/` (8.13)
    - `GET /orders/statuses/` (8.14)
    - `GET /orders/{id}/pdf/` (8.15)
    """

    serializer_class = OrderWriteSerializer
    permission_classes: ClassVar[list[type[BasePermission]]] = [IsOwnerOrManager]
    pagination_class = StandardCursorPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = OrderFilter

    def get_serializer_class(self) -> type[OrderReadSerializer | OrderWriteSerializer]:
        if self.action in ("list", "retrieve"):
            return OrderReadSerializer
        return OrderWriteSerializer

    def get_queryset(self) -> Any:
        """ "Tenant va egalik bo'yicha chegaralangan buyurtmalar.

        Employee faqat o'z buyurtmasini, manager/admin tenant ichidagi
        hammasini ko'radi (8.17).
        """

        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        queryset = selectors.get_orders().filter(tenant_id=self.request.user.tenant_id)
        if getattr(self.request.user, "role", None) == UserRole.EMPLOYEE:
            queryset = queryset.filter(user_id=self.request.user.pk)
        return queryset

    def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        """AI draft'idan buyurtma yaratadi (8.10)."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, _ = create_order_from_draft(
            payload=serializer.validated_data,
            user=request.user,
            conversation_id=serializer.validated_data.get("conversation_id"),
        )
        return Response(
            OrderReadSerializer(order, context=self.get_serializer_context()).data,
            status=http_status.HTTP_201_CREATED,
        )

    def partial_update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        """Buyurtma ma'lumotlarini qisman yangilaydi (8.11)."""

        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        order, _ = update_order_from_draft(
            order=order,
            payload=serializer.validated_data,
            user_role=getattr(request.user, "role", None),
        )
        return Response(OrderReadSerializer(order, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request: HttpRequest, pk: str | None = None) -> Response:
        """Buyurtmani tasdiqlaydi: draft -> confirmed (8.12)."""

        order = self.get_object()
        try:
            confirm_order(order=order, user=request.user)
        except DjangoValidationError as exc:
            raise ValidationError(_django_validation_detail(exc)) from exc
        order.refresh_from_db()
        return Response(OrderReadSerializer(order, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="status")
    def status(self, request: HttpRequest, pk: str | None = None) -> Response:
        """Statusni izoh va sana bilan o'zgartiradi (8.13)."""

        order = self.get_object()
        serializer = OrderStatusActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        try:
            change_order_status(
                order=order,
                target=payload["status"],
                user=request.user,
                note=payload.get("note", ""),
                action_date=payload.get("action_date"),
            )
        except DjangoValidationError as exc:
            raise ValidationError(_django_validation_detail(exc)) from exc
        order.refresh_from_db()
        return Response(OrderReadSerializer(order, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"], url_path="statuses")
    def statuses(self, request: HttpRequest) -> Response:
        """Status ro'yxati va ruxsat etilgan o'tishlar (8.14)."""

        return Response(get_status_graph())

    @action(detail=True, methods=["get"])
    def pdf(self, request: HttpRequest, pk: str | None = None) -> Response:
        """Kommercheskiy taklif PDF fayli (8.15)."""

        order = self.get_object()
        try:
            pdf_bytes = generate_order_pdf(order=order)
        except PdfUnavailableError as exc:
            return Response(
                {"detail": str(exc), "code": "pdf_unavailable", "errors": {}},
                status=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="order-{order.number}.pdf"'
        return response
