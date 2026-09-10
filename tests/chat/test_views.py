"""Chat viewlari testlari."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.chat.exceptions import AgentUnavailable

pytestmark = pytest.mark.django_db


class TestConversationViews:
    """Conversation API testlari."""

    def test_employee_cannot_see_others_conversation(
        self, api_client, employee_user, conversation_factory
    ):
        """Xodim faqat o'zining suhbatini ko'ra oladi."""
        my_conv = conversation_factory(user=employee_user)
        other_conv = conversation_factory()  # Boshqa foydalanuvchiga tegishli

        api_client.force_authenticate(user=employee_user)
        url = reverse("chat:conversation-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ids = [item["id"] for item in response.data["results"]]
        assert str(my_conv.id) in ids
        assert str(other_conv.id) not in ids

    def test_manager_can_see_all_tenant_conversations(
        self, api_client, manager_user, conversation_factory
    ):
        """Boshqaruvchi barcha suhbatlarni ko'ra oladi."""
        my_conv = conversation_factory(user=manager_user, tenant=manager_user.tenant)
        other_conv = conversation_factory(tenant=manager_user.tenant)

        api_client.force_authenticate(user=manager_user)
        url = reverse("chat:conversation-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ids = [item["id"] for item in response.data["results"]]
        assert str(my_conv.id) in ids
        assert str(other_conv.id) in ids


class TestChatStream:
    """SSE Oqim testlari."""

    @patch("apps.chat.views.chat_stream")
    def test_stream_chat_messages_success(
        self, mock_chat_stream, api_client, employee_user, conversation_factory
    ):
        """Muvaffaqiyatli xabar oqimi."""
        conv = conversation_factory(user=employee_user)

        # Mock Go javobi
        class MockEvent:
            def __init__(self, kind, content=""):
                self.kind = kind
                self.content = content

        mock_chat_stream.return_value = iter(
            [MockEvent("start"), MockEvent("content", "salom"), MockEvent("done")]
        )

        api_client.force_authenticate(user=employee_user)
        url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})

        with patch(
            "apps.chat.views.MessageToDict",
            side_effect=lambda obj, **kwargs: {"kind": obj.kind, "content": obj.content},
        ):
            response = api_client.post(url, {"content": "salom"}, format="json")
            assert response.status_code == status.HTTP_200_OK
            import asyncio

            async def _read_stream():
                chunks = []
                async for chunk in response.streaming_content:
                    if type(chunk) == bytes:
                        chunks.append(chunk.decode("utf-8"))
                    else:
                        chunks.append(chunk)
                return "".join(chunks)

            content = asyncio.run(_read_stream())
        assert 'data: {"kind": "start", "content": ""}' in content
        assert 'data: {"kind": "content", "content": "salom"}' in content
        assert 'data: {"kind": "done", "content": ""}' in content

    @patch("apps.chat.views.chat_stream")
    def test_agent_unavailable_returns_error_event(
        self, mock_chat_stream, api_client, employee_user, conversation_factory
    ):
        """AgentUnavailable bo'lganda maxsus error event qaytariladi."""
        conv = conversation_factory(user=employee_user)

        mock_chat_stream.side_effect = AgentUnavailable()

        api_client.force_authenticate(user=employee_user)
        url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})

        response = api_client.post(url, {"content": "salom"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        import asyncio

        async def _read_stream():
            chunks = []
            async for chunk in response.streaming_content:
                if type(chunk) == bytes:
                    chunks.append(chunk.decode("utf-8"))
                else:
                    chunks.append(chunk)
            return "".join(chunks)

        content = asyncio.run(_read_stream())
        assert 'data: {"kind": "error", "detail": "AI xizmati vaqtincha ishlamayapti"}' in content

    @patch("apps.chat.services.cache.incr")
    def test_rate_limit_exceeded(
        self, mock_cache_incr, api_client, employee_user, conversation_factory
    ):
        """Limitdan oshib ketganda 429 xatosi qaytariladi."""
        conv = conversation_factory(user=employee_user)
        mock_cache_incr.return_value = 100  # Xodim limiti 10

        api_client.force_authenticate(user=employee_user)
        url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})

        response = api_client.post(url, {"content": "salom"}, format="json")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @patch("apps.chat.views.chat_stream")
    def test_client_disconnect_stops_stream(
        self, mock_chat_stream, api_client, employee_user, conversation_factory
    ):
        """Klient uzilganda oqim to'xtaydi (mock orqali)."""
        conv = conversation_factory(user=employee_user)

        class MockEvent:
            def __init__(self, kind, content=""):
                self.kind = kind
                self.content = content

        class MockCall:
            def __init__(self, events):
                self.events = iter(events)
                self.cancelled = False

            def __iter__(self):
                return self.events

            def __next__(self):
                return next(self.events)

            def cancel(self):
                self.cancelled = True

        mock_call = MockCall(
            [
                MockEvent("start"),
                MockEvent("content", "salom"),
                # Done is intentionally omitted to simulate mid-stream disconnect
            ]
        )
        mock_chat_stream.return_value = mock_call

        api_client.force_authenticate(user=employee_user)
        url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})

        with patch(
            "apps.chat.views.MessageToDict",
            side_effect=lambda obj, **kwargs: {"kind": obj.kind, "content": obj.content},
        ):
            response = api_client.post(url, {"content": "salom"}, format="json")
            assert response.status_code == status.HTTP_200_OK

            import asyncio

            async def _read_and_close():
                iterator = response.streaming_content.__aiter__()
                chunk = await iterator.__anext__()
                await iterator.aclose()  # This triggers GeneratorExit
                return chunk

            first_chunk = asyncio.run(_read_and_close())
            assert b'{"kind": "start"' in first_chunk

            # Allow background thread to process cancellation
            async def _wait():
                await asyncio.sleep(0.1)

            asyncio.run(_wait())

        assert mock_call.cancelled is True
