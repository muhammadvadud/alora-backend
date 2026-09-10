from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Any

from django.core.exceptions import ValidationError

from apps.catalog.models import ProductVariant
from apps.common.choices import PriceUnit, UserRole
from apps.pricing.models import CalcRule, DiscountPolicy, DiscountTier, OrderDefaults, ServicePrice

ZERO = Decimal(0)
ONE = Decimal(1)


@dataclass(slots=True)
class PricingSnapshot:
    """Hisob uchun kerakli barcha ma'lumotlar."""

    calc_rules: dict[str, CalcRule]
    service_prices: dict[str, ServicePrice]
    discount_tiers: list[DiscountTier]
    discount_policy: DiscountPolicy
    order_defaults: OrderDefaults


def _to_decimal(value: Any) -> Decimal:
    """Har qanday sonli qiymatni Decimal ga aylantiradi."""

    if isinstance(value, Decimal):
        return value
    if value is None:
        return ZERO
    return Decimal(str(value))


def _round_to_step(value: Decimal, step: Decimal) -> Decimal:
    """Qiymatni berilgan qadamga yaxlitlaydi."""

    if step <= ZERO:
        return value
    quotient = (value / step).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return quotient * step


def _quantize_money(value: Decimal) -> Decimal:
    """Pul qiymatini 2 kasrga keltiradi."""

    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _load_singleton(model: type[Any]) -> Any:
    """Singleton modelning birinchi yozuvini qaytaradi."""

    instance = model.objects.order_by("created_at").first()
    if instance is None:
        raise ValidationError({model.__name__.lower(): "Sozlama topilmadi"})
    return instance


def load_pricing_snapshot() -> PricingSnapshot:
    """Hisoblash uchun kerakli qoidalarni bazadan yuklaydi."""

    calc_rules = {rule.key: rule for rule in CalcRule.objects.all()}
    service_prices = {
        service.key: service for service in ServicePrice.objects.filter(is_active=True)
    }
    discount_tiers = list(
        DiscountTier.objects.filter(is_active=True).order_by("min_amount", "percent")
    )
    discount_policy = _load_singleton(DiscountPolicy)
    order_defaults = _load_singleton(OrderDefaults)
    return PricingSnapshot(
        calc_rules=calc_rules,
        service_prices=service_prices,
        discount_tiers=discount_tiers,
        discount_policy=discount_policy,
        order_defaults=order_defaults,
    )


def _rule_value(snapshot: PricingSnapshot, key: str) -> Decimal:
    """CalcRule qiymatini oladi."""

    rule = snapshot.calc_rules.get(key)
    if rule is None:
        raise ValidationError({"rules": f"'{key}' hisob qoidasi topilmadi"})
    return _to_decimal(rule.value)


def _resolve_discount_policy(snapshot: PricingSnapshot, user_role: str | None) -> Decimal:
    """Rolga qarab qo'lda chegirma limitini qaytaradi."""

    if user_role == UserRole.EMPLOYEE:
        return _to_decimal(snapshot.discount_policy.manual_max_percent_employee)
    return _to_decimal(snapshot.discount_policy.manual_max_percent_manager)


def _match_tier(snapshot: PricingSnapshot, subtotal: Decimal) -> Decimal:
    """Subtotal uchun eng yuqori mos chegirma bosqichini topadi."""

    matched = ZERO
    for tier in snapshot.discount_tiers:
        min_amount = _to_decimal(tier.min_amount)
        percent = _to_decimal(tier.percent)
        if subtotal >= min_amount and percent >= matched:
            matched = percent
    return matched


def _variant_by_id(variant_id: Any) -> ProductVariant:
    """Variantni UUID bo'yicha topadi."""

    try:
        return ProductVariant.objects.select_related("product").get(id=variant_id)
    except ProductVariant.DoesNotExist as exc:
        raise ValidationError({"variant_id": "Variant topilmadi"}) from exc


def _measurement_length(measurement: Mapping[str, Any]) -> Decimal:
    """O'lchov uzunligini oladi."""

    return _to_decimal(measurement.get("length"))


def _measurement_height(measurement: Mapping[str, Any]) -> Decimal:
    """O'lchov balandligini oladi."""

    return _to_decimal(measurement.get("height"))


def _part_height(part: Mapping[str, Any], measurement: Mapping[str, Any]) -> Decimal:
    """Bo'lak balandligini aniqlaydi."""

    value = part.get("height_m")
    return _to_decimal(value if value is not None else _measurement_height(measurement))


def _part_width(part: Mapping[str, Any], measurement: Mapping[str, Any]) -> Decimal:
    """Bo'lak kengligini aniqlaydi."""

    value = part.get("width_m")
    return _to_decimal(value if value is not None else _measurement_length(measurement))


def _part_coef(part: Mapping[str, Any], snapshot: PricingSnapshot) -> Decimal:
    """Bo'lak koeffitsientini aniqlaydi."""

    value = part.get("coef")
    if value is None:
        return _rule_value(snapshot, "coef_default")
    return _to_decimal(value)


def _part_visible_area(width: Decimal, height: Decimal, coef: Decimal) -> Decimal:
    """Bo'lakning ko'rinadigan yuzasini hisoblaydi."""

    return width * coef * height


def _part_raw_area(
    width: Decimal,
    height: Decimal,
    coef: Decimal,
    seam_allowance: Decimal,
    hem_allowance: Decimal,
) -> Decimal:
    """Bo'lakning qo'shimchalar bilan xom yuzasini hisoblaydi."""

    return width * coef * (height + seam_allowance + hem_allowance)


def _variant_line_total(variant: ProductVariant, quantity: Decimal) -> Decimal:
    """Variant narxini uning birligiga qarab hisoblaydi."""

    price = _to_decimal(variant.price)
    if variant.price_unit == PriceUnit.PER_SQM:
        return _quantize_money(quantity * price)
    if variant.price_unit == PriceUnit.PER_METER:
        return _quantize_money(quantity * price)
    if variant.price_unit == PriceUnit.PER_PIECE:
        return _quantize_money(quantity * price)
    return _quantize_money(quantity * price)


def _accessory_line_total(variant: ProductVariant, qty: Decimal) -> Decimal:
    """Aksessuar narxini hisoblaydi."""

    return _variant_line_total(variant, qty)


def _service_quantity(
    *,
    service: ServicePrice,
    snapshot: PricingSnapshot,
    total_area: Decimal,
    total_length: Decimal,
    part_count: int,
) -> Decimal:
    """Xizmat miqdorini uning birligiga va kalitiga qarab hisoblaydi."""

    if service.key == "hook":
        step = _rule_value(snapshot, "hook_step")
        if step <= ZERO:
            return ZERO
        return Decimal(total_length / step).to_integral_value(rounding=ROUND_CEILING)
    if service.unit == PriceUnit.PER_SQM:
        return total_area
    if service.unit == PriceUnit.PER_METER:
        return total_length
    if service.unit == PriceUnit.PER_PIECE:
        return Decimal(part_count)
    return Decimal(part_count)


def _build_measurement_preview(
    measurement: Mapping[str, Any],
    snapshot: PricingSnapshot,
) -> dict[str, Any]:
    """Bitta o'lchov bo'yicha hisob natijasini quradi."""

    seam_allowance = _rule_value(snapshot, "seam_allowance")
    hem_allowance = _rule_value(snapshot, "hem_allowance")
    area_step = _rule_value(snapshot, "round_area_to")
    parts_payload: list[dict[str, Any]] = []
    total_raw_area = ZERO
    total_area = ZERO

    for part in measurement.get("parts", []):
        variant = _variant_by_id(part["variant_id"])
        part_width = _part_width(part, measurement)
        part_height = _part_height(part, measurement)
        part_coef = _part_coef(part, snapshot)
        visible_area = _part_visible_area(part_width, part_height, part_coef)
        raw_area = _part_raw_area(part_width, part_height, part_coef, seam_allowance, hem_allowance)
        rounded_area = _round_to_step(raw_area, area_step)
        waste_area = raw_area - visible_area
        waste_percent = ZERO
        if visible_area > ZERO:
            waste_percent = (waste_area / visible_area) * Decimal(100)
        line_total = _variant_line_total(variant, rounded_area)
        parts_payload.append(
            {
                "variant_id": str(variant.id),
                "sku": variant.sku,
                "role": part.get("role"),
                "width_m": str(part_width),
                "height_m": str(part_height),
                "coef": str(part_coef),
                "visible_area_m2": str(visible_area),
                "raw_area_m2": str(raw_area),
                "area_m2": str(rounded_area),
                "waste_area_m2": str(waste_area),
                "waste_percent": str(
                    waste_percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ),
                "price_unit": variant.price_unit,
                "unit_price": str(variant.price),
                "line_total": str(line_total),
            }
        )
        total_raw_area += raw_area
        total_area += rounded_area

    accessories_payload: list[dict[str, Any]] = []
    total_accessory = ZERO
    for accessory in measurement.get("accessories", []):
        variant = _variant_by_id(accessory["variant_id"])
        qty = _to_decimal(accessory.get("qty"))
        line_total = _accessory_line_total(variant, qty)
        accessories_payload.append(
            {
                "variant_id": str(variant.id),
                "sku": variant.sku,
                "qty": str(qty),
                "price_unit": variant.price_unit,
                "unit_price": str(variant.price),
                "line_total": str(line_total),
            }
        )
        total_accessory += line_total

    return {
        "length": str(_measurement_length(measurement)),
        "height": str(_measurement_height(measurement)),
        "parts": parts_payload,
        "accessories": accessories_payload,
        "raw_area_m2": str(total_raw_area),
        "area_m2": str(total_area),
        "accessories_total": str(_quantize_money(total_accessory)),
    }


def _build_service_lines(
    measurement_payloads: Sequence[Mapping[str, Any]],
    snapshot: PricingSnapshot,
    requested_services: Sequence[str],
    delivery: bool,
) -> tuple[list[dict[str, Any]], Decimal, Decimal]:
    """Xizmat qatorlarini quradi va umumiy summani qaytaradi."""

    total_area = ZERO
    total_length = ZERO
    total_parts = 0
    for measurement in measurement_payloads:
        total_length += _measurement_length(measurement)
        total_parts += len(measurement.get("parts", []))
        for part in measurement.get("parts", []):
            part_width = _part_width(part, measurement)
            part_height = _part_height(part, measurement)
            part_coef = _part_coef(part, snapshot)
            raw_area = _part_raw_area(
                part_width,
                part_height,
                part_coef,
                _rule_value(snapshot, "seam_allowance"),
                _rule_value(snapshot, "hem_allowance"),
            )
            total_area += _round_to_step(raw_area, _rule_value(snapshot, "round_area_to"))

    service_lines: list[dict[str, Any]] = []
    total_service_sum = ZERO
    delivery_amount = ZERO

    for service_key in requested_services:
        service = snapshot.service_prices.get(service_key)
        if service is None:
            raise ValidationError({"services": f"'{service_key}' xizmati topilmadi"})
        qty = _service_quantity(
            service=service,
            snapshot=snapshot,
            total_area=total_area,
            total_length=total_length,
            part_count=total_parts,
        )
        line_total = _quantize_money(qty * _to_decimal(service.price))
        service_lines.append(
            {
                "key": service.key,
                "name": service.name,
                "qty": str(qty),
                "price_unit": service.unit,
                "unit_price": str(service.price),
                "line_total": str(line_total),
                "is_delivery": False,
            }
        )
        total_service_sum += line_total

    if delivery:
        delivery_service = snapshot.service_prices.get("delivery")
        if delivery_service is not None:
            delivery_amount = _quantize_money(_to_decimal(delivery_service.price))
            service_lines.append(
                {
                    "key": delivery_service.key,
                    "name": delivery_service.name,
                    "qty": str(ONE),
                    "price_unit": delivery_service.unit,
                    "unit_price": str(delivery_service.price),
                    "line_total": str(delivery_amount),
                    "is_delivery": True,
                }
            )
        else:
            delivery_amount = _quantize_money(_to_decimal(snapshot.order_defaults.delivery_amount))
            service_lines.append(
                {
                    "key": "delivery",
                    "name": "Yetkazish",
                    "qty": str(ONE),
                    "price_unit": PriceUnit.PER_PIECE,
                    "unit_price": str(delivery_amount),
                    "line_total": str(delivery_amount),
                    "is_delivery": True,
                }
            )

    return service_lines, total_service_sum, delivery_amount


def _normalize_measurements(payload: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    """O'lchovlar ro'yxatini xavfsiz qaytaradi."""

    measurement_payloads = payload.get("measurements", [])
    if not isinstance(measurement_payloads, Sequence) or isinstance(
        measurement_payloads, (str, bytes)
    ):
        raise ValidationError({"measurements": "O'lchovlar ro'yxat bo'lishi kerak"})
    return measurement_payloads


def _normalize_services(payload: Mapping[str, Any]) -> Sequence[str]:
    """Xizmatlar ro'yxatini qaytaradi."""

    services = payload.get("services", [])
    if not isinstance(services, Sequence) or isinstance(services, (str, bytes)):
        raise ValidationError({"services": "Xizmatlar ro'yxat bo'lishi kerak"})
    return [str(service) for service in services]


def calculate_preview(
    payload: Mapping[str, Any],
    *,
    user_role: str | None = None,
) -> dict[str, Any]:
    """Preview kalkulyatsiyasini bajaradi."""

    snapshot = load_pricing_snapshot()
    measurement_payloads = _normalize_measurements(payload)
    requested_services = _normalize_services(payload)
    measurement_previews = [
        _build_measurement_preview(measurement, snapshot) for measurement in measurement_payloads
    ]
    service_lines, service_sum, delivery_amount = _build_service_lines(
        measurement_payloads,
        snapshot,
        requested_services,
        bool(payload.get("delivery", False)),
    )

    parts_sum = ZERO
    accessories_sum = ZERO
    for measurement in measurement_previews:
        for part in measurement["parts"]:
            parts_sum += _to_decimal(part["line_total"])
        accessories_sum += _to_decimal(measurement["accessories_total"])

    subtotal = _quantize_money(parts_sum + accessories_sum + service_sum)
    tier_discount = _match_tier(snapshot, subtotal)
    manual_requested = _to_decimal(payload.get("discount_percent", ZERO))
    manual_max = _resolve_discount_policy(snapshot, user_role)
    manual_applied = min(manual_requested, manual_max)
    if snapshot.discount_policy.stack_with_tier:
        applied_discount_percent = tier_discount + manual_applied
    else:
        applied_discount_percent = max(tier_discount, manual_applied)

    discount_amount = _quantize_money(subtotal * applied_discount_percent / Decimal(100))
    total_before_rounding = subtotal - discount_amount + delivery_amount
    min_order_amount = _rule_value(snapshot, "min_order_amount")
    total_before_rounding = max(total_before_rounding, min_order_amount)
    total = _quantize_money(
        _round_to_step(total_before_rounding, _rule_value(snapshot, "round_total_to"))
    )

    warnings: list[str] = []
    waste_warn_percent = _rule_value(snapshot, "waste_warn_percent")
    for measurement in measurement_previews:
        for part in measurement["parts"]:
            waste_percent = _to_decimal(part["waste_percent"])
            if waste_percent > waste_warn_percent:
                warnings.append(f"{part['sku']} uchun chiqindi {waste_percent}% dan oshdi")

    return {
        "measurements": measurement_previews,
        "services": service_lines,
        "subtotal": str(subtotal),
        "tier_discount_percent": str(tier_discount),
        "manual_discount_percent": str(manual_applied),
        "discount_percent": str(applied_discount_percent),
        "discount_amount": str(discount_amount),
        "delivery_amount": str(_quantize_money(delivery_amount)),
        "total": str(total),
        "warnings": warnings,
    }
