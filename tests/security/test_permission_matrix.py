import pytest
from django.urls import reverse

from apps.common.choices import UserRole
from apps.common.factories import UserFactory


@pytest.fixture
def users():
    return {
        "employee": UserFactory(role=UserRole.EMPLOYEE),
        "manager": UserFactory(role=UserRole.MANAGER),
        "admin": UserFactory(role=UserRole.ADMIN),
    }

matrix_cases = [
    # (endpoint_name, http_method, kwargs, user_roles_expected_status)
    # chat, katalog o'qish -> employee ✅, manager ✅, admin ✅
    ("chat:conversation-list", "get", {}, {"employee": 200, "manager": 200, "admin": 200}),
    ("product-list", "get", {}, {"employee": 200, "manager": 200, "admin": 200}),

    # buyurtma yaratish -> employee ✅, manager ✅, admin ✅
    ("orders:order-list", "post", {}, {"employee": 400, "manager": 400, "admin": 400}), # 400 is fine (validation error), means not 403

    # katalog yozish, narx -> employee ❌, manager ✅, admin ✅
    ("product-list", "post", {}, {"employee": 403, "manager": 400, "admin": 400}),
    ("service-price-root", "patch", {}, {"employee": 403, "manager": 405, "admin": 405}), # PATCH list is method not allowed or 400, let's just check 403

    # xodimlar, limit, usage -> employee ❌, manager ✅, admin ✅
    ("employee-list", "get", {}, {"employee": 403, "manager": 200, "admin": 200}),
    ("usage-summary", "get", {}, {"employee": 403, "manager": 200, "admin": 200}),

    # calc-rules, knowledge -> employee ❌, manager ✅, admin ✅
    ("calc-rule-root", "patch", {}, {"employee": 403, "manager": 405, "admin": 405}),
    ("knowledge-rule-list", "post", {}, {"employee": 403, "manager": 400, "admin": 400}),

    # system prompt, ModelPricing, tannarx -> employee ❌, manager ❌, admin ✅
    ("prompts:prompt-list", "post", {}, {"employee": 403, "manager": 403, "admin": 400}),
    ("model-pricing-list", "post", {}, {"employee": 403, "manager": 403, "admin": 400}),
]

@pytest.mark.django_db
@pytest.mark.parametrize("url_name, method, kwargs, expected", matrix_cases)
def test_permission_matrix(api_client, users, url_name, method, kwargs, expected):
    url = reverse(url_name, kwargs=kwargs)
    
    for role, expected_status in expected.items():
        user = users[role]
        api_client.force_authenticate(user=user)
        
        req_method = getattr(api_client, method)
        response = req_method(url, data={})
        
        if expected_status == 403:
            assert response.status_code == 403, f"{role} uchun {url_name} ga ruxsat berildi!"
        else:
            assert response.status_code != 403, f"{role} uchun {url_name} man etildi!"
