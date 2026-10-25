"""SSE `done` dan keyin saqlash: bo'sh assistant matni yozilmaydi, usage saqlanadi."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.chat.models import Message
from apps.chat.tasks import save_message_and_usage
from apps.common.choices import MessageRole


@pytest.mark.django_db
def test_bosh_assistant_matni_saqlanmaydi_usage_saqlanadi(conversation_factory, tenant) -> None:
    conversation = conversation_factory()
    event = {"kind": "done", "content": "", "usage": {"prompt_tokens": 10, "completion_tokens": 5}}

    with (
        patch("apps.usage.tasks.save_usage_record") as usage_task,
        patch("apps.chat.tasks.generate_conversation_title"),
    ):
        save_message_and_usage(
            conversation_id=str(conversation.id),
            user_message_content="salom",
            ai_event_data=event,
            tenant_id=str(tenant.id),
        )

    roles = list(Message.objects.filter(conversation=conversation).values_list("role", flat=True))
    assert roles == [MessageRole.USER]
    assert usage_task.delay.called or usage_task.called


@pytest.mark.django_db
def test_toliq_assistant_matni_saqlanadi(conversation_factory, tenant) -> None:
    conversation = conversation_factory()
    event = {"kind": "done", "content": "Javob", "usage": {}}

    with (
        patch("apps.usage.tasks.save_usage_record"),
        patch("apps.chat.tasks.generate_conversation_title"),
    ):
        save_message_and_usage(
            conversation_id=str(conversation.id),
            user_message_content="salom",
            ai_event_data=event,
            tenant_id=str(tenant.id),
        )

    assert (
        Message.objects.filter(conversation=conversation, role=MessageRole.ASSISTANT).count() == 1
    )


@pytest.mark.django_db
def test_bir_xil_matn_keyinroq_yana_saqlanadi(conversation_factory) -> None:
    from datetime import timedelta

    from django.utils import timezone

    from apps.chat.tasks import save_message

    conversation = conversation_factory()
    first = save_message(session_id=conversation.session_id, role=MessageRole.USER, content="ha")
    # Retry oynasida — dublikat emas
    again = save_message(session_id=conversation.session_id, role=MessageRole.USER, content="ha")
    assert again == first
    # Oynadan tashqarida — yangi xabar
    Message.objects.filter(pk=first).update(created_at=timezone.now() - timedelta(minutes=5))
    later = save_message(session_id=conversation.session_id, role=MessageRole.USER, content="ha")
    assert later != first
    assert Message.objects.filter(conversation=conversation, role=MessageRole.USER).count() == 2
