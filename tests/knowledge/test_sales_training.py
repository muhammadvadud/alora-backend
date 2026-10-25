from __future__ import annotations

import json
import stat
from copy import deepcopy
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command

from apps.catalog.models import Category, Fason, Product, ProductVariant
from apps.common.factories import AdminFactory
from apps.knowledge.models import KnowledgeRule
from apps.knowledge.services import (
    apply_sales_pack,
    load_sales_pack,
    managed_id,
    preview_sales_pack,
    rollback_sales_pack,
)
from apps.prompts.models import PromptVersion


@pytest.fixture()
def sales_environment(db: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setattr("apps.knowledge.services._notify_catalog", lambda: None)
    monkeypatch.setattr("apps.prompts.services.notify_prompt_updated", lambda **kwargs: None)
    author = AdminFactory()
    category = Category.objects.create(tenant=author.tenant, name="Portyera", slug="portyera")
    product = Product.objects.create(
        tenant=author.tenant,
        category=category,
        name="Office Minimal",
        code="OFFICE-MINIMAL",
        description="Avvalgi tavsif",
        recommended_rooms=["office"],
        tags={"owner_tag": True},
        composition="Yorliqda tasdiqlangan tarkib",
        care="Yorliqda tasdiqlangan parvarish",
    )
    variant = ProductVariant.objects.create(
        tenant=author.tenant,
        product=product,
        sku="TRAINING-TEST-OFFICE",
        color_name="Oq",
        price=Decimal(45000),
        price_unit="per_sqm",
        width_m=Decimal("2.8"),
    )
    return {"author": author, "product": product, "variant": variant}


def test_sales_pack_has_referenced_compact_local_knowledge() -> None:
    pack = load_sales_pack()
    assert len(pack["rules"]) >= 100
    assert len(pack["fasons"]) >= 8
    assert any("kelin-kuyov" in rule["recommendation"].lower() for rule in pack["rules"])
    assert any("pogon metr" in rule["recommendation"] for rule in pack["rules"])
    assert all(len(rule["recommendation"]) <= 420 for rule in pack["rules"])
    assert all(rule["sources"] for rule in pack["rules"])


@pytest.mark.parametrize(
    "problem", ["duplicate", "missing_source", "unsupported_condition", "long"]
)
def test_sales_pack_rejects_unsafe_or_unusable_data(tmp_path: Path, problem: str) -> None:
    pack = deepcopy(load_sales_pack())
    if problem == "duplicate":
        pack["rules"].append(pack["rules"][0])
    elif problem == "missing_source":
        pack["rules"][0]["sources"] = ["not-a-source"]
    elif problem == "unsupported_condition":
        pack["rules"][0]["condition"] = {"objection": "expensive"}
    else:
        pack["rules"][0]["recommendation"] = "a" * 421
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(pack), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_sales_pack(path)


def test_preview_does_not_change_database(sales_environment: dict[str, Any]) -> None:
    before = (KnowledgeRule.objects.count(), Fason.objects.count(), PromptVersion.objects.count())
    summary = preview_sales_pack(load_sales_pack())
    assert summary["product_descriptions"] == 1
    assert summary["rules"] >= 100
    assert (
        KnowledgeRule.objects.count(),
        Fason.objects.count(),
        PromptVersion.objects.count(),
    ) == before
    sales_environment["product"].refresh_from_db()
    assert sales_environment["product"].description == "Avvalgi tavsif"


def test_training_command_defaults_to_dry_run(sales_environment: dict[str, Any]) -> None:
    output = StringIO()
    call_command("train_sales", stdout=output)
    assert json.loads(output.getvalue())["dry_run"] is True
    assert not PromptVersion.objects.exists()


def test_apply_is_idempotent_and_keeps_prices_labels_and_owner_rules(
    sales_environment: dict[str, Any], tmp_path: Path
) -> None:
    pack = load_sales_pack()
    owner = KnowledgeRule.objects.create(
        kind="general", recommendation="Managerning yangi o'z qoidasi", priority=1
    )
    legacy = pack["retire_legacy"][0]
    old = KnowledgeRule.objects.create(**legacy, condition={}, priority=95)
    first = apply_sales_pack(
        pack, author=sales_environment["author"], snapshot_path=tmp_path / "one.json"
    )
    counts = (KnowledgeRule.objects.count(), Fason.objects.count(), PromptVersion.objects.count())
    second = apply_sales_pack(
        pack, author=sales_environment["author"], snapshot_path=tmp_path / "two.json"
    )
    assert first["prompt_version"] == second["prompt_version"]
    assert (
        KnowledgeRule.objects.count(),
        Fason.objects.count(),
        PromptVersion.objects.count(),
    ) == counts
    owner.refresh_from_db()
    old.refresh_from_db()
    assert owner.is_active and not old.is_active
    product = sales_environment["product"]
    product.refresh_from_db()
    assert product.tags["owner_tag"] is True
    assert "sodda parda" in product.tags["sales_aliases"]
    assert product.composition == "Yorliqda tasdiqlangan tarkib"
    assert product.care == "Yorliqda tasdiqlangan parvarish"
    sales_environment["variant"].refresh_from_db()
    assert sales_environment["variant"].price == Decimal(45000)
    assert stat.S_IMODE((tmp_path / "one.json").stat().st_mode) == 0o600


def test_rollback_restores_legacy_and_products_and_deactivates_new_templates(
    sales_environment: dict[str, Any], tmp_path: Path
) -> None:
    pack = load_sales_pack()
    legacy = pack["retire_legacy"][0]
    old = KnowledgeRule.objects.create(**legacy, condition={}, priority=95)
    prompt = PromptVersion.objects.create(
        version=1,
        content="Oldingi do'kon qoidasi",
        author=sales_environment["author"],
        is_current=True,
    )
    snapshot_path = tmp_path / "rollback.json"
    apply_sales_pack(pack, author=sales_environment["author"], snapshot_path=snapshot_path)
    rollback_sales_pack(snapshot_path, author=sales_environment["author"])
    old.refresh_from_db()
    assert old.is_active
    product = sales_environment["product"]
    product.refresh_from_db()
    assert product.description == "Avvalgi tavsif"
    assert product.recommended_rooms == ["office"]
    assert product.tags == {"owner_tag": True}
    assert PromptVersion.objects.get(is_current=True).content == prompt.content
    assert not Fason.objects.filter(
        pk__in=[
            managed_id("fason", f"{product.tenant_id}:{spec['key']}") for spec in pack["fasons"]
        ],
        is_active=True,
    ).exists()
    assert (
        not KnowledgeRule.objects.filter(pk=managed_id("rule", pack["rules"][0]["key"]))
        .get()
        .is_active
    )


def test_existing_snapshot_cannot_be_overwritten(
    sales_environment: dict[str, Any], tmp_path: Path
) -> None:
    path = tmp_path / "protected.json"
    path.write_text("old snapshot", encoding="utf-8")
    with pytest.raises(FileExistsError):
        apply_sales_pack(load_sales_pack(), author=sales_environment["author"], snapshot_path=path)
    assert path.read_text() == "old snapshot"
    assert not PromptVersion.objects.exists()


def test_list_tags_keep_their_shape_owner_values_and_rollback(
    sales_environment: dict[str, Any], tmp_path: Path
) -> None:
    product = sales_environment["product"]
    product.tags = ["owner_tag", "portyera"]
    product.save(update_fields=["tags"])
    path = tmp_path / "list-tags.json"
    apply_sales_pack(load_sales_pack(), author=sales_environment["author"], snapshot_path=path)
    product.refresh_from_db()
    assert isinstance(product.tags, list)
    assert product.tags[:2] == ["owner_tag", "portyera"]
    assert "sodda parda" in product.tags
    rollback_sales_pack(path, author=sales_environment["author"])
    product.refresh_from_db()
    assert product.tags == ["owner_tag", "portyera"]


def test_guidance_only_keeps_products_and_fasons(
    sales_environment: dict[str, Any], tmp_path: Path
) -> None:
    product = sales_environment["product"]
    before = (product.description, product.recommended_rooms, product.tags)
    out = StringIO()
    call_command(
        "train_sales",
        apply=True,
        guidance_only=True,
        author_id=str(sales_environment["author"].pk),
        snapshot=tmp_path / "guidance.json",
        stdout=out,
    )
    product.refresh_from_db()
    assert (product.description, product.recommended_rooms, product.tags) == before
    assert not Fason.objects.exists()
    assert KnowledgeRule.objects.filter(pk=managed_id("rule", "quote_service_integrity")).exists()
    assert PromptVersion.objects.filter(is_current=True).exists()
    summary = json.loads(out.getvalue())
    assert summary["product_descriptions"] == 0
    assert summary["fasons"] == 0
