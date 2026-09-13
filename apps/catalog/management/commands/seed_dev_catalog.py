"""Dev katalogini seed qiladigan management buyrug'i.

Idempotent: kategoriya `slug`, mahsulot `code`, variant `sku`, fason `name` va
bilim qoidasi `(kind, condition)` bo'yicha `update_or_create` ishlatiladi —
buyruq qayta ishga tushirilsa qo'shimcha yozuv yaratmaydi. Faqat DEBUG=True
rejimida yoki `--force` bilan ishlaydi.

Yakunda `import_service` kabi aynan bitta yig'ma `catalog` deltasi Redis'ga
e'lon qilinadi (Go agent `Watch` orqali oladi) — katalog versiyasi shu yerda
bir marta oshadi.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, cast

import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_delete, post_save

from apps.accounts.models import Tenant
from apps.catalog.models import (
    Category,
    Fason,
    FasonAccessory,
    FasonPart,
    Product,
    ProductVariant,
)
from apps.catalog.services.import_service import IMPORT_IN_PROGRESS
from apps.common.choices import CurtainPartRole, PriceUnit
from apps.knowledge.models import KnowledgeRule

logger = structlog.get_logger(__name__)

CATEGORIES: list[tuple[str, str]] = [
    ("portyera", "Portyera"),
    ("tul", "Tul"),
    ("astar", "Astar"),
    ("kant", "Kant"),
    ("lambrekan", "Lambrekan"),
    ("aksesuar", "Aksessuar"),
]

PRODUCTS: list[dict[str, Any]] = [
    {
        "code": "VELVET-MILANO",
        "name": "Velvet Milano",
        "category": "portyera",
        "fabric_type": "velvet",
        "style": "classic",
        "pattern": "plain",
        "segment": "premium",
        "transparency": "blackout",
        "recommended_rooms": ["living"],
        "recommended_coef": "2.500",
        "default_width_m": "2.800",
        "description": "Premium blackout pillus (velvet) portyera — quyosh nurini to'liq to'sadi.",
        "sort_order": 0,
        "variants": [
            {
                "sku": "VELVET-MILANO-BORDO",
                "color_name": "Bordo",
                "color_hex": "#4A0E0E",
                "price": "180000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
            {
                "sku": "VELVET-MILANO-GRAFIT",
                "color_name": "Grafit",
                "color_hex": "#3A3F44",
                "price": "180000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "VELVET-CHEK",
        "name": "Velvet Chek",
        "category": "portyera",
        "fabric_type": "velvet",
        "style": "classic",
        "pattern": "geometric",
        "segment": "premium",
        "transparency": "blackout",
        "recommended_rooms": ["living"],
        "recommended_coef": "2.500",
        "default_width_m": "1.400",
        "description": "Tor mato (eni 1.4 m) — geometrik naqshli premium blackout portyera.",
        "sort_order": 1,
        "variants": [
            {
                "sku": "VELVET-CHEK-ZUMRAD",
                "color_name": "Zumrad",
                "color_hex": "#12682F",
                "price": "165000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "1.400",
            },
            {
                "sku": "VELVET-CHEK-QORA",
                "color_name": "Qora",
                "color_hex": "#1A1A1A",
                "price": "165000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "1.400",
            },
        ],
    },
    {
        "code": "BLACKOUT-DUO",
        "name": "Blackout Duo",
        "category": "portyera",
        "fabric_type": "blackout",
        "style": "modern",
        "pattern": "plain",
        "segment": "standard",
        "transparency": "blackout",
        "recommended_rooms": ["bedroom"],
        "recommended_coef": "2.000",
        "default_width_m": "2.800",
        "description": "Ikkala qatlamli blackout portyera — yotoqxona uchun ideal.",
        "sort_order": 2,
        "variants": [
            {
                "sku": "BLACKOUT-DUO-KUMRANG",
                "color_name": "Kum rang",
                "color_hex": "#8A8D8F",
                "price": "95000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
            {
                "sku": "BLACKOUT-DUO-OQ",
                "color_name": "Oq",
                "color_hex": "#F5F5F5",
                "price": "95000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "LINEN-GREY",
        "name": "Linen Grey",
        "category": "portyera",
        "fabric_type": "linen",
        "style": "minimal",
        "pattern": "plain",
        "segment": "standard",
        "transparency": "semi",
        "recommended_rooms": ["living", "office"],
        "recommended_coef": "1.800",
        "default_width_m": "2.800",
        "description": "Kulrang linen mato — zamonaviy interyer uchun yarim shaffof portyera (hi_tech/minimal uslubga mos).",
        "sort_order": 3,
        "variants": [
            {
                "sku": "LINEN-GREY-KULRANG",
                "color_name": "Kulrang",
                "color_hex": "#A9A9A9",
                "price": "70000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "OFFICE-MINIMAL",
        "name": "Office Minimal",
        "category": "portyera",
        "fabric_type": "polyester",
        "style": "minimal",
        "pattern": "plain",
        "segment": "economy",
        "transparency": "semi",
        "recommended_rooms": ["office"],
        "recommended_coef": "1.500",
        "default_width_m": "2.800",
        "description": "Minimal uslubdagi yengil portyera — ofis uchun ekonom segment.",
        "sort_order": 4,
        "variants": [
            {
                "sku": "OFFICE-MINIMAL-OQ",
                "color_name": "Oq",
                "color_hex": "#FFFFFF",
                "price": "45000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "KIDS-RAINBOW",
        "name": "Kids Rainbow",
        "category": "portyera",
        "fabric_type": "polyester",
        "style": "modern",
        "pattern": "floral",
        "segment": "standard",
        "transparency": "transparent",
        "recommended_rooms": ["kids"],
        "recommended_coef": "2.000",
        "default_width_m": "2.800",
        "description": "Yuviladigan, yorqin rangli mato — bolalar xonasi uchun. 30°S da yuvish mumkin.",
        "care": "30°S da yuvish, oqartiruvchisiz.",
        "sort_order": 5,
        "variants": [
            {
                "sku": "KIDS-RAINBOW-RANGBARANG",
                "color_name": "Rang-barang",
                "color_hex": "#E8B4B8",
                "price": "65000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "CARMEL-KITCHEN",
        "name": "Carmel Kitchen",
        "category": "portyera",
        "fabric_type": "cottage",
        "style": "provence",
        "pattern": "floral",
        "segment": "economy",
        "transparency": "semi",
        "recommended_rooms": ["kitchen"],
        "recommended_coef": "2.000",
        "default_width_m": "2.800",
        "description": "Oshxona uchun provans uslubidagi parda. Rim yoki rulon qatlam sifatida ishlatish mumkin.",
        "tags": ["rim", "rulon"],
        "sort_order": 6,
        "variants": [
            {
                "sku": "CARMEL-KITCHEN-KREM",
                "color_name": "Krem",
                "color_hex": "#F5E1C0",
                "price": "55000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "TUL-DANTEL",
        "name": "Tul Dantel",
        "category": "tul",
        "fabric_type": "tulle",
        "style": "classic",
        "pattern": "floral",
        "segment": "standard",
        "transparency": "transparent",
        "recommended_rooms": ["living", "wedding"],
        "recommended_coef": "2.000",
        "default_width_m": "2.800",
        "description": "Dantel naqshli tul — to'y va yashash xonasi uchun.",
        "sort_order": 7,
        "variants": [
            {
                "sku": "TUL-DANTEL-OQ",
                "color_name": "Oq",
                "color_hex": "#FFFFFF",
                "price": "38000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
            {
                "sku": "TUL-DANTEL-PUSHTI",
                "color_name": "Pushti",
                "color_hex": "#F7C8D0",
                "price": "38000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "TUL-OQ-ODDIY",
        "name": "Tul Oq Oddiy",
        "category": "tul",
        "fabric_type": "tulle",
        "style": "classic",
        "pattern": "plain",
        "segment": "economy",
        "transparency": "transparent",
        "recommended_rooms": ["living", "bedroom", "office", "kitchen", "kids", "wedding"],
        "recommended_coef": "2.000",
        "default_width_m": "2.800",
        "description": "Oddiy oq tul — barcha xonalarga mos.",
        "sort_order": 8,
        "variants": [
            {
                "sku": "TUL-OQ-ODDIY-OQ",
                "color_name": "Oq",
                "color_hex": "#FFFFFF",
                "price": "18000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "ASTAR-SOFT",
        "name": "Astar Soft",
        "category": "astar",
        "fabric_type": "lining",
        "style": "classic",
        "pattern": "plain",
        "segment": "standard",
        "transparency": "semi",
        "recommended_rooms": [],
        "recommended_coef": "1.000",
        "default_width_m": "2.800",
        "description": "Yumshoq astar (lining) matosi — portyera orqasiga.",
        "sort_order": 9,
        "variants": [
            {
                "sku": "ASTAR-SOFT-OQ",
                "color_name": "Oq",
                "color_hex": "#FFFFFF",
                "price": "22000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "KANT-ATLAS",
        "name": "Kant Atlas",
        "category": "kant",
        "fabric_type": "atlas",
        "style": "classic",
        "pattern": "plain",
        "segment": "premium",
        "transparency": "opaque",
        "recommended_rooms": [],
        "recommended_coef": None,
        "default_width_m": "0.150",
        "description": "Atlas kant (dekorativ lenta) — metr hisobida, oltin rang.",
        "sort_order": 10,
        "variants": [
            {
                "sku": "KANT-ATLAS-OLTIN",
                "color_name": "Oltin",
                "color_hex": "#D4AF37",
                "price": "15000.00",
                "price_unit": PriceUnit.PER_METER,
                "width_m": "0.150",
            },
        ],
    },
    {
        "code": "LAMBREKAN-KLASSIK",
        "name": "Lambrekan Klassik",
        "category": "lambrekan",
        "fabric_type": "velvet",
        "style": "classic",
        "pattern": "plain",
        "segment": "premium",
        "transparency": "semi",
        "recommended_rooms": ["living", "wedding"],
        "recommended_coef": "2.000",
        "default_width_m": "2.800",
        "description": "Klassik lambrekan uchun mato.",
        "sort_order": 11,
        "variants": [
            {
                "sku": "LAMBREKAN-KLASSIK-KREM",
                "color_name": "Krem",
                "color_hex": "#F5E1C0",
                "price": "120000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
            {
                "sku": "LAMBREKAN-KLASSIK-MARJON",
                "color_name": "Marjon",
                "color_hex": "#E8796B",
                "price": "120000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "BORDO-SATIN",
        "name": "Bordo Satin",
        "category": "portyera",
        "fabric_type": "satin",
        "style": "classic",
        "pattern": "plain",
        "segment": "premium",
        "transparency": "semi",
        "recommended_rooms": ["living"],
        "recommended_coef": "2.500",
        "default_width_m": "2.800",
        "description": "Bordo rangli satin portyera — klassik uslub uchun.",
        "sort_order": 12,
        "variants": [
            {
                "sku": "BORDO-SATIN-BORDO",
                "color_name": "Bordo",
                "color_hex": "#4A0E0E",
                "price": "155000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
    {
        "code": "GRAFIT-HITECH",
        "name": "Grafit Hi-tech",
        "category": "portyera",
        "fabric_type": "polyester",
        "style": "hi_tech",
        "pattern": "plain",
        "segment": "standard",
        "transparency": "semi",
        "recommended_rooms": ["living"],
        "recommended_coef": "2.000",
        "default_width_m": "2.800",
        "description": "Grafit rangli hi-tech uslubdagi portyera.",
        "sort_order": 13,
        "variants": [
            {
                "sku": "GRAFIT-HITECH-GRAFIT",
                "color_name": "Grafit",
                "color_hex": "#3A3F44",
                "price": "85000.00",
                "price_unit": PriceUnit.PER_SQM,
                "width_m": "2.800",
            },
        ],
    },
]

FASON_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Klassik uch qismli",
        "style": "classic",
        "rooms": ["wedding", "living"],
        "parts": [
            {
                "role": CurtainPartRole.PORTYERA,
                "name": "Portyera",
                "width_share": "1.000",
                "height_share": "1.000",
                "default_coef": "2.500",
                "sort_order": 0,
            },
            {
                "role": CurtainPartRole.TUL,
                "name": "Tul",
                "width_share": "1.000",
                "height_share": "1.000",
                "default_coef": "2.000",
                "sort_order": 1,
            },
            {
                "role": CurtainPartRole.LAMBREKAN,
                "name": "Lambrekan",
                "width_share": "1.000",
                "height_share": "0.150",
                "default_coef": "2.000",
                "sort_order": 2,
            },
        ],
        "accessories": [
            {
                "category": "Kant",
                "default_qty": "1.000",
                "qty_formula": "2 * (width + height)",
            },
        ],
    },
    {
        "name": "Zamonaviy ikki qatlam",
        "style": "modern",
        "rooms": ["living", "bedroom"],
        "parts": [
            {
                "role": CurtainPartRole.PORTYERA,
                "name": "Portyera",
                "width_share": "1.000",
                "height_share": "1.000",
                "default_coef": "2.200",
                "sort_order": 0,
            },
            {
                "role": CurtainPartRole.TUL,
                "name": "Tul",
                "width_share": "1.000",
                "height_share": "1.000",
                "default_coef": "2.000",
                "sort_order": 1,
            },
        ],
        "accessories": [],
    },
    {
        "name": "Ofis minimal",
        "style": "minimal",
        "rooms": ["office"],
        "parts": [
            {
                "role": CurtainPartRole.PORTYERA,
                "name": "Portyera",
                "width_share": "1.000",
                "height_share": "1.000",
                "default_coef": "1.500",
                "sort_order": 0,
            },
        ],
        "accessories": [],
    },
]

KNOWLEDGE_RULES: list[dict[str, Any]] = [
    {
        "kind": KnowledgeRule.Kind.LIGHT,
        "condition": {"light": "south"},
        "recommendation": "Janubiy taraf uchun blackout mato tavsiya qilamiz — quyosh nurini to'liq to'sadi.",
        "priority": 30,
    },
    {
        "kind": KnowledgeRule.Kind.ROOM_STYLE,
        "condition": {"room": "kids"},
        "recommendation": "Bolalar xonasi uchun yuviladigan va yorqin rangli matolarni tavsiya qilamiz.",
        "priority": 25,
    },
    {
        "kind": KnowledgeRule.Kind.CONSTRUCTION,
        "condition": {"construction": "balcony_door"},
        "recommendation": "Balkon eshigi uchun eshik ochilishiga joy qoldiramiz, karnizni devor bo'ylab o'rnatamiz.",
        "priority": 20,
    },
    {
        "kind": KnowledgeRule.Kind.OBJECTION,
        "condition": {"objection": "expensive"},
        "recommendation": "Narx katta tuyulsa — burma koeffitsientini pasaytirish yoki arzon analogni taklif qilish mumkin.",
        "priority": 15,
    },
]


@contextmanager
def _suspend_catalog_signals() -> Iterator[None]:
    """Fason va bilim qoidasi signal'larini vaqtincha to'xtatadi.

    Bu signal'lar `IMPORT_IN_PROGRESS`'ni tekshirmaydi (faqat mahsulot va
    variant signal'lari tekshiradi). Seed yakunida bitta yig'ma `catalog`
    deltasi yuborilgani uchun versiya boshqa joylarda oshmasligi shart —
    shu signallar vaqtincha uzilib, oxirida qayta ulanadi.
    """

    from apps.catalog import signals as catalog_signals
    from apps.knowledge import signals as knowledge_signals

    connections: list[tuple[Any, type[Any], Callable[..., Any]]] = [
        (post_save, Fason, cast(Callable[..., Any], catalog_signals.fason_post_save)),
        (post_delete, Fason, cast(Callable[..., Any], catalog_signals.fason_post_delete)),
        (post_save, FasonPart, cast(Callable[..., Any], catalog_signals.fason_child_changed)),
        (post_delete, FasonPart, cast(Callable[..., Any], catalog_signals.fason_child_changed)),
        (post_save, FasonAccessory, cast(Callable[..., Any], catalog_signals.fason_child_changed)),
        (
            post_delete,
            FasonAccessory,
            cast(Callable[..., Any], catalog_signals.fason_child_changed),
        ),
        (
            post_save,
            KnowledgeRule,
            cast(Callable[..., Any], knowledge_signals.knowledge_rule_post_save),
        ),
        (
            post_delete,
            KnowledgeRule,
            cast(Callable[..., Any], knowledge_signals.knowledge_rule_post_delete),
        ),
    ]
    for signal, sender, receiver in connections:
        signal.disconnect(receiver=receiver, sender=sender)
    try:
        yield
    finally:
        for signal, sender, receiver in connections:
            signal.connect(receiver=receiver, sender=sender, weak=False)


class Command(BaseCommand):
    help = "Dev katalogini seed qiladi (idempotent, faqat DEBUG yoki --force bilan)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="DEBUG=False bo'lsa ham ishlash (dev/lokal baza uchun)",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_dev_catalog faqat DEBUG=True rejimida yoki --force bilan ishlaydi"
            )

        tenant = Tenant.objects.order_by("created_at").first()
        if tenant is None:
            raise CommandError("Tenant topilmadi — avval tenant yaratilishi kerak")

        counts: dict[str, int] = {
            "categories": 0,
            "products": 0,
            "variants": 0,
            "fasons": 0,
            "parts": 0,
            "accessories": 0,
            "rules": 0,
        }

        marker = IMPORT_IN_PROGRESS.set(True)
        try:
            with _suspend_catalog_signals(), transaction.atomic():
                categories = {
                    slug: self._seed_category(tenant, slug, name, counts)
                    for slug, name in CATEGORIES
                }
                for spec in PRODUCTS:
                    self._seed_product(tenant, categories, spec, counts)
                for spec in FASON_TEMPLATES:
                    self._seed_fason(tenant, spec, counts)
                for spec in KNOWLEDGE_RULES:
                    self._seed_rule(spec, counts)
        finally:
            IMPORT_IN_PROGRESS.reset(marker)

        delta_text = "yo'q (o'zgarish yo'q)"
        if any(counts[key] for key in counts):
            from apps.chat.grpc_server.catalog_service import publish_catalog_delta

            publish_catalog_delta(
                tenant_id=str(tenant.id),
                entity="catalog",
                entity_id=str(tenant.id),
                action="update",
            )
            delta_text = "ha"

        message = (
            f"Katalog yaratildi: {counts['products']} mahsulot, "
            f"{counts['variants']} variant, {counts['fasons']} fason, "
            f"{counts['rules']} bilim qoidasi. Delta: {delta_text}"
        )
        logger.info("seed_dev_catalog_done", tenant_id=str(tenant.id), **counts)
        self.stdout.write(self.style.SUCCESS(message))

    def _seed_category(
        self, tenant: Tenant, slug: str, name: str, counts: dict[str, int]
    ) -> Category:
        category, created = Category.objects.update_or_create(
            tenant=tenant,
            slug=slug,
            defaults={"name": name, "sort_order": 0},
        )
        if created:
            counts["categories"] += 1
        return category

    def _seed_product(
        self,
        tenant: Tenant,
        categories: dict[str, Category],
        spec: dict[str, Any],
        counts: dict[str, int],
    ) -> None:
        category = categories[spec["category"]]
        product, created = Product.objects.update_or_create(
            tenant=tenant,
            code=spec["code"],
            defaults={
                "category": category,
                "name": spec["name"],
                "description": spec.get("description", ""),
                "fabric_type": spec.get("fabric_type", ""),
                "pattern": spec.get("pattern", ""),
                "style": spec.get("style", ""),
                "transparency": spec.get("transparency", ""),
                "care": spec.get("care", ""),
                "recommended_rooms": spec.get("recommended_rooms", []),
                "recommended_coef": spec.get("recommended_coef"),
                "default_width_m": spec.get("default_width_m"),
                "segment": spec.get("segment", ""),
                "tags": spec.get("tags", []),
                "sort_order": spec.get("sort_order", 0),
                "is_sewing_required": True,
            },
        )
        if created:
            counts["products"] += 1
        for variant in spec["variants"]:
            self._seed_variant(tenant, product, variant, counts)

    def _seed_variant(
        self, tenant: Tenant, product: Product, spec: dict[str, Any], counts: dict[str, int]
    ) -> None:
        _variant, created = ProductVariant.objects.update_or_create(
            tenant=tenant,
            sku=spec["sku"],
            defaults={
                "product": product,
                "color_name": spec["color_name"],
                "color_hex": spec.get("color_hex", ""),
                "width_m": spec.get("width_m"),
                "price": spec["price"],
                "price_unit": spec["price_unit"],
                "is_active": True,
            },
        )
        if created:
            counts["variants"] += 1

    def _seed_fason(self, tenant: Tenant, spec: dict[str, Any], counts: dict[str, int]) -> None:
        fason, created = Fason.objects.update_or_create(
            tenant=tenant,
            name=spec["name"],
            defaults={
                "style": spec["style"],
                "rooms": spec["rooms"],
                "part_count": len(spec["parts"]),
            },
        )
        if created:
            counts["fasons"] += 1
        for part in spec["parts"]:
            _part, part_created = FasonPart.objects.update_or_create(
                tenant=tenant,
                fason=fason,
                role=part["role"],
                name=part["name"],
                defaults={
                    "width_share": part["width_share"],
                    "height_share": part["height_share"],
                    "default_coef": part["default_coef"],
                    "sort_order": part["sort_order"],
                },
            )
            if part_created:
                counts["parts"] += 1
        for accessory in spec["accessories"]:
            _acc, acc_created = FasonAccessory.objects.update_or_create(
                tenant=tenant,
                fason=fason,
                category=accessory["category"],
                defaults={
                    "default_qty": accessory["default_qty"],
                    "qty_formula": accessory["qty_formula"],
                },
            )
            if acc_created:
                counts["accessories"] += 1

    def _seed_rule(self, spec: dict[str, Any], counts: dict[str, int]) -> None:
        _rule, created = KnowledgeRule.objects.update_or_create(
            kind=spec["kind"],
            condition=spec["condition"],
            defaults={
                "recommendation": spec["recommendation"],
                "priority": spec["priority"],
                "is_active": True,
            },
        )
        if created:
            counts["rules"] += 1
