"""Ichki gRPC chaqiruvlari uchun service-token interceptor."""

from __future__ import annotations

import hmac
from collections.abc import Callable
from typing import Any

import grpc
import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)


def _metadata_token(details: grpc.HandlerCallDetails) -> str:
    """RPC metadata'sidan service tokenni oladi."""

    for key, value in details.invocation_metadata:
        if key.lower() == "x-service-token":
            return value if isinstance(value, str) else ""
    return ""


def tokens_match(provided: str | None, expected: str | None) -> bool:
    """Ikki tokenni vaqtga bog'liq bo'lmagan usulda solishtiradi.

    `!=` operatori satrlarni qisqa-circuit (mexanizm bo'yicha) solishtiradi:
    birinchi farqli belgida to'xtaydi. Masalan `""` bilan `"ab..."` ni solishtirish
    uchun chaqiruvchi 1, `"ab"` bilan `"ac..."` ni solishtirish uchun 2 ta urinish
    kerak bo'lardi — bu token'ni bosqichma-bosqich topishga (oracle attack) imkon
    beradi. `hmac.compare_digest` esa har doim ikkala argumentning to'liq
    uzunligini tekshiradi va vaqtga bog'liq bo'lmagan taqqoslashni kafolatlaydi.

    `None` va bo'sh satr bir xil — "token yuborilmagan" holati. Kutilgan token
    bo'sh bo'lsa solishtirish har doim rad etadi: aks holda `"" == ""` bo'lib,
    token sozlanmagan prod'da tokensiz har qanday so'rov o'tib ketardi (fail-closed).
    """

    left = provided or ""
    right = expected or ""
    if not right:
        return False
    return hmac.compare_digest(left, right)


class ServiceTokenInterceptor(grpc.ServerInterceptor):
    """Barcha gRPC metodlarida `x-service-token`ni tekshiradi."""

    def intercept_service(  # type: ignore[no-untyped-def]
        self, continuation: Callable[[grpc.HandlerCallDetails], Any], handler_call_details: Any
    ) -> Any:
        handler = continuation(handler_call_details)
        method = getattr(handler_call_details, "method", "")
        if isinstance(method, str) and method.endswith("/Agent/Health"):
            return handler
        expected = getattr(settings, "AGENT_SERVICE_TOKEN", "")
        if not expected and getattr(settings, "DEBUG", False):
            logger.warning("AGENT_SERVICE_TOKEN bo'sh — gRPC auth dev rejimida o'chirilgan")
            return handler

        if handler is None:
            return None

        def check(context: grpc.ServicerContext) -> bool:
            if not tokens_match(_metadata_token(handler_call_details), expected):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "service token noto'g'ri")
            return True

        if handler.request_streaming and handler.response_streaming:
            return grpc.stream_stream_rpc_method_handler(
                lambda request_iterator, context: (
                    check(context) and handler.stream_stream(request_iterator, context)
                ),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.request_streaming:
            return grpc.stream_unary_rpc_method_handler(
                lambda request_iterator, context: (
                    check(context) and handler.stream_unary(request_iterator, context)
                ),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.response_streaming:
            return grpc.unary_stream_rpc_method_handler(
                lambda request, context: check(context) and handler.unary_stream(request, context),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        return grpc.unary_unary_rpc_method_handler(
            lambda request, context: check(context) and handler.unary_unary(request, context),
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
