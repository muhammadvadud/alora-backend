from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.chat.models import Conversation
from apps.chat.services import begin_chat_turn, build_agent_context
from apps.chat.tasks import save_message_and_usage
from apps.common.factories import EmployeeFactory, ManagerFactory
from apps.pricing.models import ModelPricing
from apps.usage.models import UsageDaily, UsageRecord
from apps.usage.services import calculate_cost, get_user_period_usage
from apps.usage.tasks import daily_usage_rollup, save_usage_record

pytestmark = pytest.mark.django_db


@pytest.fixture()
def conversation_factory(db):
    def create(**kwargs):
        user = kwargs.pop("user", None) or EmployeeFactory()
        kwargs.setdefault("tenant", user.tenant)
        return Conversation.objects.create(user=user, session_id=str(uuid4()), **kwargs)

    return create


@pytest.fixture()
def precise_rate():
    return ModelPricing.objects.create(
        provider="deepseek",
        model="cost-test",
        input_per_1m=Decimal("0.15"),
        output_per_1m=Decimal("0.60"),
        cached_input_per_1m=Decimal("0.003"),
        stt_per_minute=0,
        tts_per_1k_chars=0,
        usd_to_uzs=13000,
    )


def test_subcent_cost_and_cache_breakdown(precise_rate):
    usd, uzs = calculate_cost(
        "deepseek",
        "cost-test",
        prompt_tokens=1000,
        cached_tokens=800,
        completion_tokens=100,
        reasoning_tokens=60,
    )
    assert usd == Decimal("0.00009240")
    assert uzs == Decimal("1.20")
    assert precise_rate.cached_input_per_1m == Decimal("0.003")
    precise_rate.refresh_from_db()
    assert precise_rate.cached_input_per_1m == Decimal("0.003000")


def test_cached_count_is_bounded_by_total_input(precise_rate):
    usd, _ = calculate_cost("deepseek", "cost-test", prompt_tokens=100, cached_tokens=200)
    assert usd == Decimal("0.00000030")


def test_limits_and_daily_rollup_do_not_count_breakdown_twice(conversation_factory):
    conversation = conversation_factory()
    UsageRecord.objects.create(
        user=conversation.user,
        tenant_id=conversation.tenant_id,
        prompt_tokens=1000,
        completion_tokens=100,
        cached_tokens=800,
        reasoning_tokens=60,
    )
    assert get_user_period_usage(conversation.user, "daily").tokens == 1100
    daily_usage_rollup(date=str(timezone.localdate()))
    assert UsageDaily.objects.get(user=conversation.user).tokens == 1100


def test_two_channels_share_one_priced_record(precise_rate, conversation_factory):
    conversation = conversation_factory()
    turn = begin_chat_turn(conversation, "ha")
    context = build_agent_context(conversation, conversation.user, message_id=str(turn.pk))
    assert context["message_id"] == str(turn.pk)
    payload = {
        "user_id": str(conversation.user_id),
        "tenant_id": str(conversation.tenant_id),
        "conversation_id": str(conversation.pk),
        "message_id": str(turn.pk),
        "provider": "deepseek",
        "model": "cost-test",
        "prompt_tokens": 1000,
        "completion_tokens": 100,
        "cached_tokens": 800,
        "reasoning_tokens": 60,
        "tool_calls_json": "null",
    }
    first = save_usage_record(**payload)
    with patch("apps.chat.tasks.generate_conversation_title"):
        save_message_and_usage(
            conversation_id=str(conversation.pk),
            user_message_content="ha",
            ai_event_data={"usage": payload},
            tenant_id=str(conversation.tenant_id),
            message_id=str(turn.pk),
            user_id=str(conversation.user_id),
        )
    records = UsageRecord.objects.filter(message_id=turn.pk)
    assert records.count() == 1
    record = records.get()
    assert str(record.pk) == first
    assert record.cost_usd == Decimal("0.00009240")
    assert record.tool_calls == []
    assert conversation.messages.filter(role="user").count() == 1


def test_database_enforces_one_record_per_user_message(conversation_factory):
    conversation = conversation_factory()
    turn = begin_chat_turn(conversation, "ha")
    kwargs = {"user": conversation.user, "tenant_id": conversation.tenant_id, "message_id": turn.pk}
    UsageRecord.objects.create(**kwargs)
    with pytest.raises(IntegrityError), transaction.atomic():
        UsageRecord.objects.create(**kwargs)


def test_repeated_text_is_a_distinct_paid_turn(conversation_factory):
    conversation = conversation_factory()
    first = begin_chat_turn(conversation, "ha")
    second = begin_chat_turn(conversation, "ha")
    assert first.pk != second.pk


def test_manager_is_charged_for_own_request_not_conversation_owner(
    precise_rate, conversation_factory
):
    employee = EmployeeFactory()
    manager = ManagerFactory(tenant=employee.tenant)
    conversation = conversation_factory(user=employee, tenant=employee.tenant)
    turn = begin_chat_turn(conversation, "savol")
    with patch("apps.chat.tasks.generate_conversation_title"):
        save_message_and_usage(
            conversation_id=str(conversation.pk),
            user_message_content="savol",
            ai_event_data={
                "usage": {"provider": "deepseek", "model": "cost-test", "prompt_tokens": 1000}
            },
            tenant_id=str(employee.tenant_id),
            message_id=str(turn.pk),
            user_id=str(manager.pk),
        )
    assert UsageRecord.objects.get(message_id=turn.pk).user_id == manager.pk
