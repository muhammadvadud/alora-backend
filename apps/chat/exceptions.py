"""gRPC xatoliklari — AI agent bilan bog'liq istisnolar."""

from __future__ import annotations

from rest_framework.exceptions import APIException


class AgentUnavailable(APIException):
    """Go agent ishlamaganda yoki ulanib bo'lmaganda foydalaniladi."""

    status_code = 503
    default_detail = "AI xizmati vaqtincha ishlamayapti"
    default_code = "agent_unavailable"


class AgentTimeout(APIException):
    """Go agent javob berish muddati o'tganda."""

    status_code = 504
    default_detail = "AI xizmati javob bermadi (timeout)"
    default_code = "agent_timeout"


class AgentConnectionError(APIException):
    """Go agent bilan ulanish xatosi."""

    status_code = 503
    default_detail = "AI xizmatiga ulanib bo'lmadi"
    default_code = "agent_connection_error"
