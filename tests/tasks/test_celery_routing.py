"""Celery navbatlari uchun compose iste'molchilarini tekshirish."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT_DIR / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose_text():
    """Compose faylining matnini qaytaradi."""
    return COMPOSE_FILE.read_text(encoding="utf-8")


def test_task_routes_have_compose_consumers(compose_text):
    """Routing dagi har bir navbat kamida bitta worker tomonidan iste'mol qilinadi."""
    celery_text = (ROOT_DIR / "config" / "celery.py").read_text(encoding="utf-8")
    routed_queues = set(re.findall(r"queue['\"]:\s*['\"]([^'\"]+)", celery_text))

    for queue in routed_queues:
        assert re.search(rf"-Q\s+[^\n#]*\b{re.escape(queue)}\b", compose_text), (
            f"{queue!r} navbati uchun compose consumer topilmadi"
        )
