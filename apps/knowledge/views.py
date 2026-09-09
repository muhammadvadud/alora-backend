from __future__ import annotations

from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from apps.common.permissions import IsManager
from apps.knowledge.models import KnowledgeRule
from apps.knowledge.serializers import KnowledgeRuleReadSerializer, KnowledgeRuleWriteSerializer


class KnowledgeRuleViewSet(viewsets.ModelViewSet):
    """Bilim qoidalari uchun manager-only viewset."""

    permission_classes = [IsManager]
    queryset = KnowledgeRule.objects.all().order_by("-priority", "-created_at")
    filter_backends = [SearchFilter]
    search_fields = ["kind", "recommendation"]

    def get_serializer_class(self) -> type[KnowledgeRuleReadSerializer]:
        if self.action in {"create", "update", "partial_update"}:
            return KnowledgeRuleWriteSerializer
        return KnowledgeRuleReadSerializer

    def perform_create(self, serializer: KnowledgeRuleWriteSerializer) -> None:
        serializer.save()

    def perform_update(self, serializer: KnowledgeRuleWriteSerializer) -> None:
        serializer.save()
