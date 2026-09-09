import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.choices import PriceUnit
from apps.common.factories import AdminFactory, EmployeeFactory, ManagerFactory, TenantFactory


@pytest.fixture
def tenant():
    return TenantFactory()

def get_client_for_user(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client

@pytest.mark.django_db
class TestCostPriceVisibility:
    def test_cost_price_visibility(self, client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        prod = Product.objects.create(tenant=tenant, code="P1", name="Velvet", category=cat)
        ProductVariant.objects.create(
            tenant=tenant, sku="P1-V1", product=prod, color_name="Red", 
            price="100000.00", cost_price="50000.00", price_unit=PriceUnit.PER_SQM
        )
        
        url_list = reverse("product-list")
        url_detail = reverse("product-detail", args=[prod.id])
        
        # Test Employee
        emp = EmployeeFactory(tenant=tenant)
        emp_client = get_client_for_user(client, emp)
        
        resp = emp_client.get(url_list)
        assert "cost_price" not in resp.data["results"][0]["variants"][0]
        
        resp = emp_client.get(url_detail)
        assert "cost_price" not in resp.data["variants"][0]

        # Test Manager
        mgr = ManagerFactory(tenant=tenant)
        mgr_client = get_client_for_user(client, mgr)
        
        resp = mgr_client.get(url_list)
        assert "cost_price" not in resp.data["results"][0]["variants"][0]

        resp = mgr_client.get(url_detail)
        assert "cost_price" not in resp.data["variants"][0]

        # Test Admin
        adm = AdminFactory(tenant=tenant)
        adm_client = get_client_for_user(client, adm)
        
        resp = adm_client.get(url_list)
        assert "cost_price" in resp.data["results"][0]["variants"][0]
        assert resp.data["results"][0]["variants"][0]["cost_price"] == "50000.00"

        resp = adm_client.get(url_detail)
        assert "cost_price" in resp.data["variants"][0]
        assert resp.data["variants"][0]["cost_price"] == "50000.00"
