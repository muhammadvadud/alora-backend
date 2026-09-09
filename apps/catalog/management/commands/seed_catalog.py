import structlog
from django.core.management.base import BaseCommand

from apps.accounts.models import Tenant
from apps.catalog.models import Category, Product, ProductVariant
from apps.common.choices import PriceUnit

logger = structlog.get_logger(__name__)

class Command(BaseCommand):
    help = "Seed catalog data"

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(
            name="Default Tenant",
            defaults={"phone": "+998901234567"}
        )

        categories = {
            "Pardalar": ["Portyera", "Tul", "Rim parda", "Rulon parda", "Lambrekan"],
            "Karnizlar": [],
            "Aksessuarlar": [],
            "Xizmatlar": [],
        }

        for parent_name, children in categories.items():
            parent, _ = Category.objects.get_or_create(
                tenant=tenant,
                slug=parent_name.lower().replace(" ", "-"),
                defaults={"name": parent_name, "sort_order": 0}
            )
            for i, child_name in enumerate(children):
                Category.objects.get_or_create(
                    tenant=tenant,
                    slug=child_name.lower().replace(" ", "-"),
                    defaults={"name": child_name, "parent": parent, "sort_order": i}
                )

        # Products
        portyera = Category.objects.get(tenant=tenant, slug="portyera")
        aksessuar = Category.objects.get(tenant=tenant, slug="aksessuarlar")
        
        prod1, _ = Product.objects.get_or_create(
            tenant=tenant,
            code="VELV-01",
            defaults={
                "name": "Velvet Milano",
                "category": portyera,
                "fabric_type": "velvet",
                "style": "modern",
                "segment": "premium",
                "default_width_m": "2.800"
            }
        )
        
        ProductVariant.objects.get_or_create(
            tenant=tenant,
            sku="VELV-01-GRY",
            defaults={
                "product": prod1,
                "color_name": "Grafit",
                "price": "150000.00",
                "price_unit": PriceUnit.PER_SQM,
                "cost_price": "80000.00"
            }
        )

        prod2, _ = Product.objects.get_or_create(
            tenant=tenant,
            code="HOOK-01",
            defaults={
                "name": "Karniz ilmog'i",
                "category": aksessuar,
                "segment": "standard",
                "is_sewing_required": False
            }
        )
        
        ProductVariant.objects.get_or_create(
            tenant=tenant,
            sku="HOOK-01-WHT",
            defaults={
                "product": prod2,
                "color_name": "Oq",
                "price": "500.00",
                "price_unit": PriceUnit.PER_PIECE,
                "cost_price": "200.00"
            }
        )

        prod3, _ = Product.objects.get_or_create(
            tenant=tenant,
            code="TAPE-01",
            defaults={
                "name": "Parda tasmasi",
                "category": aksessuar,
                "segment": "economy",
                "is_sewing_required": True
            }
        )
        
        ProductVariant.objects.get_or_create(
            tenant=tenant,
            sku="TAPE-01-STD",
            defaults={
                "product": prod3,
                "color_name": "Standart",
                "price": "15000.00",
                "price_unit": PriceUnit.PER_METER,
                "cost_price": "8000.00"
            }
        )

        logger.info("Catalog seed complete")
        self.stdout.write(self.style.SUCCESS("Catalog seeded successfully."))
