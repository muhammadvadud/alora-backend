from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.catalog'
    verbose_name = _("Katalog (Catalog)")

    def ready(self):
        from . import signals  # noqa: F401

