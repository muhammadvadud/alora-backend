"""Usage va analitika API yo'llari."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.usage.views import AnalyticsViewSet, UsageViewSet

router = DefaultRouter()
router.register("usage", UsageViewSet, basename="usage")
router.register("analytics", AnalyticsViewSet, basename="analytics")

urlpatterns = router.urls