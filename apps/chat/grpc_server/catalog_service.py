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


class CatalogServicer:
    """Catalog gRPC servisining amalga oshirilishi.

    Asl bazaviy klass generatsiya kodida mavjud (alora_pb2_grpc.CatalogServicer).
    Bu klass unga parallel — shartnoma Go jamoasi bilan kelishilgandan keyin
    generatsiya qilingan bazaviy klassdan meros olish uchun qo'shiladi.
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
            for delta in self._iter_deltas(
                from_version=request.from_version,
                tenant_id=request.tenant_id,
                pb2=alora_pb2,
            ):
                yield delta
        except grpc.RpcError:
            # Klient stream'ni yopdi — normal holat
            return

    def _build_snapshot(  # noqa: C901 — bo'limlar ketma-ket quriladi
        self,
        page_token: str,
        page_size: int,
        pb2: Any,
    ) -> Any:
        """Katalogning bitta sahifasini quradi."""
        version = get_catalog_version()
        offset = int(page_token) if page_token.isdigit() else 0

        products_pb = self._products_page(offset, page_size, pb2)
        total_count = self._products_count()
        categories_pb = self._categories(pb2)
        calc_rules_pb = self._calc_rules(pb2)
        knowledge_rules_pb = self._knowledge_rules(pb2)

        has_next = offset + page_size < total_count
        next_page_token = str(offset + page_size) if has_next else ""

        return pb2.CatalogSnapshot(
            version=version,
            products=products_pb,
            categories=categories_pb,
            calc_rules=calc_rules_pb,
            knowledge_rules=knowledge_rules_pb,
            next_page_token=next_page_token,
            total_count=total_count,
        )

    def _products_count(self) -> int:
        """Faol mahsulotlar soni."""
        from apps.catalog.models import Product

        return Product.objects.filter(is_active=True).count()

    def _products_page(  # noqa: C901 — mahsulot va variantlarni yig'ish
        self,
        offset: int,
        page_size: int,
        pb2: Any,
    ) -> list[Any]:
        """Mahsulotlar sahifasini quradi (variantlar va rasmlar bilan)."""
        from apps.catalog.models import Product

        products_qs = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("variants")
            .order_by("sort_order", "name")
        )

        products_page = products_qs[offset : offset + page_size]
        result: list[Any] = []

        for product in products_page:
            variants_pb = [
                pb2.CatalogVariant(
                    id=str(v.id),
                    product_id=str(product.id),
                    sku=v.sku,
                    color_name=v.color_name,
                    color_hex=v.color_hex,
                    width_m=float(v.width_m),
                    price=float(v.price),
                    price_unit=v.price_unit,
                    old_price=float(v.old_price) if v.old_price else 0.0,
                    is_active=v.is_active,
                )
                for v in product.variants.all()
                if v.is_active
            ]

            try:
                density: float = float(product.density) if product.density else 0.0
            except ValueError:
                density = 0.0

            images = [str(i.image) for i in product.images.all()[:5]]

            result.append(
                pb2.CatalogProduct(
                    id=str(product.id),
                    category_id=str(product.category_id),
                    name=product.name,
                    code=product.code,
                    description=product.description or "",
                    fabric_type=product.fabric_type or "",
                    pattern=product.pattern or "",
                    style=product.style or "",
                    transparency=product.transparency or "",
                    density=density,
                    composition=product.composition or "",
                    care=product.care or "",
                    recommended_rooms=list(product.recommended_rooms or []),
                    recommended_coef=float(product.recommended_coef)
                    if product.recommended_coef
                    else 0.0,
                    default_width_m=float(product.default_width_m)
                    if product.default_width_m
                    else 0.0,
                    is_sewing_required=product.is_sewing_required,
                    segment=product.segment or "",
                    tags_json=json.dumps(product.tags or {}, ensure_ascii=False),
                    variants=variants_pb,
                    image_urls=images,
                )
            )

        return result

    def _categories(self, pb2: Any) -> list[Any]:
        """Kategoriyalar ro'yxati."""
        from apps.catalog.models import Category

        categories = Category.objects.filter(is_active=True).order_by("sort_order")
        return [
            pb2.CatalogCategory(
                id=str(c.id),
                name=c.name,
                slug=c.slug,
                parent_id=str(c.parent_id) if c.parent_id else "",
                sort_order=c.sort_order,
            )
            for c in categories
        ]

    def _calc_rules(self, pb2: Any) -> list[Any]:
        """Hisoblash qoidalari."""
        from apps.pricing.models import CalcRule

        rules = CalcRule.objects.filter(is_active=True)
        return [
            pb2.CatalogCalcRule(
                key=rule.key,
                value=float(rule.value),
                unit=rule.unit,
                description=rule.description or "",
                applies_to_json=json.dumps(rule.applies_to or {}, ensure_ascii=False),
            )
            for rule in rules
        ]

    def _knowledge_rules(self, pb2: Any) -> list[Any]:
        """Bilimlar bazasi qoidalari."""
        from apps.knowledge.models import KnowledgeRule

        rules = KnowledgeRule.objects.filter(is_active=True).order_by("-priority")
        return [
            pb2.CatalogKnowledgeRule(
                id=str(rule.id),
                kind=rule.kind,
                condition_json=json.dumps(rule.condition or {}, ensure_ascii=False),
                recommendation=rule.recommendation,
                priority=rule.priority,
            )
            for rule in rules
        ]

    def _iter_deltas(self, from_version: int, tenant_id: str, pb2: Any) -> Any:
        """Redis pub/sub dan delta'larni o'qib uzatadi."""
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

                if tenant_id and data["tenant_id"] != tenant_id:
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