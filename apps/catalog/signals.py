from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.catalog.models import Product, ProductVariant
from apps.chat.grpc_server.catalog_service import publish_catalog_delta


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    action = "create" if created else "update"
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="product",
        entity_id=str(instance.id),
        action=action,
    )


@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="product",
        entity_id=str(instance.id),
        action="delete",
    )


@receiver(post_save, sender=ProductVariant)
def product_variant_post_save(sender, instance, created, **kwargs):
    action = "create" if created else "update"
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="variant",
        entity_id=str(instance.id),
        action=action,
    )


@receiver(post_delete, sender=ProductVariant)
def product_variant_post_delete(sender, instance, **kwargs):
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="variant",
        entity_id=str(instance.id),
        action="delete",
    )
