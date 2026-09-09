"""14.7 - Gateway overhead <= 150 ms."""

import statistics
import time
import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.chat.models import Conversation

pytestmark = pytest.mark.django_db

def test_gateway_overhead(api_client, employee_user):
    if not employee_user.tenant.pk or not type(employee_user.tenant).objects.filter(pk=employee_user.tenant.pk).exists():
        employee_user.tenant.save()
    if employee_user._state.adding:
        employee_user.save()
        
    conv = Conversation.objects.create(
        tenant=employee_user.tenant,
        user=employee_user,
        title="Overhead Test",
        session_id=str(uuid.uuid4())
    )
    api_client.force_authenticate(user=employee_user)
    
    url = reverse("chat:conversation-messages-stream", kwargs={"pk": str(conv.id)})
    
    class MockEvent:
        def __init__(self, kind, content=""):
            self.kind = kind
            self.content = content
            
    class MockCall:
        def __init__(self, events):
            self.events = iter(events)
        def __iter__(self):
            return self.events
        def __next__(self):
            return next(self.events)
        def cancel(self):
            pass

    def mock_chat_stream_side_effect(*args, **kwargs):
        return MockCall([
            MockEvent("start"),
            MockEvent("content", "hello from mock"),
            MockEvent("done")
        ])

    measurements = []
    
    with (
        patch("apps.chat.views.chat_stream", side_effect=mock_chat_stream_side_effect),
        patch("apps.chat.views.MessageToDict", side_effect=lambda obj, **kwargs: {"kind": obj.kind, "content": obj.content}),
        patch("apps.chat.views.check_rate_limit", return_value=None),
        patch("apps.chat.views.check_usage_limit", return_value=None),
    ):
                    for _ in range(5):
                        start = time.perf_counter()
                        
                        response = api_client.post(url, {"content": "salom"}, format="json")
                        assert response.status_code == 200
                        
                        import asyncio
                        async def _read_stream(r):
                            chunks = []
                            async for chunk in r.streaming_content:
                                if type(chunk) == bytes:
                                    chunks.append(chunk.decode("utf-8"))
                                else:
                                    chunks.append(chunk)
                            return "".join(chunks)
                            
                        asyncio.run(_read_stream(response))
                        end = time.perf_counter()
                        
                        measurements.append((end - start) * 1000)  # ms
                        
    median_time = statistics.median(measurements)
    print(f"Median gateway overhead: {median_time:.2f} ms")
    assert median_time <= 150, f"Gateway overhead is {median_time:.2f} ms, expected <= 150 ms"
