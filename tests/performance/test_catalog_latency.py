"""14.8 - Katalog API <= 300 ms."""

import statistics
import time
import uuid

import pytest
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from apps.catalog.models import Category, Product, ProductImage, ProductVariant

pytestmark = pytest.mark.django_db

def test_catalog_latency(api_client, employee_user):
    if not employee_user.tenant.pk or not type(employee_user.tenant).objects.filter(pk=employee_user.tenant.pk).exists():
        employee_user.tenant.save()
    if employee_user._state.adding:
        employee_user.save()
        
    tenant = employee_user.tenant
    
    category = Category.objects.create(tenant=tenant, name="Lat Cat", slug="lat-cat")
    
    products = []
    for i in range(50):
        uid = str(uuid.uuid4())[:8]
        p = Product.objects.create(tenant=tenant, category=category, name=f"Lat Prod {uid}", code=f"LP{uid}")
        for j in range(3):
            ProductVariant.objects.create(tenant=tenant, product=p, sku=f"SKU-{uid}-{j}", price=100)
        for j in range(2):
            ProductImage.objects.create(tenant=tenant, product=p, image=f"img-{uid}-{j}.png")
        products.append(p)

    api_client.force_authenticate(user=employee_user)
    
    # URL is 'product-list' without 'catalog:' namespace in this project according to tests
    try:
        list_url = reverse("catalog:product-list")
    except NoReverseMatch:
        list_url = reverse("product-list")
    
    list_measurements = []
    for _ in range(5):
        start = time.perf_counter()
        response = api_client.get(list_url)
        end = time.perf_counter()
        assert response.status_code == 200
        list_measurements.append((end - start) * 1000)
        
    list_median = statistics.median(list_measurements)
    print(f"Catalog List API median latency: {list_median:.2f} ms")
    assert list_median <= 300, f"List latency {list_median:.2f} ms > 300 ms"
    
    try:
        detail_url = reverse("catalog:product-detail", kwargs={"pk": str(products[0].id)})
    except NoReverseMatch:
        detail_url = reverse("product-detail", kwargs={"pk": str(products[0].id)})
        
    detail_measurements = []
    for _ in range(5):
        start = time.perf_counter()
        response = api_client.get(detail_url)
        end = time.perf_counter()
        assert response.status_code == 200
        detail_measurements.append((end - start) * 1000)
        
    detail_median = statistics.median(detail_measurements)
    print(f"Catalog Detail API median latency: {detail_median:.2f} ms")
    assert detail_median <= 300, f"Detail latency {detail_median:.2f} ms > 300 ms"
