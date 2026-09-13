"""Pricing gRPC servisi testlari."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock

import pytest

from apps.chat.grpc_server.pricing_service import PricingServicer
from grpc_gen import alora_pb2
from tests.pricing.test_reference_cases import _load_fixture, _seed_catalog, _seed_pricing_models


@pytest.fixture()
def pricing_reference_data(db: Any) -> dict[str, Any]:
    """gRPC etalon testlari uchun katalog va pricing seed'ini yaratadi."""

    data = _load_fixture()
    _seed_pricing_models(data)
    _seed_catalog(data)
    return data


@pytest.mark.parametrize("case_index", range(20), ids=lambda index: f"case-{index + 1:02d}")
def test_calc_preview_grpc_matches_reference_case(
    pricing_reference_data: dict[str, Any], case_index: int
) -> None:
    """Pricing RPC etalon kalkulyator natijasini o'zgartirmasdan uzatadi."""

    case = pricing_reference_data["cases"][case_index]
    request = alora_pb2.CalcPreviewRequest(
        payload_json=json.dumps(case["input"]), user_role="manager"
    )
    response = PricingServicer().CalcPreview(request, Mock())

    assert json.loads(response.result_json) == case["expected"]
    assert response.error == ""


def test_calc_preview_grpc_rejects_invalid_json() -> None:
    """Noto'g'ri JSON umumiy xato bilan qaytadi."""

    response = PricingServicer().CalcPreview(alora_pb2.CalcPreviewRequest(payload_json="{"), Mock())

    assert response.error
    assert response.result_json == ""


def test_calc_preview_grpc_maps_unknown_variant_error(
    pricing_reference_data: dict[str, Any],
) -> None:
    """Kalkulyator ValidationError'i maydon xatosiga map qilinadi."""

    payload = _load_fixture()["cases"][0]["input"]
    payload["measurements"][0]["parts"][0]["variant_id"] = "00000000-0000-0000-0000-000000000000"
    response = PricingServicer().CalcPreview(
        alora_pb2.CalcPreviewRequest(payload_json=json.dumps(payload), user_role="manager"),
        Mock(),
    )

    assert json.loads(response.error_fields_json)["variant_id"] == "Variant topilmadi"
