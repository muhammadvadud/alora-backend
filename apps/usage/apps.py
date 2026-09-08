from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsageConfig(AppConfig):
    """usage ilovasi — hozircha skelet, to'ldirish keyingi bosqichda."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.usage"
    verbose_name = _("usage")
