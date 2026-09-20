import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestAuth:
    def test_login_success(self, client):
        user = UserFactory(password="securepass123")
        url = reverse("login")
        response = client.post(url, {"phone": user.phone, "password": "securepass123"})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, client):
        user = UserFactory(password="securepass123")
        url = reverse("login")
        response = client.post(url, {"phone": user.phone, "password": "wrongpass"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, client):
        user = UserFactory(password="securepass123", is_active=False)
        url = reverse("login")
        response = client.post(url, {"phone": user.phone, "password": "securepass123"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_and_rotation(self, client):
        user = UserFactory(password="securepass123")
        url = reverse("login")
        response = client.post(url, {"phone": user.phone, "password": "securepass123"})
        refresh_token = response.data["refresh"]

        refresh_url = reverse("refresh")
        refresh_response = client.post(refresh_url, {"refresh": refresh_token})
        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access" in refresh_response.data
        assert "refresh" in refresh_response.data
        assert refresh_response.data["refresh"] != refresh_token

        # Check blacklist (using old token should fail)
        old_token_response = client.post(refresh_url, {"refresh": refresh_token})
        assert old_token_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_me(self, client):
        user = UserFactory(password="securepass123")
        url = reverse("login")
        response = client.post(url, {"phone": user.phone, "password": "securepass123"})
        access_token = response.data["access"]

        me_url = reverse("me")
        me_response = client.get(me_url, HTTP_AUTHORIZATION=f"Bearer {access_token}")
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.data["profile"]["phone"] == user.phone
        assert "limit" in me_response.data

    def test_authenticated_user_can_change_own_password(self, client):
        user = UserFactory(password="securepass123")
        token = str(RefreshToken.for_user(user).access_token)

        response = client.post(
            reverse("me-password"),
            {"password": "new-password-123", "password_confirmation": "new-password-123"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("new-password-123")
