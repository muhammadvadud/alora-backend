"""System prompt boshqaruvi ilovasi konfiguratsiyasi."""

from django.apps import AppConfig


class PromptsConfig(AppConfig):
    """`apps.prompts` ilovasi sozlamalari."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.prompts"
    verbose_name = "System prompt boshqaruvi"

    def ready(self) -> None:
        from . import signals  # noqa: F401
