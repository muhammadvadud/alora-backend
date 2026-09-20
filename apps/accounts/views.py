from django.apps import apps
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import User as UserModel
from apps.accounts.serializers import (
    AuthMeSerializer,
    CustomTokenObtainPairSerializer,
    EmployeeLimitSerializer,
    EmployeeListSerializer,
    EmployeePasswordSerializer,
    EmployeeWriteSerializer,
)
from apps.common.choices import UserRole
from apps.common.permissions import IsManager
from apps.usage import selectors as usage_selectors
from apps.usage.services import set_user_usage_limit


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    # 5/daqiqa rate limit throttling settings da bo'lishi kerak yoki shu yerda beriladi.
    throttle_scope = "login"


@extend_schema(summary="Joriy foydalanuvchi ma'lumotlari", responses={200: AuthMeSerializer})
class AuthMeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = AuthMeSerializer(request.user)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        responses={200: EmployeeListSerializer},
        summary="Jamoa xodimlari ro'yxati",
    ),
    create=extend_schema(
        request=EmployeeWriteSerializer,
        responses={201: EmployeeListSerializer},
        summary="Yangi xodim qo'shish",
    ),
    retrieve=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        summary="Xodim tafsilotlari",
        responses={200: EmployeeListSerializer},
    ),
    update=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        request=EmployeeWriteSerializer,
        responses={200: EmployeeListSerializer},
        summary="Xodim ma'lumotlarini to'liq yangilash",
    ),
    partial_update=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        request=EmployeeWriteSerializer,
        responses={200: EmployeeListSerializer},
        summary="Xodim ma'lumotlarini yangilash",
    ),
    destroy=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        summary="Xodimni o'chirish",
        responses={204: None},
    ),
    limit=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        request=EmployeeLimitSerializer,
        summary="Xodim foydalanish limitini o'rnatish",
        responses={200: dict},
    ),
    password=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        request=EmployeePasswordSerializer,
        summary="Xodim parolini almashtirish",
        responses={200: EmployeeListSerializer},
    ),
    conversations=extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        summary="Xodimning suhbatlar ro'yxati",
        responses={200: dict},
    ),
)
class EmployeeViewSet(viewsets.ModelViewSet):
    """Jamoa xodimlarini boshqarish uchun ViewSet.

    Faqat manager va admin uchun ochiq. O'z tenanti xodimlarini ko'radi.
    """

    permission_classes = (IsManager,)
    queryset = None  # type: ignore[assignment]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return UserModel.objects.none()
        if self.queryset is None:
            User = self.request.user.__class__
            queryset = User.objects.exclude(role=UserRole.ADMIN).filter(
                role__in=[UserRole.EMPLOYEE, UserRole.MANAGER]
            )
            if self.request.user.tenant_id:
                queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
            self.queryset = queryset.order_by("-created_at")
        return self.queryset

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return EmployeeWriteSerializer
        return EmployeeListSerializer

    def list(self, request, *args, **kwargs):
        employees = self.get_queryset()
        activity = usage_selectors.get_users_today_activity(
            request.user.tenant, [emp.pk for emp in employees]
        )
        data = EmployeeListSerializer(employees, many=True).data
        for item in data:
            day = activity.get(str(item["id"]), {})
            item["today_tokens"] = day.get("tokens", 0)
            item["today_messages"] = day.get("messages", 0)
            item["today_conversations"] = day.get("conversations", 0)
        return Response(data)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

    def perform_update(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

    @action(detail=True, methods=["post"])
    def limit(self, request, pk=None):
        """Xodim uchun shaxsiy foydalanish limitini o'rnatadi.

        `{"is_unlimited": true}` — cheksiz rejim.
        """
        employee = self.get_object()
        serializer = EmployeeLimitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        limit = set_user_usage_limit(employee, serializer.validated_data)
        return Response(
            {
                "id": str(limit.id),
                "user_id": str(limit.user_id),
                "period": limit.period,
                "is_unlimited": limit.is_unlimited,
                "max_tokens": limit.max_tokens,
                "max_cost_uzs": str(limit.max_cost_uzs) if limit.max_cost_uzs is not None else None,
                "max_messages": limit.max_messages,
                "on_exceed": limit.on_exceed,
                "is_active": limit.is_active,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def password(self, request, pk=None):
        employee = self.get_object()
        if employee.role != UserRole.EMPLOYEE:
            raise serializers.ValidationError({"detail": "Faqat xodim parolini almashtirish mumkin."})

        serializer = EmployeePasswordSerializer(data=request.data, context={"user": employee})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(EmployeeListSerializer(employee).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def conversations(self, request, pk=None):
        """Xodimning suhbatlar ro'yxati.

        `chat.Conversation` modeli hali yaratilmagan bo'lsa bo'sh ro'yxat qaytariladi.
        """
        employee = self.get_object()
        Conversation = apps.get_model("chat", "Conversation")
        if Conversation is None:
            return Response([])
        conversations = Conversation.objects.filter(
            user_id=employee.pk, tenant_id=request.user.tenant_id
        ).order_by("-last_message_at")
        rows = []
        for conv in conversations:
            rows.append(
                {
                    "id": str(conv.id),
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "status": conv.status,
                    "stage": conv.stage,
                    "mode": conv.mode,
                    "last_message_at": conv.last_message_at,
                    "started_at": conv.started_at,
                }
            )
        return Response(rows)
