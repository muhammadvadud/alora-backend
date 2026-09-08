from __future__ import annotations

from django.apps import AppConfig
from django.urls import include, path
from django.utils.translation import gettext_lazy as _


def _append_urlpattern(target: list[object], route: str, include_name: str) -> None:
    """URL pattern allaqachon qo'shilmagan bo'lsa, ro'yxatga qo'shadi."""

    for pattern in target:
        if getattr(getattr(pattern, "pattern", None), "_route", None) == route:
            return
    target.append(path(route, include(include_name)))


class KnowledgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.knowledge"
    verbose_name = _("Bilimlar bazasi")

    def ready(self) -> None:
        from config import urls as project_urls

        urlpatterns = getattr(project_urls, "urlpatterns", None)
        if urlpatterns is None:
            return
        _append_urlpattern(urlpatterns, "api/v1/knowledge/", "apps.knowledge.urls")
