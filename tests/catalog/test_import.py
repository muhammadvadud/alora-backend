import io
from unittest.mock import patch

import pytest
from django.urls import reverse
from openpyxl import Workbook
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Product, ProductVariant
from apps.common.factories import EmployeeFactory, ManagerFactory, TenantFactory

pytestmark = pytest.mark.django_db


def _client(client, user):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def _csv(rows):
    return (
        "product_code,product_name,category_slug,style,pattern,segment,recommended_rooms,"
        "variant_sku,color_name,price,price_unit,width_m,is_active\n" + rows
    ).encode()


def test_import_csv_creates_products_and_variants(client):
    tenant = TenantFactory()
    response = _client(client, ManagerFactory(tenant=tenant)).post(
        reverse("import-list"),
        {
            "file": io.BytesIO(
                _csv(
                    "P1,One,curtain,,,home,living;bedroom,S1,Red,10,per_sqm,2,true\nP2,Two,curtain,,,home,living,S2,Blue,20,per_sqm,2,true\nP2,Two,curtain,,,home,living,S3,Green,21,per_sqm,2,true\n"
                )
            )
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["created"] == 3
    assert Product.objects.filter(tenant=tenant).count() == 2
    assert ProductVariant.objects.filter(tenant=tenant).count() == 3


def test_import_xlsx_and_dry_run_do_not_write(client):
    tenant = TenantFactory()
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(
        ["product_code", "product_name", "category_slug", "variant_sku", "color_name", "price"]
    )
    sheet.append(["P1", "One", "curtain", "S1", "Red", 10])
    content = io.BytesIO()
    workbook.save(content)
    content.seek(0)
    content.name = "catalog.xlsx"

    response = _client(client, ManagerFactory(tenant=tenant)).post(
        reverse("import-list") + "?dry_run=true", {"file": content}, format="multipart"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["created"] == 1
    assert Product.objects.filter(tenant=tenant).count() == 0


def test_import_reports_bad_row_and_keeps_good_rows(client):
    tenant = TenantFactory()
    response = _client(client, ManagerFactory(tenant=tenant)).post(
        reverse("import-list"),
        {
            "file": io.BytesIO(
                _csv(
                    "P1,One,curtain,,,home,living,S1,Red,-10,per_sqm,,true\nP2,Two,curtain,,,home,living,S2,Blue,20,per_sqm,,true\n"
                )
            )
        },
        format="multipart",
    )
    assert response.data["skipped"] == 1
    assert response.data["errors"][0]["field"] == "price"
    assert Product.objects.filter(tenant=tenant).count() == 1


def test_employee_cannot_import_catalog(client):
    tenant = TenantFactory()
    response = _client(client, EmployeeFactory(tenant=tenant)).post(
        reverse("import-list"), {"file": io.BytesIO(b"bad")}, format="multipart"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_import_rejects_large_file(client):
    tenant = TenantFactory()
    response = _client(client, ManagerFactory(tenant=tenant)).post(
        reverse("import-list"),
        {"file": io.BytesIO(b"x" * (5 * 1024 * 1024 + 1))},
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "5 MB" in str(response.data)


@patch("apps.chat.grpc_server.catalog_service.publish_catalog_delta")
def test_import_increments_catalog_version_once(mock_publish, client):
    tenant = TenantFactory()
    response = _client(client, ManagerFactory(tenant=tenant)).post(
        reverse("import-list"),
        {
            "file": io.BytesIO(
                _csv(
                    "P1,One,curtain,,,home,living,S1,Red,10,per_sqm,,true\nP2,Two,curtain,,,home,living,S2,Blue,20,per_sqm,,true\n"
                )
            )
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_200_OK
    assert mock_publish.call_count == 1
