"""Kontrakt 1.1 gateway: `ChatRequest.context` kalitlari va `stage` event'i."""

import asyncio
import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.chat.models import Conversation
from apps.chat.services import build_agent_context
from apps.chat.tasks import update_conversation_stage
from apps.common.choices import ConversationMode, ConversationStage

pytestmark = pytest.mark.django_db


class MockEvent:
    def __init__(self, kind, content="", result=""):
        self.kind = kind
        self.content = content
        self.result = result


def _to_dict(obj, **kwargs):
    return {"kind": obj.kind, "content": obj.content, "result": obj.result}


async def _read(response):
    chunks = []
    async for chunk in response.streaming_content:
        chunks.append(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk)
    return "".join(chunks)


def test_build_agent_context_has_contract_keys(conversation_factory, manager_user):
    conv = conversation_factory(user=manager_user)
    ctx = build_agent_context(conv, manager_user)
    assert ctx == {
        "role": "manager",
        "customer_mode": "0",
        "conversation_id": str(conv.id),
    }

    conv.mode = ConversationMode.CUSTOMER
    assert build_agent_context(conv, manager_user)["customer_mode"] == "1"


@patch("apps.chat.views.chat_stream")
def test_gateway_passes_role_and_customer_mode_to_agent(
    mock_chat_stream, api_client, employee_user, conversation_factory
):
    conv = conversation_factory(user=employee_user, mode=ConversationMode.CUSTOMER)
    mock_chat_stream.return_value = iter([MockEvent("start"), MockEvent("done")])

    api_client.force_authenticate(user=employee_user)
    url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})
    with (
        patch("apps.chat.views.MessageToDict", side_effect=_to_dict),
        patch("apps.chat.views.save_message_and_usage"),
    ):
        response = api_client.post(url, {"content": "salom"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        asyncio.run(_read(response))

    context = mock_chat_stream.call_args.kwargs["context"]
    assert context["role"] == "employee"
    assert context["customer_mode"] == "1"
    assert context["conversation_id"] == str(conv.id)


@patch("apps.chat.views.update_conversation_stage")
@patch("apps.chat.views.chat_stream")
def test_stage_event_is_forwarded_and_queued_to_celery(
    mock_chat_stream, mock_stage_task, api_client, employee_user, conversation_factory
):
    conv = conversation_factory(user=employee_user)
    state = json.dumps({"room": "living"})
    mock_chat_stream.return_value = iter(
        [MockEvent("start"), MockEvent("stage", "measure", state), MockEvent("done")]
    )

    api_client.force_authenticate(user=employee_user)
    url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})
    with (
        patch("apps.chat.views.MessageToDict", side_effect=_to_dict),
        patch("apps.chat.views.save_message_and_usage"),
    ):
        response = api_client.post(url, {"content": "salom"}, format="json")
        content = asyncio.run(_read(response))

    # Event mobilga 1:1 o'tadi (rules §7)
    assert '"kind": "stage", "content": "measure"' in content
    # DB yozuvi oqimni bloklamaydi — Celery'ga (rules §7)
    mock_stage_task.delay.assert_called_once_with(
        conversation_id=str(conv.id), stage="measure", state_json=state
    )


def test_update_conversation_stage_task(conversation_factory, employee_user):
    conv = conversation_factory(user=employee_user)
    assert conv.stage == ConversationStage.NEED

    ok = update_conversation_stage(
        conversation_id=str(conv.id), stage="calc", state_json='{"cornice_length_m": 4.2}'
    )
    assert ok is True
    conv.refresh_from_db()
    assert conv.stage == ConversationStage.CALC
    assert conv.context["agent_state"] == {"cornice_length_m": 4.2}

    # Idempotent: qayta chaqirilsa o'zgarmaydi
    assert update_conversation_stage(conversation_id=str(conv.id), stage="calc") is True
    conv.refresh_from_db()
    assert conv.stage == ConversationStage.CALC
    assert conv.context["agent_state"] == {"cornice_length_m": 4.2}


def test_update_conversation_stage_ignores_unknown_stage(conversation_factory, employee_user):
    conv = conversation_factory(user=employee_user)
    assert update_conversation_stage(conversation_id=str(conv.id), stage="teleport") is False
    assert Conversation.objects.get(pk=conv.pk).stage == ConversationStage.NEED


@patch("apps.chat.views.set_conversation_title")
@patch("apps.chat.views.chat_stream")
def test_title_event_is_forwarded_and_queued_to_celery(
    mock_chat_stream, mock_title_task, api_client, employee_user, conversation_factory
):
    """Go birinchi navbatdan keyin `title` event yuboradi — mobilga o'tadi, Celery saqlaydi."""
    conv = conversation_factory(user=employee_user)
    mock_chat_stream.return_value = iter(
        [MockEvent("start"), MockEvent("title", "Oshxona uchun parda"), MockEvent("done")]
    )

    api_client.force_authenticate(user=employee_user)
    url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})
    with (
        patch("apps.chat.views.MessageToDict", side_effect=_to_dict),
        patch("apps.chat.views.save_message_and_usage"),
    ):
        response = api_client.post(url, {"content": "salom"}, format="json")
        content = asyncio.run(_read(response))

    assert '"kind": "title", "content": "Oshxona uchun parda"' in content
    mock_title_task.delay.assert_called_once_with(
        conversation_id=str(conv.id), title="Oshxona uchun parda"
    )
