"""System prompt boshqaruvi API testlari (Bosqich 11)."""

from __future__ import annotations

from typing import Any

from rest_framework import status

from apps.prompts.models import PromptVersion

PROMPT_URL = "/api/v1/settings/prompt/"


def _seed_versions(*, admin: Any, contents: list[str]) -> list[PromptVersion]:
    """Berilgan matnlar bilan ketma-ket versiyalar yaratadi (oxirgisi joriy)."""

    versions: list[PromptVersion] = []
    for index, content in enumerate(contents, start=1):
        versions.append(
            PromptVersion.objects.create(
                version=index,
                content=content,
                author=admin,
                is_current=(index == len(contents)),
            )
        )
    return versions


class TestPermission:
    """Faqat admin kira oladi (employee va manager 403)."""

    def test_employee_cannot_list(self, auth_client: Any, employee: Any) -> None:
        assert auth_client(employee).get(PROMPT_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_create(self, auth_client: Any, employee: Any) -> None:
        response = auth_client(employee).post(PROMPT_URL, {"content": "test"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_rollback(self, auth_client: Any, employee: Any, admin: Any) -> None:
        _seed_versions(admin=admin, contents=["A", "B"])
        response = auth_client(employee).post(f"{PROMPT_URL}1/rollback/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_cannot_list(self, auth_client: Any, manager: Any) -> None:
        assert auth_client(manager).get(PROMPT_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_manager_cannot_create(self, auth_client: Any, manager: Any) -> None:
        response = auth_client(manager).post(PROMPT_URL, {"content": "test"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_cannot_rollback(self, auth_client: Any, manager: Any, admin: Any) -> None:
        _seed_versions(admin=admin, contents=["A", "B"])
        response = auth_client(manager).post(f"{PROMPT_URL}1/rollback/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list(self, auth_client: Any, admin: Any) -> None:
        assert auth_client(admin).get(PROMPT_URL).status_code == status.HTTP_200_OK


class TestCreate:
    """11.3: POST — yangi versiya, automatik raqam, muallif = request.user."""

    def test_creates_first_version(self, auth_client: Any, admin: Any) -> None:
        response = auth_client(admin).post(
            PROMPT_URL, {"content": "Siz professional parda yordamchisisiz"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        assert data["version"] == 1
        assert data["is_current"] is True
        assert data["content"] == "Siz professional parda yordamchisisiz"
        assert data["author"] == admin.id

    def test_version_number_increments(self, auth_client: Any, admin: Any) -> None:
        client = auth_client(admin)
        first = client.post(PROMPT_URL, {"content": "A"})
        second = client.post(PROMPT_URL, {"content": "B"})
        assert first.data["version"] == 1
        assert second.data["version"] == 2
        assert second.data["is_current"] is True

    def test_new_version_becomes_current(self, auth_client: Any, admin: Any) -> None:
        client = auth_client(admin)
        client.post(PROMPT_URL, {"content": "A"})
        client.post(PROMPT_URL, {"content": "B"})
        v1 = PromptVersion.objects.get(version=1)
        v2 = PromptVersion.objects.get(version=2)
        assert v1.is_current is False
        assert v2.is_current is True

    def test_empty_content_rejected(self, auth_client: Any, admin: Any) -> None:
        response = auth_client(admin).post(PROMPT_URL, {"content": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_whitespace_content_rejected(self, auth_client: Any, admin: Any) -> None:
        response = auth_client(admin).post(PROMPT_URL, {"content": "   "})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestList:
    """11.2: GET — joriy versiya + to'liq tarix."""

    def test_empty_history(self, auth_client: Any, admin: Any) -> None:
        response = auth_client(admin).get(PROMPT_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["current"] is None
        assert response.data["history"] == []

    def test_returns_current_and_full_history(self, auth_client: Any, admin: Any) -> None:
        _seed_versions(admin=admin, contents=["A", "B", "C"])
        response = auth_client(admin).get(PROMPT_URL)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["current"]["version"] == 3
        assert data["current"]["content"] == "C"
        history_versions = [row["version"] for row in data["history"]]
        assert history_versions == [3, 2, 1]
        assert all(row["is_current"] is False for row in data["history"] if row["version"] != 3)


class TestRollback:
    """11.4: rollback — eski matn bilan YANGI versiya, audit tarixi buzilmaydi."""

    def test_rollback_creates_new_version_with_old_content(
        self, auth_client: Any, admin: Any
    ) -> None:
        _seed_versions(admin=admin, contents=["A", "B"])
        response = auth_client(admin).post(f"{PROMPT_URL}1/rollback/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["version"] == 3
        assert data["content"] == "A"
        assert data["is_current"] is True

        assert PromptVersion.objects.count() == 3

        v1 = PromptVersion.objects.get(version=1)
        v2 = PromptVersion.objects.get(version=2)
        v3 = PromptVersion.objects.get(version=3)
        assert v1.content == "A"
        assert v1.is_current is False
        assert str(v1.author_id) == str(admin.id)
        assert v2.content == "B"
        assert v2.is_current is False
        assert v3.content == "A"
        assert v3.is_current is True

    def test_current_prompt_content_after_rollback(self, auth_client: Any, admin: Any) -> None:
        _seed_versions(admin=admin, contents=["Eski matn", "Hozirgi matn"])
        auth_client(admin).post(f"{PROMPT_URL}1/rollback/")
        response = auth_client(admin).get(PROMPT_URL)
        assert response.data["current"]["content"] == "Eski matn"
        assert response.data["current"]["version"] == 3

    def test_rollback_unknown_version_returns_404(self, auth_client: Any, admin: Any) -> None:
        response = auth_client(admin).post(f"{PROMPT_URL}99/rollback/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGoNotification:
    """11.5: prompt o'zgarganda Redis pub/sub orqali xabar, Redis ishlamasa 200."""

    def test_create_publishes_prompt_channel(
        self, auth_client: Any, admin: Any, monkeypatch: Any
    ) -> None:
        import redis as redis_lib

        published: list[dict[str, Any]] = []

        class _FakeRedis:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def publish(self, channel: str, message: str) -> None:
                import json

                published.append({"channel": channel, "message": json.loads(message)})

        monkeypatch.setattr(redis_lib, "from_url", _FakeRedis)
        response = auth_client(admin).post(PROMPT_URL, {"content": "Yangi matn"})
        assert response.status_code == status.HTTP_201_CREATED
        assert len(published) == 1
        assert published[0]["channel"] == "alora:prompt:updated"
        assert published[0]["message"]["entity"] == "system_prompt"
        assert published[0]["message"]["version"] == 1

    def test_create_succeeds_when_redis_down(
        self, auth_client: Any, admin: Any, monkeypatch: Any
    ) -> None:
        import redis as redis_lib

        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise redis_lib.RedisError("redis ishlamayapti")

        monkeypatch.setattr(redis_lib, "from_url", _raise)
        response = auth_client(admin).post(PROMPT_URL, {"content": "Redis bo'sa ham ishlaydi"})
        assert response.status_code == status.HTTP_201_CREATED
        assert PromptVersion.objects.count() == 1

    def test_rollback_succeeds_when_redis_down(
        self, auth_client: Any, admin: Any, monkeypatch: Any
    ) -> None:
        import redis as redis_lib

        _seed_versions(admin=admin, contents=["A", "B"])

        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise redis_lib.RedisError("redis ishlamayapti")

        monkeypatch.setattr(redis_lib, "from_url", _raise)
        response = auth_client(admin).post(f"{PROMPT_URL}1/rollback/")
        assert response.status_code == status.HTTP_200_OK
        assert PromptVersion.objects.count() == 3
