import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Category, Product
from apps.common.factories import EmployeeFactory, ManagerFactory, TenantFactory


@pytest.fixture
def tenant():
    return TenantFactory()

@pytest.fixture
def employee_client(client, tenant):
    user = EmployeeFactory(tenant=tenant)
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client

@pytest.fixture
def manager_client(client, tenant):
    user = ManagerFactory(tenant=tenant)
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client

@pytest.mark.django_db
class TestPermissions:
    def test_employee_cannot_create_product(self, employee_client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        url = reverse("product-list")
        data = {
            "name": "New Product",
            "code": "NEW-01",
            "category": cat.id
        }
        resp = employee_client.post(url, data)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_edit_product(self, employee_client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        prod = Product.objects.create(tenant=tenant, code="P1", name="Velvet", category=cat)
        url = reverse("product-detail", args=[prod.id])
        data = {"name": "Updated"}
        resp = employee_client.patch(url, data)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_create_product(self, manager_client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        url = reverse("product-list")
        data = {
            "name": "New Product",
            "code": "NEW-01",
            "category": cat.id
        }
        resp = manager_client.post(url, data)
        assert resp.status_code == status.HTTP_201_CREATED

    def test_manager_can_edit_product(self, manager_client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        prod = Product.objects.create(tenant=tenant, code="P1", name="Velvet", category=cat)
        url = reverse("product-detail", args=[prod.id])
        data = {"name": "Updated Product"}
        resp = manager_client.patch(url, data)
        assert resp.status_code == status.HTTP_200_OK
        prod.refresh_from_db()
        assert prod.name == "Updated Product"

    def test_employee_can_read_product(self, employee_client, tenant):
        cat = Category.objects.create(tenant=tenant, name="Pardalar", slug="pardalar")
        Product.objects.create(tenant=tenant, code="P1", name="Velvet", category=cat)
        url = reverse("product-list")
        resp = employee_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
