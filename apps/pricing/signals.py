"""Narx qoidalari o'zgarishini Go agentga delta sifatida e'lon qilish.

Pricing modellari global (tenant'siz) — `tenant_id=""`. `DiscountPolicy` va
`OrderDefaults` singleton: entity_id yuboriladi, Go esa butun obyektni almashtiradi.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.chat.grpc_server import catalog_payload as payloads
from apps.chat.grpc_server.catalog_service import publish_catalog_delta
from apps.pricing.models import CalcRule, DiscountPolicy, DiscountTier, OrderDefaults, ServicePrice

_PAYLOADS = {
    CalcRule: ("calc_rule", payloads.calc_rule_payload),
    ServicePrice: ("service_price", payloads.service_price_payload),
    DiscountTier: ("discount_tier", payloads.discount_tier_payload),
    DiscountPolicy: ("discount_policy", payloads.discount_policy_payload),
    OrderDefaults: ("order_defaults", payloads.order_defaults_payload),
}


def _publish(instance, action: str) -> None:
    entity, build = _PAYLOADS[type(instance)]
    publish_catalog_delta(
        tenant_id="",
        entity=entity,
        entity_id=str(instance.id),
        action=action,
        payload=build(instance) if action != "delete" else None,
    )


@receiver(post_save, sender=CalcRule)
@receiver(post_save, sender=ServicePrice)
@receiver(post_save, sender=DiscountTier)
@receiver(post_save, sender=DiscountPolicy)
@receiver(post_save, sender=OrderDefaults)
def pricing_post_save(sender, instance, created, **kwargs):
    _publish(instance, "create" if created else "update")


@receiver(post_delete, sender=CalcRule)
@receiver(post_delete, sender=ServicePrice)
@receiver(post_delete, sender=DiscountTier)
@receiver(post_delete, sender=DiscountPolicy)
@receiver(post_delete, sender=OrderDefaults)
def pricing_post_delete(sender, instance, **kwargs):
    _publish(instance, "delete")
