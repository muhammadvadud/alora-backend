from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.chat.grpc_server import catalog_payload as payloads
from apps.chat.grpc_server.catalog_service import publish_catalog_delta
from apps.knowledge.models import KnowledgeRule


@receiver(post_save, sender=KnowledgeRule)
def knowledge_rule_post_save(sender, instance, created, **kwargs):
    publish_catalog_delta(
        tenant_id="",
        entity="knowledge_rule",
        entity_id=str(instance.id),
        action="create" if created else "update",
        payload=payloads.knowledge_rule_payload(instance),
    )


@receiver(post_delete, sender=KnowledgeRule)
def knowledge_rule_post_delete(sender, instance, **kwargs):
    publish_catalog_delta(
        tenant_id="",
        entity="knowledge_rule",
        entity_id=str(instance.id),
        action="delete",
    )
