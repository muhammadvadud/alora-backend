"""Katalog o'zgarishlarini Go agentga delta sifatida e'lon qilish.

Payload — `catalog_payload` dagi bir xil dict (Snapshot bilan bir manba), shuning
uchun Go delta'ni Snapshot'siz qo'llay oladi. `FasonPart`/`FasonAccessory`
o'zgarganda butun `fason` qayta yuboriladi — Go bo'lakni alohida bilmaydi.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.catalog.models import Fason, FasonAccessory, FasonPart, Product, ProductVariant
from apps.catalog.services.import_service import IMPORT_IN_PROGRESS
from apps.chat.grpc_server import catalog_payload as payloads
from apps.chat.grpc_server.catalog_service import publish_catalog_delta


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    if IMPORT_IN_PROGRESS.get():
        return
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="product",
        entity_id=str(instance.id),
        action="create" if created else "update",
        payload=payloads.product_payload(instance),
    )


@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    if IMPORT_IN_PROGRESS.get():
        return
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="product",
        entity_id=str(instance.id),
        action="delete",
    )


@receiver(post_save, sender=ProductVariant)
def product_variant_post_save(sender, instance, created, **kwargs):
    if IMPORT_IN_PROGRESS.get():
        return
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="variant",
        entity_id=str(instance.id),
        action="create" if created else "update",
        payload=payloads.variant_payload(instance),
    )


@receiver(post_delete, sender=ProductVariant)
def product_variant_post_delete(sender, instance, **kwargs):
    if IMPORT_IN_PROGRESS.get():
        return
    publish_catalog_delta(
        tenant_id=str(instance.tenant_id),
        entity="variant",
        entity_id=str(instance.id),
        action="delete",
        payload={"product_id": str(instance.product_id)},
    )


def _publish_fason(fason: Fason, action: str) -> None:
    publish_catalog_delta(
        tenant_id=str(fason.tenant_id),
        entity="fason",
        entity_id=str(fason.id),
        action=action,
        payload=payloads.fason_payload(fason) if action != "delete" else None,
    )


@receiver(post_save, sender=Fason)
def fason_post_save(sender, instance, created, **kwargs):
    _publish_fason(instance, "create" if created else "update")


@receiver(post_delete, sender=Fason)
def fason_post_delete(sender, instance, **kwargs):
    _publish_fason(instance, "delete")


@receiver(post_save, sender=FasonPart)
@receiver(post_delete, sender=FasonPart)
@receiver(post_save, sender=FasonAccessory)
@receiver(post_delete, sender=FasonAccessory)
def fason_child_changed(sender, instance, **kwargs):
    # Ota fason CASCADE bilan o'chirilayotgan bo'lsa u allaqachon yo'q — delta fason'dan ketadi.
    fason = Fason.objects.filter(pk=instance.fason_id).first()
    if fason is not None:
        _publish_fason(fason, "update")
