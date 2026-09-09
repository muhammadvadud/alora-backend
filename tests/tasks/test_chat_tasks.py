"""Suhbat Celery tasklari testlari — 13.2, 13.3, 13.5 va 13.9."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from django.utils import timezone

from apps.chat.models import Conversation, ConversationStatus, Message
from apps.chat.tasks import (
    archive_old_conversations,
    generate_conversation_title,
    save_message,
    save_message_and_usage,
)
from apps.common.choices import MessageRole
from apps.usage.models import UsageRecord

pytestmark = pytest.mark.django_db


class TestSaveMessage:
    """13.2 — `save_message` taski."""

    def test_creates_message_with_all_fields(self, conversation):
        message = save_message(
            conversation_id=str(conversation.id),
            role=MessageRole.USER,
            content="Salom",
            tokens_in=10,
            tokens_out=20,
        )
        assert message is not None
        assert message.role == MessageRole.USER
        assert message.content == "Salom"
        assert message.tokens_in == 10
        assert message.tokens_out == 20

    def test_updates_conversation_last_message_at(self, conversation):
        save_message(conversation_id=str(conversation.id), content="Salom")
        conversation.refresh_from_db()
        assert conversation.last_message_at is not None

    def test_by_session_id_when_no_conversation_id(self, conversation):
        message = save_message(session_id=conversation.session_id, content="Salom")
        assert message is not None
        assert message.conversation_id == conversation.id

    def test_default_role_is_assistant(self, conversation):
        message = save_message(conversation_id=str(conversation.id), content="Salom")
        assert message.role == MessageRole.ASSISTANT

    def test_parses_tool_fields(self, conversation):
        message = save_message(
            conversation_id=str(conversation.id),
            role=MessageRole.TOOL,
            content="",
            tool_calls_json='[{"name": "catalog_search"}]',
            tool_result_json='{"ok": true}',
        )
        assert message.tool_calls == [{"name": "catalog_search"}]
        assert message.tool_result == {"ok": True}

    def test_missing_conversation_returns_none(self):
        assert save_message(conversation_id=str(uuid.uuid4()), content="x") is None
        assert Message.objects.count() == 0

    def test_idempotent(self, conversation):
        """Bir xil xabar ikki marta kelsa bitta yozuv qoladi (13.9)."""
        kwargs = {
            "conversation_id": str(conversation.id),
            "role": MessageRole.USER,
            "content": "Bir xil xabar",
            "tokens_in": 5,
            "tokens_out": 7,
        }
        save_message(**kwargs)
        save_message(**kwargs)
        assert Message.objects.filter(conversation=conversation).count() == 1


class TestGenerateConversationTitle:
    """13.3 — `generate_conversation_title` taski."""

    def test_uses_provided_text(self, conversation):
        title = generate_conversation_title(str(conversation.id), message_text="  Qanday  pardalar bor?\n")
        conversation.refresh_from_db()
        assert conversation.title == "Qanday pardalar bor?"
        assert title == conversation.title

    def test_reads_first_user_message(self, conversation):
        save_message(conversation_id=str(conversation.id), role=MessageRole.USER, content="Zuvayda mato kerak")
        title = generate_conversation_title(str(conversation.id))
        assert title == "Zuvayda mato kerak"

    def test_does_not_overwrite_existing_title(self, conversation):
        conversation.title = "Eski sarlavha"
        conversation.save(update_fields=["title"])
        title = generate_conversation_title(str(conversation.id), message_text="Yangi")
        assert title == "Eski sarlavha"
        conversation.refresh_from_db()
        assert conversation.title == "Eski sarlavha"

    def test_title_length_taken_from_calcrule(self, conversation):
        from apps.pricing.models import CalcRule

        CalcRule.objects.create(
            key="conversation_title_max_len",
            value="25",
            unit="chars",
            description="Suhbat sarlavhasi uzunligi",
        )
        title = generate_conversation_title(str(conversation.id), message_text="juda uzun matn " * 10)
        assert len(title) == 25

    def test_missing_conversation_returns_none(self):
        assert generate_conversation_title(str(uuid.uuid4())) is None


class TestArchiveOldConversations:
    """13.5 — `archive_old_conversations` taski."""

    def _old_conversation(self, conversation):
        old = Conversation.objects.create(
            tenant=conversation.tenant,
            user=conversation.user,
            session_id=str(uuid.uuid4()),
            title="Eski",
        )
        Conversation.objects.filter(pk=old.pk).update(
            last_message_at=timezone.now() - dt.timedelta(days=200)
        )
        return old

    def test_archives_old_active_conversations(self, conversation):
        old = self._old_conversation(conversation)
        archived = archive_old_conversations()
        old.refresh_from_db()
        assert archived == 1
        assert old.status == ConversationStatus.ARCHIVED

    def test_keeps_recent_conversations_active(self, conversation):
        archived = archive_old_conversations()
        conversation.refresh_from_db()
        assert archived == 0
        assert conversation.status == ConversationStatus.ACTIVE

    def test_idempotent(self, conversation):
        """Arxivlangan suhbat qayta arxivlanmaydi (13.9)."""
        old = self._old_conversation(conversation)
        first = archive_old_conversations()
        second = archive_old_conversations()
        assert first == 1
        assert second == 0
        old.refresh_from_db()
        assert old.status == ConversationStatus.ARCHIVED


class TestSaveMessageAndUsage:
    """13.1 + 13.2 orkestratsiyasi — `save_message_and_usage`."""

    def _event(self, **overrides):
        payload = {
            "kind": "done",
            "content": "Tavsiyam: atlas parda",
            "usage": {"prompt_tokens": 120, "completion_tokens": 80, "latency_ms": 340},
        }
        payload.update(overrides)
        return payload

    def test_saves_messages_usage_and_title(self, conversation):
        save_message_and_usage(
            conversation_id=str(conversation.id),
            user_message_content="Menga parda kerak",
            ai_event_data=self._event(),
            tenant_id=str(conversation.tenant_id),
        )
        assert Message.objects.filter(conversation=conversation).count() == 2
        assert (
            Message.objects.filter(conversation=conversation, role=MessageRole.USER).first().content
            == "Menga parda kerak"
        )
        assert UsageRecord.objects.filter(conversation=conversation.id).count() == 1
        conversation.refresh_from_db()
        assert conversation.title == "Menga parda kerak"

    def test_idempotent(self, conversation):
        """Ikki marta ishlasa takror yozuv yaratilmaydi (13.9)."""
        kwargs = {
            "conversation_id": str(conversation.id),
            "user_message_content": "Salom",
            "ai_event_data": self._event(content="Tavsiya"),
            "tenant_id": str(conversation.tenant_id),
        }
        save_message_and_usage(**kwargs)
        save_message_and_usage(**kwargs)
        assert Message.objects.filter(conversation=conversation).count() == 2
        assert UsageRecord.objects.filter(conversation=conversation.id).count() == 1

    def test_missing_conversation_is_noop(self):
        save_message_and_usage(
            conversation_id=str(uuid.uuid4()),
            user_message_content="Salom",
            ai_event_data=self._event(),
            tenant_id="",
        )
        assert Message.objects.count() == 0
        assert UsageRecord.objects.count() == 0


class TestRetryConfiguration:
    """13.9 — har bir taskda retry sozlamalari borligi."""

    def test_chat_tasks_have_retry_config(self):
        tasks = (
            save_message,
            generate_conversation_title,
            archive_old_conversations,
            save_message_and_usage,
        )
        for task in tasks:
            assert task.max_retries == 3
            assert task.retry_backoff is True
            assert Exception in task.autoretry_for