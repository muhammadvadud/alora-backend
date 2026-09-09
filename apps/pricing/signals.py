from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.chat.grpc_server.catalog_service import publish_catalog_delta
from apps.pricing.models import CalcRule


@receiver(post_save, sender=CalcRule)
def calc_rule_post_save(sender, instance, created, **kwargs):
    action = "create" if created else "update"
    publish_catalog_delta(
        tenant_id="",
        entity="calc_rule",
        entity_id=str(instance.id),
        action=action,
    )


@receiver(post_delete, sender=CalcRule)
def calc_rule_post_delete(sender, instance, **kwargs):
    publish_catalog_delta(
        tenant_id="",
        entity="calc_rule",
        entity_id=str(instance.id),
        action="delete",
    )
