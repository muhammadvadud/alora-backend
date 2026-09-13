"""Backend servisi — Go → Django yozish operatsiyalari.

ReportUsage: Ishlatilgan tokenlar/xarajat haqida hisobot.
SaveOrderDraft: Buyurtma qoralamasini saqlash.
LogMessage: Suhbat xabarini saqlash.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import grpc
import structlog
from django.core.cache import cache
from django.core.exceptions import ValidationError

from grpc_gen import alora_pb2_grpc

logger = structlog.get_logger(__name__)


def report_usage(data: dict[str, Any]) -> dict[str, Any]:
    """Ishlatilgan tokenlar/xarajat haqida hisobot qabul qiladi.

    Celery task'ga uzatiladi — javob oqimini bloklamaslik uchun.

    Args:
        data: UsageRequest xabaridan olingan ma'lumotlar.

    Returns:
        {"success": True} yoki {"success": False, "error": "..."}.
    """
    usage = data.get("usage", {})

    try:
        # tasks.py Bosqich 13 da yoziladi — hozircha stub
        from apps.usage.tasks import save_usage_record

        save_usage_record.delay(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            tenant_id=data.get("tenant_id", ""),
            conversation_id=data.get("conversation_id", ""),
            message_id=data.get("message_id", ""),
            provider=usage.get("provider", ""),
            model=usage.get("model", ""),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            cached_tokens=usage.get("cached_tokens", 0),
            reasoning_tokens=usage.get("reasoning_tokens", 0),
            stt_seconds=usage.get("stt_seconds", 0.0),
            tts_chars=usage.get("tts_chars", 0),
            tool_calls_json=usage.get("tool_calls_json", "[]"),
            latency_ms=usage.get("latency_ms", 0),
            cost_usd=usage.get("cost_usd", 0.0),
            cost_uzs=usage.get("cost_uzs", 0.0),
        )

        logger.info(
            "Usage hisoboti qabul qilindi",
            session_id=data.get("session_id"),
            model=usage.get("model"),
        )

        return {"success": True, "message": ""}

    except Exception as e:  # noqa: BLE001
        logger.error("Usage hisobotini qayta ishlashda xato", error=str(e))
        return {"success": False, "error": str(e)}


def save_order_draft(data: dict[str, Any]) -> dict[str, Any]:
    """AI qoralamasidan snapshot narxli draft buyurtma yaratadi.

    Args:
        data: OrderDraftRequest xabaridan olingan ma'lumotlar.

    Returns:
        {"success": True, "order_id": "...", "order_number": "..."}.
    """
    try:
        from apps.accounts.models import User
        from apps.chat.models import Conversation
        from apps.orders.models import Order
        from apps.orders.services import create_order_from_draft

        items_json = data.get("items_json", "")
        cache_key = (
            "alora:order_draft:"
            + hashlib.sha256(f"{data.get('session_id', '')}:{items_json}".encode()).hexdigest()
        )
        cached_order_id = cache.get(cache_key)
        if cached_order_id:
            cached_order = Order.objects.filter(id=cached_order_id).first()
            if cached_order:
                return {
                    "success": True,
                    "order_id": str(cached_order.id),
                    "order_number": cached_order.number,
                    "error": "",
                }

        try:
            items = json.loads(items_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValidationError({"items_json": "Buyurtma ma'lumotlari noto'g'ri JSON"}) from exc
        if not isinstance(items, dict):
            raise ValidationError(
                {"items_json": "Buyurtma ma'lumotlari obyektdan iborat bo'lishi kerak"}
            )

        user = User.objects.filter(id=str(data.get("user_id", "")), is_active=True).first()
        if user is None:
            return {
                "success": False,
                "order_id": "",
                "order_number": "",
                "error": "foydalanuvchi topilmadi",
            }

        conversation = Conversation.objects.filter(id=str(data.get("conversation_id", ""))).first()
        payload = {
            **items,
            "customer_name": data.get("customer_name", ""),
            "customer_phone": data.get("customer_phone", ""),
            "address": data.get("address", ""),
            "note": data.get("note", ""),
        }
        for measurement in payload.get("measurements", []):
            measurement.setdefault("cornice_length_m", measurement.get("length"))
            measurement.setdefault("height_m", measurement.get("height"))
            if "coefficient" not in measurement and measurement.get("parts"):
                measurement["coefficient"] = measurement["parts"][0].get(
                    "coefficient", measurement["parts"][0].get("coef")
                )

        order, _ = create_order_from_draft(
            payload=payload, user=user, conversation_id=conversation.id if conversation else None
        )
        if conversation:
            conversation.order = order
            conversation.save(update_fields=["order", "updated_at"])
        cache.set(cache_key, str(order.id), timeout=300)
        return {
            "success": True,
            "order_id": str(order.id),
            "order_number": order.number,
            "error": "",
        }
    except ValidationError as exc:
        messages = exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        error = "; ".join(
            f"{key}: {', '.join(map(str, value if isinstance(value, list) else [value]))}"
            for key, value in messages.items()
        )
        return {"success": False, "order_id": "", "order_number": "", "error": error}
    except Exception as exc:  # noqa: BLE001
        logger.error("Buyurtmani saqlashda xato", error=str(exc))
        return {
            "success": False,
            "order_id": "",
            "order_number": "",
            "error": "buyurtmani saqlashda xato",
        }


def log_message(data: dict[str, Any]) -> dict[str, Any]:
    """Suhbat xabarini Celery'ga uzatadi (tarix uchun).

    Args:
        data: MessageLogRequest xabaridan olingan ma'lumotlar.

    Returns:
        {"success": True}.
    """
    try:
        # tasks.py Bosqich 13 da yoziladi — hozircha stub
        from apps.chat.tasks import save_message

        save_message.delay(
            session_id=data.get("session_id", ""),
            conversation_id=data.get("conversation_id", ""),
            role=data.get("role", ""),
            content=data.get("content", ""),
            tool_calls_json=data.get("tool_calls_json", ""),
            tool_result_json=data.get("tool_result_json", ""),
            audio_url=data.get("audio_url", ""),
            tokens_in=data.get("tokens_in", 0),
            tokens_out=data.get("tokens_out", 0),
        )

        logger.info(
            "Xabar log'ga yozildi",
            conversation_id=data.get("conversation_id"),
            role=data.get("role"),
        )

        return {"success": True, "message": ""}

    except Exception as e:  # noqa: BLE001
        logger.error("Xabar log'ini qayta ishlashda xato", error=str(e))
        return {"success": False, "error": str(e)}


class BackendServicer(alora_pb2_grpc.BackendServicer):
    """Backend gRPC servisining amalga oshirilishi.

    Generatsiya qilingan bazaviy klassdan meros oladi.
    """

    def ReportUsage(self, request: Any, context: grpc.ServicerContext) -> Any:  # type: ignore[no-untyped-def]
        """Go → Django: foydalanish hisoboti (Celery'ga uzatiladi)."""
        data = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "tenant_id": request.tenant_id,
            "conversation_id": request.conversation_id,
            "message_id": request.message_id,
            "usage": {
                "provider": request.usage.provider,
                "model": request.usage.model,
                "prompt_tokens": request.usage.prompt_tokens,
                "completion_tokens": request.usage.completion_tokens,
                "cached_tokens": request.usage.cached_tokens,
                "reasoning_tokens": request.usage.reasoning_tokens,
                "stt_seconds": request.usage.stt_seconds,
                "tts_chars": request.usage.tts_chars,
                "tool_calls_json": request.usage.tool_calls_json,
                "latency_ms": request.usage.latency_ms,
                "cost_usd": request.usage.cost_usd,
                "cost_uzs": request.usage.cost_uzs,
            },
        }

        result = report_usage(data)

        if not result["success"]:
            context.abort(grpc.StatusCode.INTERNAL, result.get("error", ""))

        from grpc_gen import alora_pb2

        return alora_pb2.Ack(success=True, message="")

    def SaveOrderDraft(  # type: ignore[no-untyped-def]
        self, request: Any, context: grpc.ServicerContext
    ) -> Any:
        """Go → Django: buyurtma qoralamasini saqlash (stub)."""
        data = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "tenant_id": request.tenant_id,
            "conversation_id": request.conversation_id,
            "customer_name": request.customer_name,
            "customer_phone": request.customer_phone,
            "address": request.address,
            "items_json": request.items_json,
            "note": request.note,
        }

        result = save_order_draft(data)

        from grpc_gen import alora_pb2

        return alora_pb2.OrderDraftResponse(
            order_id=result.get("order_id", ""),
            order_number=result.get("order_number", ""),
            success=result.get("success", False),
            error=result.get("error", ""),
        )

    def LogMessage(self, request: Any, context: grpc.ServicerContext) -> Any:  # type: ignore[no-untyped-def]
        """Go → Django: suhbat xabarini saqlash (Celery'ga uzatiladi)."""
        data = {
            "session_id": request.session_id,
            "conversation_id": request.conversation_id,
            "role": request.role,
            "content": request.content,
            "tool_calls_json": request.tool_calls_json,
            "tool_result_json": request.tool_result_json,
            "audio_url": request.audio_url,
            "tokens_in": request.tokens_in,
            "tokens_out": request.tokens_out,
        }

        result = log_message(data)

        if not result["success"]:
            context.abort(grpc.StatusCode.INTERNAL, result.get("error", ""))

        from grpc_gen import alora_pb2

        return alora_pb2.Ack(success=True, message="")
