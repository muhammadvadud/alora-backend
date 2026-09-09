"""Agent.Health tekshiruvi — config/health.py dan ishlatiladi."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


def grpc_health() -> dict[str, str | int]:
    """Go agentning sog'lig'ini tekshiradi.

    Returns:
        {"status": "ok"|"error", "detail": "..."} — config/health.py uchun.
    """
    from apps.chat.grpc_client import health_check

    try:
        result = health_check(deadline_seconds=5.0)

        if result["status"] == "ok":
            logger.info(
                "gRPC agent sog'lig'i tekshirildi",
                version=result["version"],
                active_sessions=result["active_sessions"],
            )
            return {
                "status": "ok",
                "version": result["version"],
                "active_sessions": result["active_sessions"],
            }

        logger.warning(
            "gRPC agent holati",
            status=result["status"],
            last_error=result["last_error"],
        )
        return {
            "status": "error",
            "detail": result["last_error"] or result["status"],
        }

    except Exception as e:  # noqa: BLE001
        logger.error("gRPC agent tekshiruvidagi xato", error=str(e))
        return {
            "status": "error",
            "detail": str(e),
        }
