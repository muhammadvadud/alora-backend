import time

import pytest
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductImage, ProductVariant
from apps.common.choices import UserRole
from apps.common.factories import UserFactory


@pytest.fixture
def api_client_auth(api_client):
    user = UserFactory(role=UserRole.EMPLOYEE)
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestCatalogQueries:
    def setup_data(self, tenant, count=5):
        import uuid

        uid = str(uuid.uuid4())[:8]
        category = Category.objects.create(
            tenant=tenant, name=f"Test Cat {uid}", slug=f"test-cat-{uid}"
        )
        for i in range(count):
            p = Product.objects.create(
                tenant=tenant, category=category, name=f"Prod {uid} {i}", code=f"P{uid}{i}"
            )
            v1 = ProductVariant.objects.create(
                tenant=tenant, product=p, sku=f"SKU-{uid}-{i}-1", price=100
            )
            v2 = ProductVariant.objects.create(
                tenant=tenant, product=p, sku=f"SKU-{uid}-{i}-2", price=120
            )
            ProductImage.objects.create(tenant=tenant, product=p, variant=v1, image="test1.png")
            ProductImage.objects.create(tenant=tenant, product=p, variant=v2, image="test2.png")
        return category

    def test_categories_queries(self, api_client_auth):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        tenant = api_client_auth.handler._force_user.tenant
        self.setup_data(tenant, 5)

        url = reverse("category-list")

        with CaptureQueriesContext(connection) as ctx1:
            api_client_auth.get(url)
        q1 = len(ctx1.captured_queries)

        self.setup_data(tenant, 15)

        with CaptureQueriesContext(connection) as ctx2:
            response = api_client_auth.get(url)
        q2 = len(ctx2.captured_queries)

        assert response.status_code == 200
        assert q1 == q2, f"Queries changed: {q1} != {q2}"

    def test_products_queries(self, api_client_auth):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        tenant = api_client_auth.handler._force_user.tenant
        self.setup_data(tenant, 5)

        url = reverse("product-list")

        with CaptureQueriesContext(connection) as ctx1:
            api_client_auth.get(url)
        q1 = len(ctx1.captured_queries)

        self.setup_data(tenant, 15)

        with CaptureQueriesContext(connection) as ctx2:
            response = api_client_auth.get(url)
        q2 = len(ctx2.captured_queries)

        assert response.status_code == 200
        assert q1 == q2, f"Queries changed: {q1} != {q2}"

    def test_product_detail_queries(self, api_client_auth, django_assert_num_queries):
        tenant = api_client_auth.handler._force_user.tenant
        self.setup_data(tenant, 5)

        p = Product.objects.filter(tenant=tenant).first()
        url = reverse("product-detail", kwargs={"pk": p.id})

        with django_assert_num_queries(4):
            response = api_client_auth.get(url)

        assert response.status_code == 200

    def test_catalog_response_time(self, api_client_auth):
        tenant = api_client_auth.handler._force_user.tenant
        self.setup_data(tenant, 20)

        url = reverse("product-list")

        start = time.perf_counter()
        response = api_client_auth.get(url)
        end = time.perf_counter()

        assert response.status_code == 200
        assert (end - start) < 0.3, "Javob vaqti 300 ms dan oshdi!"
