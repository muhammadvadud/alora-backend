"""Testlar uchun bazaviy fabrikalar."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

from django.apps import apps
from django.contrib.auth import get_user_model

from .choices import UserRole

try:  # pragma: no cover - factory_boy mavjud bo'lsa ishlatamiz
    import factory
    from factory.django import DjangoModelFactory
except ImportError:  # pragma: no cover - fallback
    factory = None
    DjangoModelFactory = None

try:
    UserModel = get_user_model()
except Exception:  # noqa: BLE001  # pragma: no cover - settings hali yo'q bo'lishi mumkin
    UserModel = None

try:
    TenantModel = apps.get_model("accounts", "Tenant")
except Exception:  # noqa: BLE001  # pragma: no cover - accounts app keyinroq qo'shiladi
    TenantModel = None


def _default_phone(seed: int) -> str:
    """Takrorlanmaydigan test telefon raqamini yaratadi."""

    return f"+99890111{seed:04d}"


def _fallback_namespace(model_name: str, **kwargs: Any) -> SimpleNamespace:
    """Model yo'q bo'lsa oddiy namespace qaytaradi."""

    object_id = uuid.uuid4()
    payload = {"id": object_id, "pk": object_id, "is_active": True}
    payload.update(kwargs)
    payload.setdefault("model_name", model_name)
    return SimpleNamespace(**payload)


def _model_has_fields(model: type[Any] | None, field_names: tuple[str, ...]) -> bool:
    """Model kerakli maydonlarga ega ekanini tekshiradi."""

    if model is None:
        return False
    meta = getattr(model, "_meta", None)
    if meta is None:
        return False
    try:
        existing_fields = {field.name for field in meta.get_fields()}
    except Exception:  # noqa: BLE001  # pragma: no cover - fallback himoyasi
        return False
    return set(field_names).issubset(existing_fields)


if DjangoModelFactory is not None and _model_has_fields(
    TenantModel, ("name", "address", "phone", "currency", "timezone")
):

    class BaseTenantFactory(DjangoModelFactory):
        """Tenant uchun umumiy factory bazasi."""

        class Meta:
            model = TenantModel
            abstract = True

        name = factory.Sequence(lambda n: f"Filial {n + 1}")
        address = "Toshkent"
        phone = factory.Sequence(_default_phone)
        currency = "UZS"
        timezone = "Asia/Tashkent"
        is_active = True

    class TenantFactory(BaseTenantFactory):
        """Tenant uchun konkret factory."""

        class Meta:
            model = TenantModel

else:

    class BaseTenantFactory:
        """Tenant uchun fallback factory."""

        @classmethod
        def build(cls, **kwargs: Any) -> SimpleNamespace:
            payload = {
                "name": "Filial 1",
                "address": "Toshkent",
                "phone": _default_phone(1),
                "currency": "UZS",
                "timezone": "Asia/Tashkent",
                "is_active": True,
            }
            payload.update(kwargs)
            return _fallback_namespace("Tenant", **payload)

        create = build

    TenantFactory = BaseTenantFactory


if (
    DjangoModelFactory is not None
    and _model_has_fields(UserModel, ("phone", "role", "tenant"))
    and _model_has_fields(TenantModel, ("name", "address", "phone", "currency", "timezone"))
):

    class BaseUserFactory(DjangoModelFactory):
        """User uchun umumiy factory bazasi."""

        class Meta:
            model = UserModel
            abstract = True
            skip_postgeneration_save = True

        phone = factory.Sequence(_default_phone)
        full_name = factory.Sequence(lambda n: f"Foydalanuvchi {n + 1}")
        role = UserRole.EMPLOYEE
        tenant = factory.SubFactory(TenantFactory)
        is_active = True

        @factory.post_generation
        def password(self, create: bool, extracted: str | None, **kwargs: Any) -> None:
            if not create:
                return
            raw_password = extracted or "password123"
            if hasattr(self, "set_password"):
                self.set_password(raw_password)
                self.save(update_fields=["password"])

    class UserFactory(BaseUserFactory):
        """User uchun konkret factory."""

        class Meta:
            model = UserModel

else:

    class BaseUserFactory:
        """User uchun fallback factory."""

        @classmethod
        def build(cls, **kwargs: Any) -> SimpleNamespace:
            tenant = kwargs.pop("tenant", None) or TenantFactory.build()
            payload = {
                "phone": _default_phone(2),
                "full_name": "Foydalanuvchi 1",
                "role": UserRole.EMPLOYEE,
                "tenant": tenant,
                "is_active": True,
                "is_authenticated": True,
                "is_staff": False,
                "is_superuser": False,
            }
            payload.update(kwargs)
            payload.setdefault("pk", uuid.uuid4())
            payload.setdefault("id", payload["pk"])
            return _fallback_namespace("User", **payload)

        create = build

    UserFactory = BaseUserFactory


class EmployeeFactory(UserFactory):
    """Xodim foydalanuvchi factory'si."""

    @classmethod
    def build(cls, **kwargs: Any) -> Any:
        kwargs.setdefault("role", UserRole.EMPLOYEE)
        return super().build(**kwargs)

    @classmethod
    def create(cls, **kwargs: Any) -> Any:
        kwargs.setdefault("role", UserRole.EMPLOYEE)
        return super().create(**kwargs)


class ManagerFactory(UserFactory):
    """Menejer foydalanuvchi factory'si."""

    @classmethod
    def build(cls, **kwargs: Any) -> Any:
        kwargs.setdefault("role", UserRole.MANAGER)
        kwargs.setdefault("is_staff", True)
        return super().build(**kwargs)

    @classmethod
    def create(cls, **kwargs: Any) -> Any:
        kwargs.setdefault("role", UserRole.MANAGER)
        kwargs.setdefault("is_staff", True)
        return super().create(**kwargs)


class AdminFactory(UserFactory):
    """Admin foydalanuvchi factory'si."""

    @classmethod
    def build(cls, **kwargs: Any) -> Any:
        kwargs.setdefault("role", UserRole.ADMIN)
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return super().build(**kwargs)

    @classmethod
    def create(cls, **kwargs: Any) -> Any:
        kwargs.setdefault("role", UserRole.ADMIN)
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return super().create(**kwargs)


__all__ = [
    "AdminFactory",
    "BaseTenantFactory",
    "BaseUserFactory",
    "EmployeeFactory",
    "ManagerFactory",
    "TenantFactory",
    "UserFactory",
]
