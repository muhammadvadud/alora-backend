from __future__ import annotations

from django.apps import AppConfig
from django.core.checks import Warning as CheckWarning
from django.core.checks import register
from django.utils.translation import gettext_lazy as _


@register()
def check_single_tenant_assumption(app_configs, **kwargs):
    """Global pricing qarori bitta tenant bilan cheklanganini tekshiradi."""

    from apps.accounts.models import Tenant

    try:
        if Tenant.objects.count() > 1:
            return [
                CheckWarning(
                    "pricing global sozlamalari bir nechta tenant bilan mos emas",
                    hint="docs/ADR-001-pricing-global.md ga qarang, pricing modellarini tenantlashtiring",
                    id="pricing.W001",
                )
            ]
    except Exception:  # noqa: S110, BLE001
        pass
    return []


class PricingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pricing"
    verbose_name = _("Narx va hisob")

    def ready(self) -> None:
        from . import signals  # noqa: F401
