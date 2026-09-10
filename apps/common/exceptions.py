"""Yagona xato formati."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions as drf_exceptions
from rest_framework.exceptions import APIException, ErrorDetail, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import exception_handler as drf_exception_handler

try:  # pragma: no cover - structlog bor bo'lsa undan foydalaniladi
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:  # pragma: no cover - lokal fallback
    import logging

    logger = logging.getLogger(__name__)


DEFAULT_DETAIL = str(_("Kutilmagan xatolik yuz berdi"))
VALIDATION_DETAIL = str(_("Ma'lumotlar noto'g'ri"))
NOT_AUTHENTICATED_DETAIL = str(_("Tizimga kirish talab qilinadi"))
PERMISSION_DENIED_DETAIL = str(_("Bu amal uchun ruxsat yo'q"))
NOT_FOUND_DETAIL = str(_("Topilmadi"))
METHOD_NOT_ALLOWED_DETAIL = str(_("Bu usul qo'llab-quvvatlanmaydi"))
PARSE_ERROR_DETAIL = str(_("So'rov formati noto'g'ri"))
THROTTLED_DETAIL = str(_("So'rovlar soni cheklangan"))

EXCEPTION_MESSAGES: tuple[tuple[type[APIException], str], ...] = (
    (drf_exceptions.NotAuthenticated, NOT_AUTHENTICATED_DETAIL),
    (drf_exceptions.AuthenticationFailed, str(_("Kirish ma'lumotlari noto'g'ri"))),
    (drf_exceptions.PermissionDenied, PERMISSION_DENIED_DETAIL),
    (drf_exceptions.NotFound, NOT_FOUND_DETAIL),
    (drf_exceptions.MethodNotAllowed, METHOD_NOT_ALLOWED_DETAIL),
    (drf_exceptions.ParseError, PARSE_ERROR_DETAIL),
    (drf_exceptions.Throttled, THROTTLED_DETAIL),
)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """DRF xatolarini yagona, yassi formatga keltiradi."""

    response = drf_exception_handler(exc, context)
    status_code: int = HTTP_500_INTERNAL_SERVER_ERROR
    detail = DEFAULT_DETAIL
    code = "error"
    errors: dict[str, str] = {}

    if isinstance(exc, ValidationError):
        status_code = HTTP_400_BAD_REQUEST
        detail = VALIDATION_DETAIL
        code = "validation_error"
        errors = _flatten_validation_errors(exc.detail)
    else:
        if isinstance(exc, APIException):
            status_code = getattr(exc, "status_code", HTTP_500_INTERNAL_SERVER_ERROR)
            code = getattr(exc, "default_code", code)
            detail = _resolve_exception_message(exc)

    if response is None:
        logger.warning("handled_exception")
        return Response({"detail": detail, "code": code, "errors": errors}, status=status_code)

    response.data = {"detail": detail, "code": code, "errors": errors}
    return response


def _resolve_exception_message(exc: APIException) -> str:
    """APIException uchun o'zbekcha matnni qaytaradi."""

    for exception_type, message in EXCEPTION_MESSAGES:
        if isinstance(exc, exception_type):
            return message
    if isinstance(exc, ValidationError):
        return VALIDATION_DETAIL
    return str(getattr(exc, "detail", DEFAULT_DETAIL))


def _flatten_validation_errors(detail: Any, prefix: str = "") -> dict[str, str]:
    """Nested serializer xatolarini maydonlarga yassilaydi."""

    flattened: dict[str, str] = {}

    if isinstance(detail, Mapping):
        for key, value in detail.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(_flatten_validation_errors(value, child_prefix))
        return flattened

    if isinstance(detail, list):
        if not detail:
            flattened[prefix or "non_field_errors"] = ""
            return flattened

        if all(not isinstance(item, (dict, list)) for item in detail):
            flattened[prefix or "non_field_errors"] = "; ".join(
                _stringify_error(item) for item in detail
            )
            return flattened

        for index, item in enumerate(detail):
            child_prefix = f"{prefix}.{index}" if prefix else str(index)
            flattened.update(_flatten_validation_errors(item, child_prefix))
        return flattened

    flattened[prefix or "non_field_errors"] = _stringify_error(detail)
    return flattened


def _stringify_error(value: Any) -> str:
    """ErrorDetail va boshqa qiymatlarni matnga aylantiradi."""

    if isinstance(value, ErrorDetail):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return str(value)
