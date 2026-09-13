"""Joriy system prompt o'zgarganda Go agentga `prompt` delta'sini yuborish.

Faqat `is_current=True` bo'lgan versiya yuboriladi — Go bitta joriy promptni
saqlaydi; eski versiyalar audit uchun Django'da qoladi.

Redis ishlamasa prompt endpoint ishdan chiqmaydi (11.5-band): xato loglanadi,
Go keyingi Snapshot'da joriy promptni baribir oladi.
"""

import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.chat.grpc_server import catalog_payload as payloads
from apps.chat.grpc_server.catalog_service import publish_catalog_delta
from apps.prompts.models import PromptVersion

logger = structlog.get_logger(__name__)


@receiver(post_save, sender=PromptVersion)
def prompt_version_post_save(sender, instance, created, **kwargs):
    if not instance.is_current:
        return
    try:
        publish_catalog_delta(
            tenant_id="",
            entity="prompt",
            entity_id=str(instance.id),
            action="update",
            payload=payloads.prompt_payload(instance),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("prompt_delta_publish_failed", version=instance.version, error=str(exc))
