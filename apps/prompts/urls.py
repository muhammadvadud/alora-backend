"""System prompt boshqaruvi API yo'llari (Bosqich 11).

rules.md 4.4: yo'llar `DefaultRouter` orqali ro'yxatdan o'tadi, `basename`
har doim aniq beriladi. `rollback` — o'sha ViewSet ichidagi `@action`.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.prompts.views import PromptVersionViewSet

app_name = "prompts"

router = DefaultRouter()
router.register("prompt", PromptVersionViewSet, basename="prompt")

urlpatterns = router.urls
