from __future__ import annotations

from rest_framework.exceptions import NotAuthenticated, ValidationError

from apps.common.exceptions import custom_exception_handler


def test_custom_exception_handler_flattens_nested_validation_errors() -> None:
    exc = ValidationError(
        {
            "price": ["0 dan katta bo'lishi kerak"],
            "parts": [{"name": ["Bo'sh bo'lishi mumkin emas"]}],
            "non_field_errors": ["Kamida bitta bo'lak kerak"],
        }
    )

    response = custom_exception_handler(exc, {"view": None, "request": None})

    assert response is not None
    assert response.status_code == 400
    assert response.data == {
        "detail": "Ma'lumotlar noto'g'ri",
        "code": "validation_error",
        "errors": {
            "price": "0 dan katta bo'lishi kerak",
            "parts.0.name": "Bo'sh bo'lishi mumkin emas",
            "non_field_errors": "Kamida bitta bo'lak kerak",
        },
    }


def test_custom_exception_handler_uses_uzbek_auth_message() -> None:
    exc = NotAuthenticated()

    response = custom_exception_handler(exc, {"view": None, "request": None})

    assert response is not None
    assert response.data["detail"] == "Tizimga kirish talab qilinadi"
    assert response.data["code"] == "not_authenticated"
    assert response.data["errors"] == {}
