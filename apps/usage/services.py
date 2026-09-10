"""Usage ilovasi biznes-mantiqi — limit va xarajat hisobi."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.common.choices import OnExceed, UsagePeriod


class UsageLimitExceeded(APIException):
    """Limit tugaganda 429 bilan qaytadigan xato."""

    status_code = 429
    default_detail = "Foydalanish limiti tugadi"
    default_code = "usage_limit_exceeded"


@dataclass(frozen=True)
class PeriodUsage:
    """Davr uchun yig'ilgan foydalanish ko'rsatkichlari."""

    tokens: int = 0
    cost_uzs: Decimal = Decimal(0)
    messages: int = 0


@dataclass(frozen=True)
class LimitCheckResult:
    """Limitni tekshirish natijasi."""

    blocked: bool
    period: str
    limit: Any | None = None
    usage: PeriodUsage | None = None
    reason: str = ""


def period_start(period: str, now: dt.datetime | None = None) -> dt.datetime:
    """Berilgan davr (daily|monthly) uchun boshlanish vaqtini qaytaradi."""

    current = now or timezone.now()
    if period == UsagePeriod.MONTHLY:
        return current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return current.replace(hour=0, minute=0, second=0, microsecond=0)


def resolve_usage_limit(user: Any) -> Any | None:
    """Xodim uchun amaldagi limitni ustuvorlik bo'yicha qaytaradi.

    Ustuvorlik: shaxsiy limit > rol limiti > limit yo'q (cheksiz).
    Shaxsiy limit mavjud bo'lsa — rol limiti e'tiborga olinmaydi.
    """


    UsageLimit = _usage_limit_model()
    if UsageLimit is None:
        return None

    personal = (
        UsageLimit.objects.filter(
            user__pk=user.pk,
            is_active=True,
            user__isnull=False,
            role__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )
    if personal is not None:
        return personal

    return (
        UsageLimit.objects.filter(
            user__isnull=True,
            role=getattr(user, "role", None),
            is_active=True,
        )
        .order_by("-created_at")
        .first()
    )


def get_user_period_usage(user: Any, period: str) -> PeriodUsage:
    """Berilgan davr uchun xodimning joriy foydalanishini hisoblaydi.

    Limit tekshiruvi real vaqtda bo'lishi uchun xom jadvaldan o'qiladi.
    Statistikada esa `UsageDaily` rollup'idan foydalaniladi (qarang: selectors).
    """

    UsageRecord = _usage_record_model()
    if UsageRecord is None:
        return PeriodUsage()

    start = period_start(period)
    aggregate = UsageRecord.objects.filter(
        user__pk=user.pk,
        created_at__gte=start,
    ).aggregate(
        total_tokens=Sum("prompt_tokens") + Sum("completion_tokens") + Sum("cached_tokens") + Sum("reasoning_tokens"),
        total_cost=Sum("cost_uzs"),
    )
    messages = UsageRecord.objects.filter(user__pk=user.pk, created_at__gte=start).count()

    total_tokens = aggregate.get("total_tokens") or 0
    total_cost = aggregate.get("total_cost") or Decimal(0)
    if not isinstance(total_cost, Decimal):
        total_cost = Decimal(str(total_cost))
    return PeriodUsage(tokens=int(total_tokens), cost_uzs=total_cost, messages=messages)


def check_usage_limit(user: Any) -> LimitCheckResult:
    """Foydalanuvchi limitini tekshiradi va natijani qaytaradi.

    `is_unlimited=True` bo'lsa cheklov umuman qo'llanmaydi. Limitni oshiruvchi
    holatda `on_exceed=block` bo'lsa `blocked=True` qaytadi.
    """

    from django.db import transaction

    with transaction.atomic():
        # Poyga holati (race condition) ni oldini olish uchun bazada qulflaymiz
        user.__class__.objects.select_for_update().get(pk=user.pk)

        limit = resolve_usage_limit(user)
        period = limit.period if limit is not None else UsagePeriod.DAILY
        usage = get_user_period_usage(user, period)

        if limit is None or limit.is_unlimited:
            return LimitCheckResult(blocked=False, period=period, limit=limit, usage=usage)

        exceeded = _is_exceeded(limit, usage)
        if not exceeded or limit.on_exceed != OnExceed.BLOCK:
            return LimitCheckResult(blocked=False, period=period, limit=limit, usage=usage)

        return LimitCheckResult(
            blocked=True,
            period=period,
            limit=limit,
            usage=usage,
            reason=_resolve_exceed_reason(limit, usage),
        )


def enforce_usage_limit(user: Any) -> None:
    """Limit bloklashni talab qilsa 429 xatoni ko'taradi.

    Chat gateway bu funksiyani chaqiradi; tugagan limit bo'lsa foydalanuvchi
    tushunarli 429 xato oladi.
    """

    result = check_usage_limit(user)
    if result.blocked:
        raise UsageLimitExceeded(result.reason)


def set_user_usage_limit(user: Any, fields: dict[str, Any]) -> Any:
    """Xodim uchun shaxsiy limitni yaratadi yoki yangilaydi.

    `{"is_unlimited": true}` berilganda cheksiz rejim yoqiladi, boshqa
    cheklov maydonlari qoldiriladi. Amaldagi shaxsiy limit bitta bo'ladi
    (yangi yozuv ustiga yoziladi, tarix saqlanmaydi).
    """

    UsageLimit = _usage_limit_model()
    if UsageLimit is None:
        raise UsageLimitExceeded("Limit modeli mavjud emas")

    limit, _ = UsageLimit.objects.get_or_create(
        user=user,
        role=None,
        defaults={"period": UsagePeriod.DAILY, "is_active": True},
    )

    for field, value in fields.items():
        if field in {"is_unlimited", "period", "max_tokens", "max_cost_uzs", "max_messages", "on_exceed", "is_active"}:
            setattr(limit, field, value)
    limit.save()
    return limit


def calculate_cost(
    provider: str,
    model: str,
    *,
    prompt_tokens: int,
    completion_tokens: int = 0,
    cached_tokens: int = 0,
    reasoning_tokens: int = 0,
    stt_seconds: int = 0,
    tts_chars: int = 0,
) -> tuple[Decimal, Decimal]:
    """ModelPricing bo'yicha USD va UZS dagi xarajatni hisoblaydi.

    Narx yo'q bo'lsa — nol qaytadi. Barcha hisob `Decimal` da, yaxlitlash
    oxirida 2 kasr aniqligida bajariladi.
    """

    pricing = _model_pricing(provider, model)
    if pricing is None:
        return Decimal(0), Decimal(0)

    million = Decimal(1_000_000)
    usd = Decimal(0)
    usd += _decimal(pricing.input_per_1m) * Decimal(prompt_tokens) / million
    usd += _decimal(pricing.output_per_1m) * Decimal(completion_tokens) / million
    usd += _decimal(pricing.cached_input_per_1m) * Decimal(cached_tokens) / million
    usd += _decimal(pricing.output_per_1m) * Decimal(reasoning_tokens) / million
    usd += _decimal(pricing.stt_per_minute) * Decimal(stt_seconds) / Decimal(60)
    usd += _decimal(pricing.tts_per_1k_chars) * Decimal(tts_chars) / Decimal(1000)

    usd = usd.quantize(Decimal("0.01"))
    cost_uzs = (usd * _decimal(pricing.usd_to_uzs)).quantize(Decimal("0.01"))
    return usd, cost_uzs


def _is_exceeded(limit: Any, usage: PeriodUsage) -> bool:
    """Limit qiymatlarini joriy foydalanish bilan solishtiradi."""

    if limit.max_tokens is not None and usage.tokens >= limit.max_tokens:
        return True
    if limit.max_cost_uzs is not None and usage.cost_uzs >= _decimal(limit.max_cost_uzs):
        return True
    return bool(limit.max_messages is not None and usage.messages >= limit.max_messages)


def _resolve_exceed_reason(limit: Any, usage: PeriodUsage) -> str:
    """Limit oshganining sababini o'zbekcha tavsiflaydi."""

    if limit.max_tokens is not None and usage.tokens >= limit.max_tokens:
        return f"Tokenlar limiti tugadi ({usage.tokens}/{limit.max_tokens})"
    if limit.max_cost_uzs is not None and usage.cost_uzs >= _decimal(limit.max_cost_uzs):
        return f"Xarajat limiti tugadi ({usage.cost_uzs}/{limit.max_cost_uzs})"
    if limit.max_messages is not None and usage.messages >= limit.max_messages:
        return f"Xabarlar limiti tugadi ({usage.messages}/{limit.max_messages})"
    return "Foydalanish limiti tugadi"


def _decimal(value: Any) -> Decimal:
    """Qiymatni Decimal ga, kerak bo'lsa aylantiradi."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _usage_record_model() -> Any:
    """UsageRecord modelini izza vaqtda qaytaradi."""

    from django.apps import apps

    try:
        return apps.get_model("usage", "UsageRecord")
    except LookupError:
        return None


def _usage_limit_model() -> Any:
    """UsageLimit modelini izza vaqtda qaytaradi."""

    from django.apps import apps

    try:
        return apps.get_model("usage", "UsageLimit")
    except LookupError:
        return None


def _model_pricing(provider: str, model: str) -> Any | None:
    """ModelPricing yozuvini (provider, model) bo'yicha qaytaradi."""

    from django.apps import apps

    try:
        ModelPricing = apps.get_model("pricing", "ModelPricing")
    except LookupError:
        return None
    return ModelPricing.objects.filter(provider=provider, model=model, is_active=True).order_by("-created_at").first()