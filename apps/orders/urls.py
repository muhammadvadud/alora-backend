"""Buyurtmalar API yo'llari (Bosqich 8).

rules.md 4.4: yo'llar `DefaultRouter` orqali ro'yxatdan o'tadi, `basename`
har doim aniq beriladi. Qo'shimcha amallar (`confirm`, `status`, `pdf`,
`statuses`) `OrderViewSet` ichida `@action` bilan yoziladi.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.orders.views import OrderViewSet

app_name = "orders"

router = DefaultRouter()
router.register("", OrderViewSet, basename="order")

urlpatterns = router.urls
