from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.knowledge.views import KnowledgeRuleViewSet


router = DefaultRouter()
router.register("rules", KnowledgeRuleViewSet, basename="knowledge-rule")

urlpatterns = [
    path("", include(router.urls)),
]
