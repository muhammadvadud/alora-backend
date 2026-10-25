from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import Fason, FasonPart, Product
from apps.common.choices import CurtainPartRole
from apps.knowledge.models import KnowledgeRule
from apps.pricing.models import CalcRule
from apps.prompts.models import PromptVersion
from apps.prompts.services import create_prompt_version

DATA_DIR = Path(__file__).with_name("data")
PACK_PATH = DATA_DIR / "sales_v1.json"
PROMPT_PATH = DATA_DIR / "sales_prompt_v1.txt"
CONDITION_KEYS = {"room", "style", "pattern", "transparency", "light"}
RULE_FIELDS = ("kind", "condition", "recommendation", "priority", "is_active")
PRODUCT_FIELDS = ("description", "recommended_rooms", "tags")


def managed_id(entity: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"alora:sales-training:v1:{entity}:{key}")


def load_sales_pack(path: Path = PACK_PATH) -> dict[str, Any]:
    pack = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(pack, dict) or not isinstance(pack.get("version"), str):
        raise ValidationError("Bilim paketi obyekt va versiyaga ega bo'lishi kerak")
    sources = pack.get("sources", {})
    rules = pack.get("rules", [])
    if not isinstance(sources, dict) or not isinstance(rules, list) or not rules:
        raise ValidationError("Manbalar va bilim qoidalari kerak")
    kinds = set(KnowledgeRule.Kind.values)
    seen: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("key"), str):
            raise ValidationError("Har bilim qoidasi key bilan beriladi")
        if rule["key"] in seen:
            raise ValidationError(f"Takroriy bilim kaliti: {rule['key']}")
        seen.add(rule["key"])
        text = rule.get("recommendation", "")
        condition = rule.get("condition", {})
        priority = rule.get("priority")
        if rule.get("kind") not in kinds or not isinstance(text, str) or not 1 <= len(text) <= 420:
            raise ValidationError(f"Bilim turi yoki matni noto'g'ri: {rule['key']}")
        if not isinstance(priority, int) or isinstance(priority, bool) or not 0 <= priority <= 100:
            raise ValidationError(f"Bilim ustuvorligi noto'g'ri: {rule['key']}")
        if not isinstance(condition, dict) or set(condition) - CONDITION_KEYS:
            raise ValidationError(f"Go'da qo'llanmaydigan bilim sharti: {rule['key']}")
        for value in condition.values():
            if not isinstance(value, str) or not value:
                raise ValidationError(f"Bilim sharti bo'sh yoki noto'g'ri: {rule['key']}")
        refs = rule.get("sources", [])
        if not isinstance(refs, list) or not refs or any(ref not in sources for ref in refs):
            raise ValidationError(f"Bilim manbasi topilmadi: {rule['key']}")
    seen.clear()
    for fason in pack.get("fasons", []):
        key = fason.get("key")
        parts = fason.get("parts", [])
        if not isinstance(key, str) or key in seen or not 1 <= len(parts) <= 10:
            raise ValidationError("Fason kaliti yoki bo'laklar soni noto'g'ri")
        seen.add(key)
        for part in parts:
            if part.get("role") not in CurtainPartRole.values:
                raise ValidationError(f"Fason roli noto'g'ri: {key}")
            for field in ("width_share", "height_share"):
                try:
                    value = Decimal(part[field])
                except (KeyError, TypeError, InvalidOperation) as error:
                    raise ValidationError(f"Fason ulushi noto'g'ri: {key}") from error
                if not value.is_finite() or not Decimal(0) < value <= Decimal(1):
                    raise ValidationError(f"Fason ulushi chegaradan tashqari: {key}")
            if not isinstance(part.get("coefficient_rule"), str):
                raise ValidationError(f"Fason CalcRule kaliti kerak: {key}")
    seen.clear()
    for product in pack.get("product_enrichment", []):
        code = product.get("code")
        if not isinstance(code, str) or code in seen or not product.get("description"):
            raise ValidationError("Mahsulot kodi yoki tavsifi noto'g'ri")
        seen.add(code)
        if not isinstance(product.get("rooms"), list) or not isinstance(
            product.get("aliases"), list
        ):
            raise ValidationError(f"Mahsulot xona/atamalari noto'g'ri: {code}")
    return pack


def _target_products(pack: dict[str, Any]) -> list[Product]:
    codes = [spec["code"] for spec in pack.get("product_enrichment", [])]
    return list(Product.objects.filter(code__in=codes, is_active=True).order_by("pk"))


def _coefficient_values(pack: dict[str, Any]) -> dict[str, Decimal]:
    values = dict(CalcRule.objects.filter(is_active=True).values_list("key", "value"))
    needed = {
        part["coefficient_rule"] for fason in pack.get("fasons", []) for part in fason["parts"]
    }
    for key in needed:
        if key not in values:
            if "coef_default" not in values:
                raise ValidationError(f"Fason koeffitsienti bazada yo'q: {key}")
            values[key] = values["coef_default"]
    return values


def preview_sales_pack(pack: dict[str, Any]) -> dict[str, Any]:
    products = _target_products(pack)
    tenants = {str(product.tenant_id) for product in products}
    _coefficient_values(pack)
    ids = [managed_id("rule", rule["key"]) for rule in pack["rules"]]
    return {
        "version": pack["version"],
        "rules": len(ids),
        "existing_managed_rules": KnowledgeRule.objects.filter(pk__in=ids).count(),
        "product_descriptions": len(products),
        "tenants": sorted(tenants),
        "fasons": len(tenants) * len(pack.get("fasons", [])),
        "prompt_chars": len(PROMPT_PATH.read_text(encoding="utf-8")),
    }


def _legacy_rules(pack: dict[str, Any]) -> list[KnowledgeRule]:
    texts = [rule["recommendation"] for rule in pack.get("retire_legacy", [])]
    pairs = {(rule["kind"], rule["recommendation"]) for rule in pack.get("retire_legacy", [])}
    return [
        rule
        for rule in KnowledgeRule.objects.filter(recommendation__in=texts)
        if (rule.kind, rule.recommendation) in pairs
    ]


def _snapshot_before(pack: dict[str, Any], products: list[Product]) -> dict[str, Any]:
    ids = {managed_id("rule", rule["key"]) for rule in pack["rules"]}
    ids.update(rule.pk for rule in _legacy_rules(pack))
    existing = {
        str(rule.pk): {field: getattr(rule, field) for field in RULE_FIELDS}
        for rule in KnowledgeRule.objects.filter(pk__in=ids)
    }
    current = PromptVersion.objects.filter(is_current=True).first()
    tenants = {str(product.tenant_id) for product in products}
    fason_ids = [
        managed_id("fason", f"{tenant}:{fason['key']}")
        for tenant in sorted(tenants)
        for fason in pack.get("fasons", [])
    ]
    if Fason.objects.filter(pk__in=fason_ids).exists():
        existing_fasons = list(Fason.objects.filter(pk__in=fason_ids).values("id", "is_active"))
    else:
        existing_fasons = []
    return {
        "schema": "alora.sales-training.snapshot.v1",
        "pack_version": pack["version"],
        "rules": {str(rule_id): existing.get(str(rule_id)) for rule_id in sorted(ids)},
        "products": {
            str(product.pk): {field: getattr(product, field) for field in PRODUCT_FIELDS}
            for product in products
        },
        "fason_ids": [str(fason_id) for fason_id in fason_ids],
        "existing_fasons": existing_fasons,
        "previous_prompt_id": str(current.pk) if current else None,
    }


def _write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump(snapshot, output, ensure_ascii=False, indent=2, default=str)


def _notify_catalog() -> None:
    from apps.chat.grpc_server.catalog_service import publish_catalog_delta

    publish_catalog_delta(tenant_id="", entity="catalog", entity_id="", action="update")


def _apply_rules(pack: dict[str, Any]) -> None:
    legacy = _legacy_rules(pack)
    for rule in legacy:
        rule.is_active = False
    KnowledgeRule.objects.bulk_update(legacy, ["is_active"])
    for spec in pack["rules"]:
        values = {
            field: spec[field] for field in ("kind", "condition", "recommendation", "priority")
        }
        values["is_active"] = True
        rule_id = managed_id("rule", spec["key"])
        existing = KnowledgeRule.objects.filter(pk=rule_id).first()
        if existing is None:
            KnowledgeRule.objects.bulk_create([KnowledgeRule(id=rule_id, **values)])
        elif any(getattr(existing, field) != value for field, value in values.items()):
            KnowledgeRule.objects.filter(pk=rule_id).update(**values)


def _apply_products(pack: dict[str, Any], products: list[Product]) -> None:
    by_code = {spec["code"]: spec for spec in pack.get("product_enrichment", [])}
    changed: list[Product] = []
    for product in products:
        spec = by_code[product.code]
        tags: list[str] | dict[str, Any]
        if isinstance(product.tags, list):
            tags = list(dict.fromkeys([*product.tags, *spec["aliases"]]))
        else:
            tags = dict(product.tags or {})
            tags["sales_aliases"] = spec["aliases"]
            tags["sales_training_version"] = pack["version"]
        values = {
            "description": spec["description"],
            "recommended_rooms": spec["rooms"],
            "tags": tags,
        }
        if any(getattr(product, field) != value for field, value in values.items()):
            for field, value in values.items():
                setattr(product, field, value)
            changed.append(product)
    Product.objects.bulk_update(changed, list(PRODUCT_FIELDS))


def _apply_fasons(pack: dict[str, Any], products: list[Product]) -> None:
    coefficients = _coefficient_values(pack)
    tenant_ids = sorted({str(product.tenant_id) for product in products})
    for tenant_id in tenant_ids:
        for spec in pack.get("fasons", []):
            fason_id = managed_id("fason", f"{tenant_id}:{spec['key']}")
            values = {
                "tenant_id": tenant_id,
                "name": spec["name"],
                "style": spec["style"],
                "rooms": spec["rooms"],
                "part_count": len(spec["parts"]),
                "is_active": True,
            }
            if not Fason.objects.filter(pk=fason_id).exists():
                Fason.objects.bulk_create([Fason(id=fason_id, **values)])
            for index, part in enumerate(spec["parts"]):
                part_id = managed_id("fason-part", f"{fason_id}:{index}")
                part_values = {
                    "tenant_id": tenant_id,
                    "fason_id": fason_id,
                    "role": part["role"],
                    "name": part["name"],
                    "width_share": Decimal(part["width_share"]),
                    "height_share": Decimal(part["height_share"]),
                    "default_coef": coefficients[part["coefficient_rule"]],
                    "sort_order": index,
                }
                if not FasonPart.objects.filter(pk=part_id).exists():
                    FasonPart.objects.bulk_create([FasonPart(id=part_id, **part_values)])
            Fason.objects.filter(pk=fason_id).update(is_active=True)


def apply_sales_pack(pack: dict[str, Any], *, author: Any, snapshot_path: Path) -> dict[str, Any]:
    summary = preview_sales_pack(pack)
    with transaction.atomic():
        products = _target_products(pack)
        _write_snapshot(snapshot_path, _snapshot_before(pack, products))
        _apply_rules(pack)
        _apply_products(pack, products)
        _apply_fasons(pack, products)
        text = PROMPT_PATH.read_text(encoding="utf-8").strip()
        current = PromptVersion.objects.filter(is_current=True).first()
        if current is None or current.content != text:
            current = create_prompt_version(content=text, author=author)
        summary["prompt_version"] = current.version
        transaction.on_commit(_notify_catalog)
    return summary


def rollback_sales_pack(snapshot_path: Path, *, author: Any) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("schema") != "alora.sales-training.snapshot.v1":
        raise ValidationError("Qaytarish snapshot formati noto'g'ri")
    with transaction.atomic():
        for rule_id, previous in snapshot["rules"].items():
            if previous is None:
                KnowledgeRule.objects.filter(pk=rule_id).update(is_active=False)
            else:
                KnowledgeRule.objects.filter(pk=rule_id).update(**previous)
        for product_id, previous in snapshot["products"].items():
            Product.objects.filter(pk=product_id).update(**previous)
        Fason.objects.filter(pk__in=snapshot["fason_ids"]).update(is_active=False)
        for previous in snapshot["existing_fasons"]:
            Fason.objects.filter(pk=previous["id"]).update(is_active=previous["is_active"])
        previous_prompt_id = snapshot["previous_prompt_id"]
        if previous_prompt_id:
            previous_prompt = PromptVersion.objects.get(pk=previous_prompt_id)
            create_prompt_version(content=previous_prompt.content, author=author)
        else:
            PromptVersion.objects.filter(is_current=True).update(is_current=False)
        transaction.on_commit(_notify_catalog)
    return {"rolled_back": snapshot["pack_version"]}
