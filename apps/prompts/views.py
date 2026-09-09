"""System prompt boshqaruvi viewset (faqat admin, rules.md §5)."""

from __future__ import annotations

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsAdmin
from apps.prompts.models import PromptVersion
from apps.prompts.selectors import get_prompt_history
from apps.prompts.serializers import PromptReadSerializer, PromptWriteSerializer
from apps.prompts.services import create_prompt_version, rollback_prompt_version


class PromptVersionViewSet(viewsets.GenericViewSet):
    """System prompt versiyalari endpointi.

    - `GET /settings/prompt/` — joriy versiya + to'liq tarix (11.2-band).
    - `POST /settings/prompt/` — yangi versiya (11.3-band).
    - `POST /settings/prompt/{version}/rollback/` — eski versiyaga qaytish (11.4-band).
    """

    permission_classes = (IsAdmin,)
    lookup_field = "version"
    queryset = PromptVersion.objects.all()
    serializer_class = PromptReadSerializer

    @extend_schema(summary="Joriy versiya va tarix", responses={200: dict})
    def list(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        versions = list(get_prompt_history())
        current = next((v for v in versions if v.is_current), None)
        return Response(
            {
                "current": PromptReadSerializer(current).data if current else None,
                "history": PromptReadSerializer(versions, many=True).data,
            }
        )

    @extend_schema(
        request=PromptWriteSerializer,
        responses={201: PromptReadSerializer},
        summary="Yangi prompt versiyasi yaratish",
    )
    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = PromptWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = create_prompt_version(
            content=serializer.validated_data["content"],
            author=request.user,
        )
        return Response(PromptReadSerializer(version).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Eski versiyaga qaytish",
        responses={200: PromptReadSerializer},
    )
    @action(detail=True, methods=["post"])
    def rollback(self, request: Any, version: str | None = None) -> Response:
        target: PromptVersion = self.get_object()
        new_version = rollback_prompt_version(target=target, author=request.user)
        return Response(PromptReadSerializer(new_version).data, status=status.HTTP_200_OK)
