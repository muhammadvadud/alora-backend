from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrdersConfig(AppConfig):
    """orders ilovasi — hozircha skelet, to'ldirish keyingi bosqichda."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"
    verbose_name = _("orders")
