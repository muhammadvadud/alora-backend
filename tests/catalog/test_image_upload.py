import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.catalog.models import Category, Product
from apps.common.choices import UserRole
from apps.common.factories import UserFactory


@pytest.fixture
def admin_client(api_client):
    user = UserFactory(role=UserRole.ADMIN)
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_image_upload_success(admin_client):
    admin_user = admin_client.handler._force_user
    tenant = admin_user.tenant
    category = Category.objects.create(tenant=tenant, name="Cat", slug="cat")
    product = Product.objects.create(tenant=tenant, category=category, name="Prod", code="P1")

    from PIL import Image

    img = Image.new("RGB", (10, 10), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    image_data = img_byte_arr.getvalue()

    file = SimpleUploadedFile("test.png", image_data, content_type="image/png")

    url = reverse("product-images", kwargs={"pk": product.id})
    response = admin_client.post(url, {"image": file}, format="multipart")

    assert response.status_code == status.HTTP_201_CREATED, response.data


@pytest.mark.django_db
def test_image_upload_large_file():
    from django.core.exceptions import ValidationError

    from apps.common.validators import validate_image_file

    file = SimpleUploadedFile("large.png", b"dummy", content_type="image/png")
    file.size = 11 * 1024 * 1024

    with pytest.raises(ValidationError, match="Fayl hajmi 10 MB dan oshmasligi kerak"):
        validate_image_file(file)


@pytest.mark.django_db
def test_image_upload_invalid_mime():
    from django.core.exceptions import ValidationError

    from apps.common.validators import validate_image_file

    file = SimpleUploadedFile("test.pdf", b"dummy", content_type="application/pdf")
    file.size = 100

    with pytest.raises(
        ValidationError, match="Faqat JPEG, PNG va WEBP formatidagi rasmlar ruxsat etiladi"
    ):
        validate_image_file(file)
