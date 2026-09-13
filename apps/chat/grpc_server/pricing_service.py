"""Pricing gRPC servisi — hisob-kitobning yagona Django kirish nuqtasi."""

from __future__ import annotations

import json
from typing import Any

import grpc
import structlog
from django.core.exceptions import ValidationError

from apps.pricing.services.calculator import calculate_preview
from grpc_gen import alora_pb2, alora_pb2_grpc

logger = structlog.get_logger(__name__)


def _validation_fields(exc: ValidationError) -> dict[str, str]:
    """Django ValidationError maydonlarini proto uchun yassi JSON'ga o'giradi."""

    if exc.message_dict:
        return {
            str(field): ", ".join(str(message) for message in messages)
            for field, messages in exc.message_dict.items()
        }
    return {"detail": ", ".join(str(message) for message in exc.messages)}


class PricingServicer(alora_pb2_grpc.PricingServicer):
    """Go agentdan kelgan sinxron narx hisoblash so'rovlarini bajaradi."""

    def CalcPreview(  # type: ignore[no-untyped-def]
        self, request: Any, context: grpc.ServicerContext
    ) -> Any:
        """JSON payload'ni Django kalkulyatoriga uzatib, JSON natija qaytaradi."""

        try:
            payload = json.loads(request.payload_json)
        except (TypeError, json.JSONDecodeError):
            return alora_pb2.CalcPreviewResponse(error="payload_json noto'g'ri JSON")

        if not isinstance(payload, dict):
            return alora_pb2.CalcPreviewResponse(error="payload_json obyekt bo'lishi kerak")

        try:
            result = calculate_preview(payload, user_role=request.user_role or None)
            return alora_pb2.CalcPreviewResponse(
                result_json=json.dumps(result, ensure_ascii=False),
            )
        except ValidationError as exc:
            fields = _validation_fields(exc)
            return alora_pb2.CalcPreviewResponse(
                error="Ma'lumotlar noto'g'ri",
                error_fields_json=json.dumps(fields, ensure_ascii=False),
            )
        except Exception:
            logger.exception(
                "Pricing hisoblashda kutilmagan xato",
                session_id=request.session_id,
                tenant_id=request.tenant_id,
            )
            return alora_pb2.CalcPreviewResponse(error="hisob xizmatida xato")
