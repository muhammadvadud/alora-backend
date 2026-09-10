"""Jamoa boshqaruvi (manager paneli) API yo'llari."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.accounts.views import EmployeeViewSet

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")

urlpatterns = router.urls
