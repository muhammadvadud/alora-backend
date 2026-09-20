"""orders ilovasi biznes-mantiqlari."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.common.choices import OrderStatus, PaymentStatus, PriceUnit
from apps.orders.models import (
    DiscountSource,
    Order,
    OrderAccessory,
    OrderCurtainPart,
    OrderItem,
    OrderMeasurement,
)
from apps.pricing.services.calculator import calculate_preview, load_pricing_snapshot

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:  # pragma: no cover - lokal fallback
    import logging

    logger = logging.getLogger(__name__)


ZERO = Decimal(0)


def _to_decimal(value: Any) -> Decimal:
    """Sonli qiymatni Decimal ga aylantiradi."""

    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        return ZERO
    return Decimal(str(value))


def _quantize_money(value: Decimal) -> Decimal:
    """Pul qiymatini 2 kasrga keltiradi."""

    return value.quantize(Decimal("0.01"))


def generate_order_number(order: Order) -> str:
    """Buyurtma raqamini yaratadi: ALR-2026-000123.

    Raqam suffix'i DB darajasidagi `orders_order_number_seq` sequence'idan
    olinadi (race-free) va hech qachon tiklanmaydi.
    """

    return f"ALR-{order.created_at.year}-{order.number_seq:06d}"


def _assign_order_number(order: Order) -> None:
    """Yangi buyurtmaga raqam va `number_seq` qiymatini yozadi."""

    order.save()
    order.refresh_from_db(fields=["number_seq", "created_at"])
    order.number = generate_order_number(order)
    order.save(update_fields=["number", "updated_at"])


ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.DRAFT: frozenset({OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.MEASURING, OrderStatus.CANCELLED}),
    OrderStatus.MEASURING: frozenset({OrderStatus.PRODUCTION, OrderStatus.CANCELLED}),
    OrderStatus.PRODUCTION: frozenset({OrderStatus.READY, OrderStatus.CANCELLED}),
    OrderStatus.READY: frozenset({OrderStatus.INSTALLING, OrderStatus.CANCELLED}),
    OrderStatus.INSTALLING: frozenset({OrderStatus.COMPLETED, OrderStatus.CANCELLED}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


def get_status_graph() -> list[dict[str, Any]]:
    """Status ro'yxati va har biri uchun ruxsat etilgan o'tishlarni qaytaradi."""

    return [
        {
            "value": value,
            "label": label,
            "allowed": sorted(ALLOWED_TRANSITIONS.get(value, frozenset())),
        }
        for value, label in OrderStatus.choices
    ]


def validate_transition(current: str, target: str | None) -> None:
    """Status o'tishi ruxsat etilganini tekshiradi."""

    from django.core.exceptions import ValidationError

    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValidationError(
            {"status": f"'{current}' holatdan '{target}' holatga o'tish ruxsat etilmagan"}
        )


def confirm_order(*, order: Order, user: Any) -> Order:
    """Buyurtmani tasdiqlaydi: draft -> confirmed, confirmed_by/at to'ldiradi."""

    from django.core.exceptions import ValidationError

    if order.status != OrderStatus.DRAFT:
        raise ValidationError({"status": "Faqat draft holatidagi buyurtma tasdiqlanishi mumkin"})
    change_order_status(order=order, target=OrderStatus.CONFIRMED, user=user)
    logger.info(
        "order_confirmed", order_id=str(order.pk), number=order.number, user_id=str(user.pk)
    )
    return order


def change_order_status(
    *,
    order: Order,
    target: str,
    user: Any | None = None,
    note: str = "",
    action_date: date | None = None,
) -> Order:
    """Buyurtma statusini ruxsat etilgan o'tish bo'yicha o'zgartiradi.

    Qulf (select_for_update) sababi: Ikki parallel so'rov bir vaqtda
    statusni o'zgartirishga urinsa, poyga holati (race condition) orqali
    noto'g'ri (masalan, bekor qilingan buyurtma ishlab chiqarishga o'tishi)
    holatlarning oldini olish uchun qulflanadi.
    """

    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        validate_transition(locked.status, target)
        old_status = locked.status
        change_fields = ["status"]
        locked.status = target

        if target == OrderStatus.CONFIRMED:
            locked.confirmed_by = user
            locked.confirmed_at = timezone.now()
            change_fields += ["confirmed_by", "confirmed_at"]

        if action_date is not None:
            locked.deadline_date = action_date
            change_fields.append("deadline_date")

        if note:
            locked.note = note.strip()
            change_fields.append("note")

        locked.save(update_fields=change_fields)

    order.refresh_from_db()
    logger.info(
        "order_status_changed",
        order_id=str(order.pk),
        number=order.number,
        old_status=old_status,
        new_status=target,
    )
    return order


def _measurement_to_calc_payload(
    measurement_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Bitta o'lchovni kalkulyator so'rov formatiga o'giradi."""

    parts: list[dict[str, Any]] = []
    for part in measurement_payload.get("parts", []):
        parts.append(
            {
                "variant_id": part["variant_id"],
                "role": part.get("role"),
                "width_m": part.get("width_m"),
                "height_m": part.get("height_m"),
                "coef": part.get("coefficient", part.get("coef")),
            }
        )

    accessories: list[dict[str, Any]] = []
    for accessory in measurement_payload.get("accessories", []):
        accessories.append({"variant_id": accessory["variant_id"], "qty": accessory.get("qty")})

    return {
        "length": measurement_payload.get("cornice_length_m"),
        "height": measurement_payload.get("height_m"),
        "parts": parts,
        "accessories": accessories,
    }


def _order_to_calc_payload(order: Order) -> dict[str, Any]:
    """Buyurtma ichidagi o'lchov/xizmatlarni kalkulyator formatiga o'giradi."""

    measurements: list[dict[str, Any]] = []
    services: list[str] = []
    delivery = False
    for measurement in order.measurements.all():
        payload = {
            "length": measurement.cornice_length_m,
            "height": measurement.height_m,
            "parts": [],
            "accessories": [],
        }
        for part in measurement.parts.all():
            payload["parts"].append(
                {
                    "variant_id": part.variant_id,
                    "role": part.role,
                    "width_m": part.width_m,
                    "height_m": part.height_m,
                    "coef": part.coefficient,
                }
            )
        for accessory in measurement.accessories.all():
            payload["accessories"].append(
                {"variant_id": accessory.variant_id, "qty": accessory.qty}
            )
        measurements.append(payload)

    for item in order.items.all():
        if item.service_key == "delivery":
            delivery = True
        else:
            services.append(item.service_key)

    discount_percent = ZERO
    if order.discount_source == DiscountSource.MANUAL:
        discount_percent = _to_decimal(order.discount_percent)

    return {
        "measurements": measurements,
        "services": services,
        "delivery": delivery,
        "discount_percent": discount_percent,
    }


def _apply_prepayment(
    order: Order,
    *,
    total: Decimal,
    prepayment_percent: Decimal | None,
) -> None:
    """Avans, qoldiq va to'lov holatini buyurtma summasi asosida hisoblaydi."""

    defaults = load_pricing_snapshot().order_defaults
    percent = (
        prepayment_percent
        if prepayment_percent is not None
        else _to_decimal(defaults.prepayment_percent)
    )
    prepayment = _quantize_money(total * percent / Decimal(100))
    balance = _quantize_money(total - prepayment)

    order.prepayment_percent = percent
    order.prepayment = prepayment
    order.balance = balance
    if prepayment <= ZERO:
        order.payment_status = PaymentStatus.UNPAID
    elif balance <= ZERO:
        order.payment_status = PaymentStatus.PAID
    else:
        order.payment_status = PaymentStatus.PREPAID


def _apply_calc_result(
    order: Order,
    result: Mapping[str, Any],
    prepayment_percent: Decimal | None,
) -> None:
    """Kalkulyator natijasini buyurtma summasi maydonlariga yozadi."""

    subtotal = _to_decimal(result["subtotal"])
    discount_percent = _to_decimal(result["discount_percent"])
    discount_amount = _to_decimal(result["discount_amount"])
    delivery_amount = _to_decimal(result["delivery_amount"])
    total = _to_decimal(result["total"])

    order.subtotal = _quantize_money(subtotal)
    order.discount_percent = discount_percent
    order.discount_amount = _quantize_money(discount_amount)
    order.delivery_amount = _quantize_money(delivery_amount)
    order.total = _quantize_money(total)
    _apply_prepayment(order, total=total, prepayment_percent=prepayment_percent)


def create_order_from_draft(
    *,
    payload: Mapping[str, Any],
    user: Any,
    conversation_id: Any = None,
) -> tuple[Order, dict[str, Any]]:
    """AI draft'idan buyurtma yaratadi va kalkulyator orqali hisoblaydi.

    Narx va nomlar (snapshot) buyurtma yaratilgan paytdagi qiymatlari bilan
    saqlanadi — katalog keyin o'zgarsa buyurtma o'zgarmaydi (TZ 3.6).
    """

    calc_payload = {
        "measurements": [_measurement_to_calc_payload(m) for m in payload.get("measurements", [])],
        "services": [str(s) for s in payload.get("services", [])],
        "delivery": bool(payload.get("delivery", False)),
        "discount_percent": _to_decimal(payload.get("discount_percent", ZERO)),
    }
    result = calculate_preview(calc_payload, user_role=getattr(user, "role", None))

    with transaction.atomic():
        order = Order(
            tenant=user.tenant,
            user=user,
            conversation_id=conversation_id,
            customer_name=payload["customer_name"],
            customer_phone=payload["customer_phone"],
            address=payload.get("address", ""),
            status=OrderStatus.DRAFT,
            deadline_date=payload.get("deadline_date"),
            discount_source=(
                DiscountSource.MANUAL
                if _to_decimal(payload.get("discount_percent", ZERO)) > ZERO
                else DiscountSource.TIER
            ),
        )
        _assign_order_number(order)

        _build_measurements(order, payload, result)

        order_items = []
        for service_line in result["services"]:
            order_items.append(
                OrderItem(
                    order=order,
                    service_key=service_line["key"],
                    name_snapshot=service_line["name"],
                    qty=_to_decimal(service_line["qty"]),
                    unit=service_line.get("price_unit") or PriceUnit.PER_PIECE,
                    unit_price=_to_decimal(service_line["unit_price"]),
                    total=_to_decimal(service_line["line_total"]),
                )
            )
        if order_items:
            OrderItem.objects.bulk_create(order_items)

        defaults = load_pricing_snapshot().order_defaults
        if order.deadline_date is None:
            order.deadline_date = timezone.localdate() + timedelta(days=int(defaults.deadline_days))
        order.note = payload.get("note", "")
        _apply_calc_result(
            order,
            result,
            prepayment_percent=_to_decimal(payload.get("prepayment_percent", ZERO))
            if payload.get("prepayment_percent") is not None
            else None,
        )
        order.save(
            update_fields=[
                "deadline_date",
                "note",
                "subtotal",
                "discount_percent",
                "discount_amount",
                "delivery_amount",
                "total",
                "prepayment_percent",
                "prepayment",
                "balance",
                "payment_status",
                "updated_at",
            ]
        )

    logger.info(
        "order_created",
        order_id=str(order.pk),
        number=order.number,
        user_id=str(user.pk),
        total=str(order.total),
    )
    return order, result


def _build_measurements(
    order: Order, payload: Mapping[str, Any], result: Mapping[str, Any]
) -> None:
    """O'lchov, parda bo'laklari va aksessuarlarni snapshot narxlar bilan yaratadi."""

    result_measurements = list(result["measurements"])
    if not payload.get("measurements"):
        return

    for index, measurement_payload in enumerate(payload["measurements"]):
        parts_payload = measurement_payload.get("parts", [])
        coefficient = measurement_payload.get("coefficient")
        if coefficient is None and parts_payload:
            coefficient = parts_payload[0].get("coefficient") or parts_payload[0].get("coef")
        if coefficient is None:
            coefficient = load_pricing_snapshot().calc_rules["coef_default"].value
        measurement = OrderMeasurement.objects.create(
            order=order,
            room_name=measurement_payload.get("room_name", f"Xona {index + 1}"),
            cornice_length_m=measurement_payload.get("cornice_length_m"),
            height_m=measurement_payload.get("height_m"),
            layers=measurement_payload.get("layers", []),
            coefficient=coefficient,
            note=measurement_payload.get("note", ""),
        )

        result_measurement = result_measurements[index] if index < len(result_measurements) else {}
        result_parts = result_measurement.get("parts", [])
        for part_index, part_payload in enumerate(parts_payload):
            result_part = result_parts[part_index] if part_index < len(result_parts) else {}
            OrderCurtainPart.objects.create(
                measurement=measurement,
                variant_id=part_payload["variant_id"],
                role=part_payload.get("role", ""),
                width_m=part_payload.get("width_m"),
                height_m=part_payload.get("height_m"),
                coefficient=part_payload.get("coefficient") or part_payload.get("coef"),
                area_sqm=_resolve_part_area(result_part, part_payload),
                price_per_sqm=result_part.get("unit_price"),
                total=result_part.get("line_total"),
                sort_order=part_index,
            )

        accessories_payload = measurement_payload.get("accessories", [])
        result_accessories = result_measurement.get("accessories", [])
        for accessory_index, accessory_payload in enumerate(accessories_payload):
            result_accessory = (
                result_accessories[accessory_index]
                if accessory_index < len(result_accessories)
                else {}
            )
            OrderAccessory.objects.create(
                measurement=measurement,
                variant_id=accessory_payload["variant_id"],
                qty=accessory_payload.get("qty"),
                unit=result_accessory.get("price_unit") or PriceUnit.PER_PIECE,
                unit_price=result_accessory.get("unit_price"),
                total=result_accessory.get("line_total"),
                sort_order=accessory_index,
            )


def _resolve_part_area(result_part: Mapping[str, Any], part_payload: Mapping[str, Any]) -> Decimal:
    """Bo'lak yuzasini mos 3 kasr bilan qaytaradi.

    Kalkulyator natijasidagi `area_m2` asosiy manba. U yo'q bo'lgan chekka
    holatda — xavfsiz fallback sifatida ko'rinadigan yuza geometriyasi
    hisoblanadi (kenglik x koeffitsient x balandlik). Kenglik emas!
    """

    area = result_part.get("area_m2")
    if area is not None:
        return _to_decimal(area).quantize(Decimal("0.001"))
    width = _to_decimal(part_payload.get("width_m"))
    height = _to_decimal(part_payload.get("height_m"))
    coefficient = part_payload.get("coefficient") or part_payload.get("coef")
    if coefficient is None:
        coefficient = Decimal(load_pricing_snapshot().calc_rules["coef_default"].value)
    return (width * _to_decimal(coefficient) * height).quantize(Decimal("0.001"))


def _rebuild_service_items(order: Order, result: Mapping[str, Any]) -> None:
    """Kalkulyator natijasiga mos xizmat qatorlarini qayta yozadi.

    `OrderItem`'lar (tikuv, o'rnatish, yetkazish, ...) snapshot holatidagi
    xizmatlar uchun yaratiladi. O'lchov yoki xizmat o'zgarganda eski kiritma
    o'chirilib, yangi natija bo'yicha qayta yoziladi.
    """

    order.items.all().delete()
    order_items = [
        OrderItem(
            order=order,
            service_key=service_line["key"],
            name_snapshot=service_line["name"],
            qty=_to_decimal(service_line["qty"]),
            unit=service_line.get("price_unit") or PriceUnit.PER_PIECE,
            unit_price=_to_decimal(service_line["unit_price"]),
            total=_to_decimal(service_line["line_total"]),
        )
        for service_line in result["services"]
    ]
    if order_items:
        OrderItem.objects.bulk_create(order_items)


def _current_service_keys(order: Order) -> list[str]:
    """Buyurtmadagi xizmat kalitlarini (yetkazishdan tashqari) qaytaradi."""

    return [item.service_key for item in order.items.all() if item.service_key != "delivery"]


def _current_has_delivery(order: Order) -> bool:
    """Buyurtmada yetkazish xizmati bor-yo'qligini qaytaradi."""

    return order.items.filter(service_key="delivery").exists()


def update_order_from_draft(
    *,
    order: Order,
    payload: Mapping[str, Any],
    user_role: str | None = None,
) -> tuple[Order, dict[str, Any] | None]:
    """Buyurtma ma'lumotlarini yangilaydi (8.11 PATCH).

    O'lchov, xizmat, yetkazish, chegirma yoki avans berilgan bo'lsa — summa
    `apps/pricing/services/calculator.py` orqali qayta hisoblanadi.
    """

    with transaction.atomic():
        header_fields = ["updated_at"]
        if "customer_name" in payload:
            order.customer_name = str(payload["customer_name"]).strip()
            header_fields.append("customer_name")
        if "customer_phone" in payload:
            order.customer_phone = str(payload["customer_phone"]).strip()
            header_fields.append("customer_phone")
        if "address" in payload:
            order.address = str(payload["address"])
            header_fields.append("address")
        if "note" in payload:
            order.note = str(payload["note"]).strip()
            header_fields.append("note")
        if "deadline_date" in payload:
            order.deadline_date = payload["deadline_date"]
            header_fields.append("deadline_date")
        if "conversation_id" in payload:
            order.conversation_id = payload["conversation_id"]
            header_fields.append("conversation_id")

        recalc_keys = (
            "measurements",
            "services",
            "delivery",
            "discount_percent",
            "prepayment_percent",
        )
        needs_recalc = any(key in payload for key in recalc_keys)
        result: dict[str, Any] | None = None

        if needs_recalc:
            calc_payload = _order_to_calc_payload(order)
            if "measurements" in payload:
                calc_payload["measurements"] = [
                    _measurement_to_calc_payload(measurement_payload)
                    for measurement_payload in payload["measurements"]
                ]
            if "services" in payload:
                calc_payload["services"] = [str(service) for service in payload["services"]]
            if "delivery" in payload:
                calc_payload["delivery"] = bool(payload["delivery"])
            if "discount_percent" in payload:
                calc_payload["discount_percent"] = _to_decimal(payload["discount_percent"])
                order.discount_source = (
                    DiscountSource.MANUAL
                    if _to_decimal(payload["discount_percent"]) > ZERO
                    else DiscountSource.TIER
                )

            result = calculate_preview(calc_payload, user_role=user_role)

            if "measurements" in payload:
                order.measurements.all().delete()
                _build_measurements(order, payload, result)

            _rebuild_service_items(order, result)

            prepayment = payload.get("prepayment_percent")
            _apply_calc_result(
                order,
                result,
                prepayment_percent=_to_decimal(prepayment) if prepayment is not None else None,
            )
            if payload.get("payment_status") == PaymentStatus.PAID:
                order.payment_status = PaymentStatus.PAID
                order.prepayment_percent = Decimal("100")
                order.prepayment = order.total
                order.balance = ZERO
            order.save(
                update_fields=[
                    *header_fields,
                    "discount_source",
                    "subtotal",
                    "discount_percent",
                    "discount_amount",
                    "delivery_amount",
                    "total",
                    "prepayment_percent",
                    "prepayment",
                    "balance",
                    "payment_status",
                ]
            )
        else:
            if "payment_status" in payload:
                if payload["payment_status"] != PaymentStatus.PAID:
                    raise ValueError("Faqat to'liq to'langan holatga o'tkazish qo'llab-quvvatlanadi")
                order.payment_status = PaymentStatus.PAID
                order.prepayment_percent = Decimal("100")
                order.prepayment = order.total
                order.balance = ZERO
                header_fields.extend(["payment_status", "prepayment_percent", "prepayment", "balance"])
            order.save(update_fields=header_fields)

    logger.info(
        "order_updated",
        order_id=str(order.pk),
        number=order.number,
        recalculated=needs_recalc,
    )
    return order, result


def recalculate_order(*, order: Order, user_role: str | None = None) -> dict[str, Any]:
    """Buyurtma summasini apps/pricing/services/calculator.py orqali qayta hisoblaydi.

    Qulf (select_for_update) sababi: Bir vaqtda bir nechta o'zgarish
    buyurtmani qayta hisoblaganda poyga holatini (race condition) oldini olish.
    """

    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        payload = _order_to_calc_payload(locked)
        result = calculate_preview(payload, user_role=user_role)

        _apply_calc_result(locked, result, prepayment_percent=None)
        locked.save(
            update_fields=[
                "subtotal",
                "discount_percent",
                "discount_amount",
                "delivery_amount",
                "total",
                "prepayment",
                "balance",
                "payment_status",
                "updated_at",
            ]
        )

    order.refresh_from_db()
    logger.info(
        "order_recalculated",
        order_id=str(order.pk),
        number=order.number,
        total=str(order.total),
    )
    return result


def _summarize_order_lines(order: Order) -> Decimal:
    """Buyurtma qatorlaridagi snapshot summalarini yig'adi."""

    total = ZERO
    for measurement in order.measurements.all():
        total += Decimal(sum((part.total or ZERO) for part in measurement.parts.all()))
        total += Decimal(
            sum((accessory.total or ZERO) for accessory in measurement.accessories.all())
        )
    total += Decimal(sum((item.total or ZERO) for item in order.items.all()))
    return _quantize_money(total)


def order_lines_total(order: Order) -> Decimal:
    """Buyurtma qatorlari (bo'lak + aksessuar + xizmat) umumiy summasini qaytaradi."""

    return _summarize_order_lines(order)


def sync_order_from_calc_result(order: Order, result: Mapping[str, Any]) -> None:
    """Kalkulyator natijasini buyurtma jami bilan sinxron qiladi (yordamchi)."""

    _apply_calc_result(order, result, prepayment_percent=None)
    order.save(
        update_fields=[
            "subtotal",
            "discount_percent",
            "discount_amount",
            "delivery_amount",
            "total",
            "prepayment",
            "balance",
            "payment_status",
            "updated_at",
        ]
    )
