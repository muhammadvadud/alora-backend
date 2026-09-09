"""Bosqich 13 — Celery tasklari uchun umumiy fixture'lar."""

from __future__ import annotations

import uuid

import pytest

from apps.common.factories import EmployeeFactory, TenantFactory


@pytest.fixture()
def tenant(db):
    """Bazaga saqlangan tenant."""
    return TenantFactory()


@pytest.fixture()
def employee(tenant):
    """Bazaga saqlangan xodim."""
    return EmployeeFactory(tenant=tenant)


@pytest.fixture()
def conversation(employee):
    """Bo'sh sarlavhali, bazaga saqlangan suhbat."""
    from apps.chat.models import Conversation

    return Conversation.objects.create(
        tenant=employee.tenant,
        user=employee,
        session_id=str(uuid.uuid4()),
        title="",
    )