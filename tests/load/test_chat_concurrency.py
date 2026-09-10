"""14.6 - Yuk testi: 50 parallel chat sessiyasi.

Bu test konkurentlikni o'lchaydi, throttle'ni emas. Shuning uchun DRF
throttle chegaralari test davomida o'chiriladi — aks holda `chat: 30/minute`
chegarasi 50 ta parallel so'rovning bir qismini 429 bilan rad etadi va test
o'lchamoqchi bo'lgan narsani umuman tekshirmaydi.
"""

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from django.core.signals import request_finished
from django.db import close_old_connections, connection
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.chat.models import Conversation

pytestmark = pytest.mark.django_db(transaction=True)

@patch("rest_framework.throttling.SimpleRateThrottle.allow_request", return_value=True)
def test_50_concurrent_chat_sessions(_no_throttle, employee_user):
    """50 parallel chat sessiyasini simulyatsiya qilish."""
    
    if not employee_user.tenant.pk or not type(employee_user.tenant).objects.filter(pk=employee_user.tenant.pk).exists():
        employee_user.tenant.save()
    if employee_user._state.adding:
        employee_user.save()
    
    conversations = []
    for _ in range(50):
        c = Conversation.objects.create(
            tenant=employee_user.tenant,
            user=employee_user,
            title="Load Test",
            session_id=str(uuid.uuid4())
        )
        conversations.append(c)
    
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

    def mock_chat_stream_side_effect(*args, **kwargs):
        return MockCall([
            MockEvent("start"),
            MockEvent("content", "hello from mock"),
            MockEvent("done")
        ])

    def _run_single_session(conv):
        try:
            client = APIClient()
            client.force_authenticate(user=employee_user)
            url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})
            
            response = client.post(url, {"content": "salom"}, format="json")
            
            if response.status_code != status.HTTP_200_OK:
                return {"conv_id": conv.id, "error": f"Status {response.status_code}", "content": None}
                
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
            return {"conv_id": conv.id, "error": None, "content": content}
        finally:
            connection.close()

    request_finished.disconnect(close_old_connections)
    
    try:
        with (
            patch("apps.chat.views.chat_stream", side_effect=mock_chat_stream_side_effect),
            patch("apps.chat.views.MessageToDict", side_effect=lambda obj, **kwargs: {"kind": obj.kind, "content": obj.content}),
            patch("apps.chat.views.check_rate_limit", return_value=None),
            patch("apps.chat.views.check_usage_limit", return_value=None),
        ):
            start_time = time.perf_counter()
            with ThreadPoolExecutor(max_workers=50) as executor:
                results = list(executor.map(_run_single_session, conversations))
            end_time = time.perf_counter()
    finally:
        request_finished.connect(close_old_connections)

    assert end_time - start_time < 60, f"Test took {end_time - start_time} seconds"
    
    for res in results:
        assert res["error"] is None
        assert 'data: {"kind": "start"' in res["content"]
        assert 'data: {"kind": "content", "content": "hello from mock"}' in res["content"]
