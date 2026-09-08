"""Backend servisi — Go → Django yozish operatsiyalari.

ReportUsage: Ishlatilgan tokenlar/xarajat haqida hisobot.
SaveOrderDraft: Buyurtma qoralamasini saqlash.
LogMessage: Suhbat xabarini saqlash.
"""

from __future__ import annotations

import uuid
from typing import Any

import grpc
import structlog

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

    except Exception as e:
        logger.error("Usage hisobotini qayta ishlashda xato", error=str(e))
        return {"success": False, "error": str(e)}


def save_order_draft(data: dict[str, Any]) -> dict[str, Any]:
    """Buyurtma qoralamasini saqlash (AI tomonidan yaratilgan).

    Hozircha stub — orders app to'liq yozilgandan keyin
    haqiqiy logic qo'shiladi.

    Args:
        data: OrderDraftRequest xabaridan olingan ma'lumotlar.

    Returns:
        {"success": True, "order_id": "...", "order_number": "..."}.
    """
    try:
        # Hozircha faqat log yozamiz
        logger.info(
            "Buyurtma qoralamasi qabul qilindi (stub)",
            session_id=data.get("session_id"),
            customer_name=data.get("customer_name"),
            customer_phone=data.get("customer_phone"),
        )

        # Kelajakda orders app orqali:
        # from apps.orders.services import create_order_from_draft
        # order = create_order_from_draft(data)
        # return {"success": True, "order_id": str(order.id), "order_number": order.number}

        draft_id = str(uuid.uuid4())

        return {
            "success": True,
            "order_id": draft_id,
            "order_number": f"ALR-DRAFT-{draft_id[:8].upper()}",
            "error": "",
        }

    except Exception as e:
        logger.error("Buyurtma qoralamasini saqlashda xato", error=str(e))
        return {
            "success": False,
            "order_id": "",
            "order_number": "",
            "error": str(e),
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

    except Exception as e:
        logger.error("Xabar log'ini qayta ishlashda xato", error=str(e))
        return {"success": False, "error": str(e)}


class BackendServicer:
    """Backend gRPC servisining amalga oshirilishi.

    Asl bazaviy klass generatsiya kodida mavjud (alora_pb2_grpc.BackendServicer).
    Generatsiya qilingan bazaviy klassdan meros olish uchun shu klass etarli —
    `add_BackendServicer_to_server()` barcha kerakli metodlarni chaqiradi.
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
