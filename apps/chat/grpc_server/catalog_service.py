"""Catalog servisi — Django → Go katalog sinxronizatsiyasi.

Catalog.Snapshot: to'liq katalog nusxasini sahifalab beradi.
Catalog.Watch: Redis pub/sub kanalidan delta o'qib Go'ga uzatadi.
"""

from __future__ import annotations

import json
from typing import Any

import grpc
import redis
import structlog
from django.conf import settings
from google.protobuf.json_format import ParseDict

from apps.chat.grpc_server import catalog_payload as payloads
from grpc_gen import alora_pb2_grpc

logger = structlog.get_logger(__name__)

# Redis pub/sub kanali nomi
CATALOG_DELTA_CHANNEL = "alora:catalog:deltas"
CATALOG_VERSION_KEY = "alora:catalog:version"


def get_catalog_version() -> int:
    """Redis'dan joriy katalog versiya raqamini oladi."""
    r = redis.from_url(settings.REDIS_URL)
    version = r.get(CATALOG_VERSION_KEY)
    return int(version) if version else 0


def increment_catalog_version(r: redis.Redis | None = None) -> int:
    """Katalog versiya raqamini bittaga oshiradi va qaytaradi."""
    client = r or redis.from_url(settings.REDIS_URL)
    return int(client.incr(CATALOG_VERSION_KEY))


def publish_catalog_delta(
    tenant_id: str,
    entity: str,
    entity_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
) -> int:
    """Catalog delta'sini Redis pub/sub kanaliga e'lon qiladi.

    Args:
        tenant_id: Tenant UUID si.
        entity: O'zgarayotgan subyekt turi (product, variant, ...).
        entity_id: Yozuv UUID si.
        action: Amal turi (create, update, delete).
        payload: Yangilangan ma'lumot (JSON serializable).

    Returns:
        Yangi versiya raqami.
    """
    r = redis.from_url(settings.REDIS_URL)
    version = increment_catalog_version(r)

    delta = {
        "tenant_id": tenant_id,
        "entity": entity,
        "entity_id": entity_id,
        "action": action,
        "version": version,
        "payload_json": json.dumps(payload or {}, ensure_ascii=False),
    }

    r.publish(CATALOG_DELTA_CHANNEL, json.dumps(delta, ensure_ascii=False))

    logger.info(
        "Catalog delta e'lon qilindi",
        version=version,
        entity=entity,
        action=action,
    )

    return version


class CatalogServicer(alora_pb2_grpc.CatalogServicer):
    """Catalog gRPC servisining amalga oshirilishi.

    Kontrakt 1.1: pricing (service_prices, discount_tiers, discount_policy,
    order_defaults), fasons va prompt faqat BIRINCHI sahifada (page_token bo'sh)
    to'ldiriladi — ular kichik va sahifalanmaydi; Go ularni birinchi sahifadan oladi.
    """

    PAGE_SIZE_DEFAULT = 100
    PAGE_SIZE_MAX = 1000

    def Snapshot(self, request: Any, context: grpc.ServicerContext) -> Any:  # type: ignore[no-untyped-def]
        """Go agent Catalog.Snapshot chaqirganda — katalog sahifasini qaytaradi."""
        from grpc_gen import alora_pb2

        page_size = request.page_size or self.PAGE_SIZE_DEFAULT
        if page_size > self.PAGE_SIZE_MAX:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"page_size {self.PAGE_SIZE_MAX} dan oshmasligi kerak",
            )

        return self._build_snapshot(
            page_token=request.page_token,
            page_size=page_size,
            pb2=alora_pb2,
        )

    def Watch(self, request: Any, context: grpc.ServicerContext) -> Any:  # type: ignore[no-untyped-def]
        """Go agent Watch stream ochganda — Redis pub/sub dan delta uzatadi."""
        from grpc_gen import alora_pb2

        try:
            yield from self._iter_deltas(
                from_version=request.from_version,
                tenant_id=request.tenant_id,
                pb2=alora_pb2,
            )
        except grpc.RpcError:
            # Klient stream'ni yopdi — normal holat
            return

    # ── Snapshot ───────────────────────────────────────────────────────────

    def _build_snapshot(
        self,
        page_token: str,
        page_size: int,
        pb2: Any,
    ) -> Any:
        """Katalogning bitta sahifasini quradi."""
        version = get_catalog_version()
        offset = int(page_token) if page_token.isdigit() else 0
        is_first_page = offset == 0

        total_count = self._products_count()
        has_next = offset + page_size < total_count
        next_page_token = str(offset + page_size) if has_next else ""

        snapshot: dict[str, Any] = {
            "version": version,
            "products": self._products_page(offset, page_size),
            "categories": self._categories() if is_first_page else [],
            "calc_rules": self._calc_rules() if is_first_page else [],
            "knowledge_rules": self._knowledge_rules() if is_first_page else [],
            "next_page_token": next_page_token,
            "total_count": total_count,
        }
        if is_first_page:
            snapshot.update(self._pricing_block())
            snapshot["fasons"] = self._fasons()
            prompt = self._prompt()
            if prompt is not None:
                snapshot["prompt"] = prompt

        return ParseDict(snapshot, pb2.CatalogSnapshot(), ignore_unknown_fields=True)

    def _products_count(self) -> int:
        """Faol mahsulotlar soni."""
        from apps.catalog.models import Product

        return Product.objects.filter(is_active=True).count()

    def _products_page(self, offset: int, page_size: int) -> list[dict[str, Any]]:
        """Mahsulotlar sahifasi (variantlar va rasmlar bilan)."""
        from apps.catalog.models import Product

        products_qs = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("variants", "images")
            .order_by("sort_order", "name")
        )
        return [payloads.product_payload(p) for p in products_qs[offset : offset + page_size]]

    def _categories(self) -> list[dict[str, Any]]:
        from apps.catalog.models import Category

        qs = Category.objects.filter(is_active=True).order_by("sort_order")
        return [payloads.category_payload(c) for c in qs]

    def _calc_rules(self) -> list[dict[str, Any]]:
        from apps.pricing.models import CalcRule

        return [payloads.calc_rule_payload(r) for r in CalcRule.objects.filter(is_active=True)]

    def _knowledge_rules(self) -> list[dict[str, Any]]:
        from apps.knowledge.models import KnowledgeRule

        qs = KnowledgeRule.objects.filter(is_active=True).order_by("-priority")
        return [payloads.knowledge_rule_payload(r) for r in qs]

    def _pricing_block(self) -> dict[str, Any]:
        """Xizmat narxlari, chegirma bosqichlari, siyosat va buyurtma defaultlari."""
        from apps.pricing.models import DiscountPolicy, DiscountTier, OrderDefaults, ServicePrice

        block: dict[str, Any] = {
            "service_prices": [
                payloads.service_price_payload(s)
                for s in ServicePrice.objects.filter(is_active=True).order_by("key")
            ],
            "discount_tiers": [
                payloads.discount_tier_payload(t)
                for t in DiscountTier.objects.filter(is_active=True).order_by(
                    "min_amount", "percent"
                )
            ],
        }
        policy = DiscountPolicy.objects.order_by("created_at").first()
        if policy is not None:
            block["discount_policy"] = payloads.discount_policy_payload(policy)
        defaults = OrderDefaults.objects.order_by("created_at").first()
        if defaults is not None:
            block["order_defaults"] = payloads.order_defaults_payload(defaults)
        return block

    def _fasons(self) -> list[dict[str, Any]]:
        from apps.catalog.models import Fason

        qs = (
            Fason.objects.filter(is_active=True)
            .prefetch_related("parts", "accessories")
            .order_by("name")
        )
        return [payloads.fason_payload(f) for f in qs]

    def _prompt(self) -> dict[str, Any] | None:
        from apps.prompts.models import PromptVersion

        current = PromptVersion.objects.filter(is_current=True).first()
        return payloads.prompt_payload(current) if current is not None else None

    # ── Watch ──────────────────────────────────────────────────────────────

    def _iter_deltas(self, from_version: int, tenant_id: str, pb2: Any) -> Any:
        """Redis pub/sub dan delta'larni o'qib uzatadi.

        `from_version` joriy versiyadan orqada bo'lsa oraliq delta'lar Redis'da
        saqlanmagani uchun FULL_RESYNC yuboriladi va stream yopiladi — Go Snapshot
        olib, yangi versiya bilan Watch'ni qayta ochadi.
        """
        current_version = get_catalog_version()
        if from_version < current_version:
            yield pb2.CatalogDelta(
                version=current_version,
                entity="catalog",
                entity_id="",
                action="FULL_RESYNC",
                tenant_id=tenant_id,
                payload_json="",
            )
            return

        r = redis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        pubsub.subscribe(CATALOG_DELTA_CHANNEL)

        try:
            for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                data = json.loads(message["data"])

                if data["version"] <= from_version:
                    continue

                # Global obyektlar (pricing, prompt, knowledge) tenant'siz keladi —
                # ular har qanday tenant filtrida o'tadi.
                if tenant_id and data["tenant_id"] and data["tenant_id"] != tenant_id:
                    continue

                logger.info(
                    "Catalog delta yuborildi",
                    version=data["version"],
                    entity=data["entity"],
                    action=data["action"],
                )

                yield pb2.CatalogDelta(
                    version=data["version"],
                    entity=data["entity"],
                    entity_id=data["entity_id"],
                    action=data["action"],
                    tenant_id=data["tenant_id"],
                    payload_json=data.get("payload_json", ""),
                )
        finally:
            pubsub.unsubscribe()
            pubsub.close()
