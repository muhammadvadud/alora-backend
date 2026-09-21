"""Limit maydonida 0 — cheklov qo'yilmagan (bloklamaydi)."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from apps.usage.services import PeriodUsage, _is_exceeded


def _limit(**kw):
    base = {"max_tokens": 0, "max_cost_uzs": Decimal("0.00"), "max_messages": 0}
    base.update(kw)
    return SimpleNamespace(**base)


def test_nol_limit_bloklamaydi() -> None:
    usage = PeriodUsage(tokens=500, cost_uzs=Decimal("0.00"), messages=3)
    assert _is_exceeded(_limit(max_tokens=10000), usage) is False


def test_faqat_token_limiti_oshsa_bloklaydi() -> None:
    usage = PeriodUsage(tokens=10000, cost_uzs=Decimal("0.00"), messages=3)
    assert _is_exceeded(_limit(max_tokens=10000), usage) is True
