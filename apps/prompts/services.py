"""System prompt boshqaruvi biznes-mantiqlari (Bosqich 11).

rules.md 0.4: biznes-mantiq faqat services qatlamida yashaydi.
Bir vaqtda bitta joriy versiya — model darajasidagi UniqueConstraint bilan
kafolatlanadi (11.1-band).
"""

from __future__ import annotations

import json
from typing import Any

import redis
import structlog
from django.conf import settings
from django.db import transaction
from django.db.models import Max

from apps.prompts.models import PromptVersion

logger = structlog.get_logger(__name__)

# Redis pub/sub kanali — system prompt o'zgarganda Go agentga xabar beriladi (11.5-band)
PROMPT_UPDATED_CHANNEL = "alora:prompt:updated"


def _next_version_number() -> int:
    """Mavjud eng katta versiya raqamidan bittaga kattasini qaytaradi."""

    max_version = PromptVersion.objects.aggregate(max_version=Max("version"))["max_version"]
    return (max_version or 0) + 1


def _deactivate_current() -> None:
    """Barcha joriy versiyalarni `is_current=False` qiladi.

    Yozuvning o'zi (matn, muallif, versiya raqami) o'zgarishsiz qoladi —
    faqat joriylik belgisi yangilanadi.
    """

    PromptVersion.objects.filter(is_current=True).update(is_current=False)


def notify_prompt_updated(*, version: PromptVersion) -> None:
    """Prompt yangilangani haqida Redis pub/sub orqali Go agentga xabar beradi.

    Redis ishlamasa prompt endpoint ishdan chiqmaydi — xato loglanadi va
    javob normal qaytadi (11.5-band).
    """

    try:
        client = redis.from_url(settings.REDIS_URL)
        payload = json.dumps(
            {
                "tenant_id": "",
                "entity": "system_prompt",
                "entity_id": str(version.id),
                "action": "update",
                "version": version.version,
                "payload_json": "",
            },
            ensure_ascii=False,
        )
        client.publish(PROMPT_UPDATED_CHANNEL, payload)
        logger.info(
            "Prompt yangilanishi e'lon qilindi",
            entity="system_prompt",
            version=version.version,
        )
    except redis.RedisError:
        logger.exception(
            "Prompt yangilanishi Redis ga e'lon qilinmadi",
            entity="system_prompt",
            version=version.version,
        )


def create_prompt_version(*, content: str, author: Any) -> PromptVersion:
    """Yangi system prompt versiyasini yaratadi va joriy qilib qo'yadi.

    Versiya raqami avtomatik oshadi, muallif — request.user.
    """

    with transaction.atomic():
        _deactivate_current()
        version = PromptVersion.objects.create(
            version=_next_version_number(),
            content=content,
            author=author,
            is_current=True,
        )
    notify_prompt_updated(version=version)
    return version


def rollback_prompt_version(*, target: PromptVersion, author: Any) -> PromptVersion:
    """Belgilangan eski versiya matnini yangi versiya qilib qaytaradi.

    Audit tarixi buzilmaydi (11.4-band): `target` yozuvi o'zgartirilmaydi,
    uning matni bilan yangi joriy versiya yaratiladi.
    """

    with transaction.atomic():
        _deactivate_current()
        version = PromptVersion.objects.create(
            version=_next_version_number(),
            content=target.content,
            author=author,
            is_current=True,
        )
    notify_prompt_updated(version=version)
    return version
