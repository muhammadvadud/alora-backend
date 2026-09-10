import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.choices import PriceUnit
from apps.common.factories import ManagerFactory, TenantFactory


@pytest.fixture
def tenant():
    return TenantFactory()


@pytest.fixture
def manager_client(client, tenant):
    user = ManagerFactory(tenant=tenant)
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.mark.django_db
class TestBulkPrice:
    def test_bulk_price_amount(self, manager_client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        prod = Product.objects.create(tenant=tenant, code="P1", name="Velvet", category=cat)
        var1 = ProductVariant.objects.create(
            tenant=tenant,
            sku="P1-V1",
            product=prod,
            color_name="Red",
            price="100000.00",
            price_unit=PriceUnit.PER_SQM,
        )
        var2 = ProductVariant.objects.create(
            tenant=tenant,
            sku="P1-V2",
            product=prod,
            color_name="Blue",
            price="150000.00",
            price_unit=PriceUnit.PER_SQM,
        )

        url = reverse("variant-bulk-price")
        data = {"variant_ids": [var1.id, var2.id], "value": "10000.00", "type": "amount"}

        resp = manager_client.post(url, data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["updated"] == 2

        var1.refresh_from_db()
        var2.refresh_from_db()

        assert var1.price == 110000
        assert var2.price == 160000

    def test_bulk_price_percent(self, manager_client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        prod = Product.objects.create(tenant=tenant, code="P1", name="Velvet", category=cat)
        var1 = ProductVariant.objects.create(
            tenant=tenant,
            sku="P1-V1",
            product=prod,
            color_name="Red",
            price="100000.00",
            price_unit=PriceUnit.PER_SQM,
        )
        var2 = ProductVariant.objects.create(
            tenant=tenant,
            sku="P1-V2",
            product=prod,
            color_name="Blue",
            price="150000.00",
            price_unit=PriceUnit.PER_SQM,
        )

        url = reverse("variant-bulk-price")
        data = {"variant_ids": [var1.id, var2.id], "value": "10.00", "type": "percent"}

        resp = manager_client.post(url, data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["updated"] == 2

        var1.refresh_from_db()
        var2.refresh_from_db()

        assert var1.price == 110000
        assert var2.price == 165000
