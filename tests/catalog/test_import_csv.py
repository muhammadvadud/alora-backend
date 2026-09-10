import io

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.factories import ManagerFactory, TenantFactory


@pytest.fixture
def tenant():
    return TenantFactory()

@pytest.fixture
def manager_client(client, tenant):
    user = ManagerFactory(tenant=tenant)
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client

@pytest.mark.django_db
class TestImportCSV:
    def test_successful_import(self, manager_client, tenant):
        url = reverse("import-import-csv")
        csv_content = (
            "code,name,category_slug,sku,color_name,price\n"
            "C1,Zebra,pardalar,Z1-Red,Qizil,150000\n"
            "C1,Zebra,pardalar,Z1-Blue,Ko'k,160000\n"
        )
        file = io.BytesIO(csv_content.encode("utf-8"))
        file.name = "catalog.csv"
        
        resp = manager_client.post(url, {"file": file}, format="multipart")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["created"] == 2
        assert data["updated"] == 0
        assert data["skipped"] == 0
        assert len(data["errors"]) == 0
        
        assert ProductVariant.objects.filter(tenant=tenant).count() == 2
        assert Product.objects.filter(tenant=tenant, code="C1").count() == 1
        assert Category.objects.filter(tenant=tenant, slug="pardalar").count() == 1

    def test_import_with_invalid_row(self, manager_client, tenant):
        url = reverse("import-import-csv")
        csv_content = (
            "code,name,category_slug,sku,color_name,price\n"
            "C1,Zebra,pardalar,Z1-Red,Qizil,150000\n"
            "C2,Rollo,pardalar,R1-White,Oq,not-a-number\n"
        )
        file = io.BytesIO(csv_content.encode("utf-8"))
        file.name = "catalog.csv"
        
        resp = manager_client.post(url, {"file": file}, format="multipart")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["created"] == 1
        assert data["skipped"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["row"] == 3
        
        assert ProductVariant.objects.filter(tenant=tenant).count() == 1

    def test_dry_run(self, manager_client, tenant):
        url = reverse("import-import-csv")
        csv_content = (
            "code,name,category_slug,sku,color_name,price\n"
            "C1,Zebra,pardalar,Z1-Red,Qizil,150000\n"
        )
        file = io.BytesIO(csv_content.encode("utf-8"))
        file.name = "catalog.csv"
        
        resp = manager_client.post(url + "?dry_run=true", {"file": file}, format="multipart")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["created"] == 1
        
        assert ProductVariant.objects.filter(tenant=tenant).count() == 0

    def test_no_file(self, manager_client, tenant):
        url = reverse("import-import-csv")
        resp = manager_client.post(url, {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.json()
        assert data["code"] == "validation_error"
        assert "file" in data["errors"]

