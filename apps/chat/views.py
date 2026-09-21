"""Suhbat API view'lari."""

from __future__ import annotations

import json

from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from google.protobuf.json_format import MessageToDict
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.exceptions import AgentUnavailable
from apps.chat.grpc_client import chat_stream
from apps.chat.models import Conversation
from apps.chat.permissions import IsConversationOwnerOrManager
from apps.chat.selectors import get_messages_for_conversation, get_transcript
from apps.chat.serializers import ConversationSerializer, MessageSerializer
from apps.chat.services import (
    archive_conversation,
    build_agent_context,
    check_rate_limit,
    check_usage_limit,
    reset_conversation_context,
)
from apps.chat.tasks import (
    save_message_and_usage,
    set_conversation_title,
    update_conversation_stage,
)
from apps.common.models import TenantScopedQuerySetMixin
from apps.common.pagination import StandardCursorPagination


class ConversationViewSet(
    TenantScopedQuerySetMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Suhbatlar uchun ViewSet."""

    serializer_class = ConversationSerializer
    permission_classes = (IsConversationOwnerOrManager,)
    pagination_class = StandardCursorPagination

    def get_queryset(self):
        user = self.request.user
        qs = Conversation.objects.filter(tenant_id=user.tenant_id).order_by("-updated_at")
        # Bosh sahifa ro'yxati — har kim faqat O'Z suhbatlarini ko'radi (manager ham).
        # Xodimlar suhbatlari boshqaruvda: /team/employees/{id}/conversations/.
        # Bitta suhbatni ochish (retrieve/messages) manager uchun tenant bo'yicha ochiq.
        if self.action == "list" or getattr(user, "role", None) == "employee":
            qs = qs.filter(user=user)
        return qs

    def perform_create(self, serializer):
        import uuid

        serializer.save(
            user=self.request.user, tenant=self.request.user.tenant, session_id=str(uuid.uuid4())
        )

    def perform_destroy(self, instance):
        archive_conversation(instance)

    @extend_schema(summary="Kontekstni tozalash", responses={200: dict})
    @action(detail=True, methods=["post"])
    def reset(self, request, pk=None):
        conversation = self.get_object()
        reset_conversation_context(conversation)
        return Response({"status": "Kontekst tozalandi."})

    @extend_schema(summary="Suhbat transkripti", responses={200: dict})
    @action(detail=True, methods=["get"])
    def transcript(self, request, pk=None):
        conversation = self.get_object()
        transcript = get_transcript(conversation.id)
        return Response(transcript)


class EventStreamRenderer(BaseRenderer):
    """`Accept: text/event-stream` uchun renderer — SSE mijozlari (mobil ilova,
    EventSource) shu header'ni yuboradi; u bo'lmasa DRF 406 qaytarardi.
    Javob `StreamingHttpResponse` bo'lgani uchun render chaqirilmaydi;
    xato holatida (`Response`) JSON qaytariladi."""

    media_type = "text/event-stream"
    format = "sse"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return JSONRenderer().render(data, "application/json", renderer_context)


class ConversationMessagesView(APIView):
    """Suhbat xabarlarini olish (GET) va SSE orqali yuborish (POST)."""

    permission_classes = (IsConversationOwnerOrManager,)
    renderer_classes = (JSONRenderer, EventStreamRenderer)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        # Oddiy (xato) javob SSE renderer bilan kelishilgan bo'lsa ham JSON sifatida
        # belgilanadi — mijoz `detail` ni parse qila olsin (API-GUIDE §xato formati).
        if isinstance(response, Response) and isinstance(
            getattr(response, "accepted_renderer", None), EventStreamRenderer
        ):
            response.content_type = "application/json"
        return response

    serializer_class = MessageSerializer
    throttle_scope = "chat"

    @extend_schema(
        summary="Suhbat xabarlarini olish",
        responses={200: MessageSerializer(many=True)},
    )
    def get(self, request, pk):
        user = request.user
        try:
            if getattr(user, "role", None) == "employee":
                conversation = Conversation.objects.get(id=pk, user=user, is_active=True)
            else:
                conversation = Conversation.objects.get(id=pk, tenant=user.tenant, is_active=True)
        except Conversation.DoesNotExist:
            return Response({"detail": "Suhbat topilmadi."}, status=404)

        messages_qs = get_messages_for_conversation(conversation.id)
        paginator = StandardCursorPagination()
        page = paginator.paginate_queryset(messages_qs, request)

        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages_qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="AI javobini SSE orqali olish",
        responses={200: MessageSerializer(many=True)},
    )
    def post(self, request, pk):
        user = request.user
        tenant_id = str(user.tenant.id) if getattr(user, "tenant", None) else ""

        try:
            if getattr(user, "role", None) == "employee":
                conversation = Conversation.objects.get(id=pk, user=user, is_active=True)
            else:
                conversation = Conversation.objects.get(id=pk, tenant=user.tenant, is_active=True)
        except Conversation.DoesNotExist:
            return Response({"detail": "Suhbat topilmadi."}, status=404)

        message_text = request.data.get("content", "")

        check_usage_limit(user)
        check_rate_limit(user)

        agent_context = build_agent_context(conversation, user)

        import asyncio

        async def event_generator():
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue(maxsize=100)
            call_ref = [None]

            def _consume():
                call = None
                try:
                    call = chat_stream(
                        session_id=conversation.session_id,
                        user_id=str(user.id),
                        tenant_id=tenant_id,
                        message=message_text,
                        context=agent_context,
                        deadline_seconds=60.0,
                    )
                    call_ref[0] = call
                    for event in call:
                        asyncio.run_coroutine_threadsafe(queue.put(event), loop).result()
                    asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()
                except Exception as e:  # noqa: BLE001
                    asyncio.run_coroutine_threadsafe(queue.put(e), loop).result()
                    if call is not None:
                        call.cancel()

            pump_task = asyncio.create_task(asyncio.to_thread(_consume))

            try:
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    if isinstance(event, Exception):
                        import grpc

                        if isinstance(event, AgentUnavailable) or (
                            hasattr(event, "code") and event.code() == grpc.StatusCode.UNAVAILABLE
                        ):
                            yield f"data: {json.dumps({'kind': 'error', 'detail': 'AI xizmati vaqtincha ishlamayapti'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'kind': 'error', 'detail': str(event)})}\n\n"
                        break

                    event_dict = MessageToDict(event, preserving_proto_field_name=True)

                    if event_dict.get("kind") == "stage":
                        # Bosqich Django'da saqlanadi (manager ko'radi); event mobilga 1:1 o'tadi.
                        update_conversation_stage.delay(
                            conversation_id=str(conversation.id),
                            stage=event_dict.get("content", ""),
                            state_json=event_dict.get("result", ""),
                        )

                    if event_dict.get("kind") == "title" and event_dict.get("content"):
                        # AI birinchi navbatdan keyin qo'ygan sarlavha (Go title.go).
                        set_conversation_title.delay(
                            conversation_id=str(conversation.id),
                            title=event_dict["content"],
                        )

                    yield f"data: {json.dumps(event_dict)}\n\n"

                    if event_dict.get("kind") == "done":
                        save_message_and_usage.delay(
                            conversation_id=str(conversation.id),
                            user_message_content=message_text,
                            ai_event_data=event_dict,
                            tenant_id=tenant_id,
                        )
            except (asyncio.CancelledError, GeneratorExit):
                if call_ref[0] is not None:
                    call_ref[0].cancel()
                pump_task.cancel()
                raise

        return StreamingHttpResponse(event_generator(), content_type="text/event-stream")
