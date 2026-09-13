"""Katalog obyektlarini proto-JSON dict'ga aylantirish — Snapshot va Delta uchun YAGONA manba.

Nega dict: `Catalog.Snapshot` bu dict'ni `ParseDict` bilan pb xabariga aylantiradi,
`publish_catalog_delta` esa xuddi shu dict'ni `payload_json` qilib yuboradi. Ikkala yo'l
bir xil maydon nomlari (snake_case, proto JSON) bilan ketadi — Go tarafida bitta mapping.

Pul, o'lcham va foizlar **string** (decimal matn) ko'rinishida — Django `Decimal` bilan
bit-bit moslik uchun (`CatalogVariant.price` kabi eski `double` maydonlar shartnoma
qoidasi bo'yicha o'zgartirilmaydi).
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any


def _dec(value: Any, default: str = "0") -> str:
    """Decimal qiymatni matnga aylantiradi (None → default)."""
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return str(value)
    return str(Decimal(str(value)))


def _float(value: Any) -> float:
    """Eski `double` maydonlar uchun (shartnoma o'zgarmaydi)."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _file_url(field: Any) -> str:
    """FileField/ImageField'dan URL oladi; fayl bo'lmasa bo'sh."""
    if not field:
        return ""
    try:
        return field.url
    except ValueError:
        return str(field)


# ── Katalog ────────────────────────────────────────────────────────────────


def variant_payload(variant: Any) -> dict[str, Any]:
    return {
        "id": str(variant.id),
        "product_id": str(variant.product_id),
        "sku": variant.sku,
        "color_name": variant.color_name or "",
        "color_hex": variant.color_hex or "",
        "width_m": _float(variant.width_m),
        "price": _float(variant.price),
        "price_unit": variant.price_unit,
        "old_price": _float(variant.old_price),
        "is_active": bool(variant.is_active),
    }


def product_payload(product: Any, *, include_variants: bool = True) -> dict[str, Any]:
    variants = (
        [variant_payload(v) for v in product.variants.all() if v.is_active]
        if include_variants
        else []
    )
    images = [_file_url(i.image) for i in product.images.all()[:5]]
    return {
        "id": str(product.id),
        "category_id": str(product.category_id) if product.category_id else "",
        "name": product.name,
        "code": product.code or "",
        "description": product.description or "",
        "fabric_type": product.fabric_type or "",
        "pattern": product.pattern or "",
        "style": product.style or "",
        "transparency": product.transparency or "",
        "density": _float(product.density),
        "composition": product.composition or "",
        "care": product.care or "",
        "recommended_rooms": list(product.recommended_rooms or []),
        "recommended_coef": _float(product.recommended_coef),
        "default_width_m": _float(product.default_width_m),
        "is_sewing_required": bool(product.is_sewing_required),
        "segment": product.segment or "",
        "tags_json": json.dumps(product.tags or {}, ensure_ascii=False),
        "variants": variants,
        "image_urls": images,
    }


def category_payload(category: Any) -> dict[str, Any]:
    return {
        "id": str(category.id),
        "name": category.name,
        "slug": category.slug,
        "parent_id": str(category.parent_id) if category.parent_id else "",
        "sort_order": int(category.sort_order or 0),
    }


def fason_payload(fason: Any) -> dict[str, Any]:
    return {
        "id": str(fason.id),
        "name": fason.name,
        "style": fason.style or "",
        "rooms": list(fason.rooms or []),
        "image_url": _file_url(fason.image),
        "part_count": int(fason.part_count or 0),
        "parts": [
            {
                "id": str(p.id),
                "role": p.role,
                "name": p.name,
                "width_share": _dec(p.width_share, "1"),
                "height_share": _dec(p.height_share, "1"),
                "default_coef": _dec(p.default_coef, "2"),
                "sort_order": int(p.sort_order or 0),
            }
            for p in fason.parts.all().order_by("sort_order", "id")
        ],
        "accessories": [
            {
                "id": str(a.id),
                "category": a.category,
                "default_qty": _dec(a.default_qty, "1"),
                "qty_formula": a.qty_formula or "",
            }
            for a in fason.accessories.all().order_by("id")
        ],
    }


# ── Pricing ────────────────────────────────────────────────────────────────


def calc_rule_payload(rule: Any) -> dict[str, Any]:
    return {
        "key": rule.key,
        "value": _float(rule.value),
        "unit": rule.unit,
        "description": rule.description or "",
        "applies_to_json": json.dumps(rule.applies_to or {}, ensure_ascii=False),
    }


def service_price_payload(service: Any) -> dict[str, Any]:
    return {
        "key": service.key,
        "name": service.name,
        "price": _dec(service.price),
        "unit": service.unit,
        "is_active": bool(service.is_active),
    }


def discount_tier_payload(tier: Any) -> dict[str, Any]:
    return {
        "id": str(tier.id),
        "min_amount": _dec(tier.min_amount),
        "percent": _dec(tier.percent),
        "is_active": bool(tier.is_active),
    }


def discount_policy_payload(policy: Any) -> dict[str, Any]:
    return {
        "manual_max_percent_employee": _dec(policy.manual_max_percent_employee),
        "manual_max_percent_manager": _dec(policy.manual_max_percent_manager),
        "stack_with_tier": bool(policy.stack_with_tier),
    }


def order_defaults_payload(defaults: Any) -> dict[str, Any]:
    return {
        "prepayment_percent": _dec(defaults.prepayment_percent),
        "delivery_amount": _dec(defaults.delivery_amount),
        "deadline_days": int(defaults.deadline_days or 0),
    }


# ── Bilimlar va prompt ─────────────────────────────────────────────────────


def knowledge_rule_payload(rule: Any) -> dict[str, Any]:
    return {
        "id": str(rule.id),
        "kind": rule.kind,
        "condition_json": json.dumps(rule.condition or {}, ensure_ascii=False),
        "recommendation": rule.recommendation,
        "priority": int(rule.priority or 0),
    }


def prompt_payload(prompt: Any) -> dict[str, Any]:
    return {
        "version": int(prompt.version),
        "content": prompt.content,
        "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else "",
    }
