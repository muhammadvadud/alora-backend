import pytest
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.choices import PriceUnit
from apps.common.factories import EmployeeFactory, TenantFactory


@pytest.fixture
def api_client_auth(client):
    tenant = TenantFactory()
    user = EmployeeFactory(tenant=tenant)
    # Simple JWT token needs to be generated or we can just force_login if using SessionAuth in tests,
    # but the API uses JWT. Let's see how they test it.
    from rest_framework_simplejwt.tokens import RefreshToken
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client, tenant, user

@pytest.mark.django_db
class TestFilters:
    def test_product_filters(self, api_client_auth):
        client, tenant, _user = api_client_auth
        
        # create categories
        cat1 = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        cat2 = Category.objects.create(tenant=tenant, name="Karnizlar", slug="karnizlar")
        
        # create products
        prod1 = Product.objects.create(
            tenant=tenant, code="P1", name="Velvet", category=cat1, 
            style="modern", recommended_rooms=["living"], segment="premium",
            description="Nice velvet", tags=["new"]
        )
        ProductVariant.objects.create(
            tenant=tenant, sku="P1-V1", product=prod1, color_name="Red", 
            price="100000.00", price_unit=PriceUnit.PER_SQM
        )
        
        prod2 = Product.objects.create(
            tenant=tenant, code="P2", name="Rulon", category=cat2, 
            style="classic", recommended_rooms=["kitchen"], segment="standard"
        )
        ProductVariant.objects.create(
            tenant=tenant, sku="P2-V1", product=prod2, color_name="White", 
            price="50000.00", price_unit=PriceUnit.PER_PIECE
        )
        
        url = reverse("product-list")
        
        # check category filter
        resp = client.get(url, {"category": cat1.id})
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P1"
        
        # check style filter
        resp = client.get(url, {"style": "classic"})
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P2"
        
        # check room filter
        resp = client.get(url, {"room": "living"})
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P1"
        
        # check segment
        resp = client.get(url, {"segment": "premium"})
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P1"
        
        # check price_unit
        resp = client.get(url, {"price_unit": "per_piece"})
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P2"
        
        # check search
        resp = client.get(url, {"search": "Velvet"})
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P1"
        
        # check min/max price
        resp = client.get(url, {"min_price": "80000"})
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P1"
        
        resp = client.get(url, {"max_price": "80000"})
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["code"] == "P2"
