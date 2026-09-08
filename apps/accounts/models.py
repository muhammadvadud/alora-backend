"""Accounts modellar."""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel
from apps.common.choices import UserRole


class Tenant(BaseModel):
    name = models.CharField(max_length=255, verbose_name=_("Nomi"))
    address = models.TextField(blank=True, verbose_name=_("Manzili"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Telefon"))
    currency = models.CharField(max_length=10, default="UZS", verbose_name=_("Valyuta"))
    timezone = models.CharField(max_length=50, default="Asia/Tashkent", verbose_name=_("Vaqt mintaqasi"))

    class Meta:
        verbose_name = _("Ijarachi (Tenant)")
        verbose_name_plural = _("Ijarachilar (Tenants)")

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, phone: str, password: str | None = None, **extra_fields) -> "User":
        if not phone:
            raise ValueError(_("Telefon raqami kiritilishi shart"))
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser is_staff=True bo'lishi kerak.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi kerak.")

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    phone = models.CharField(max_length=20, unique=True, verbose_name=_("Telefon"))
    full_name = models.CharField(max_length=255, verbose_name=_("To'liq ism"))
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE,
        verbose_name=_("Rol"),
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
        verbose_name=_("Ijarachi"),
    )
    is_staff = models.BooleanField(default=False, verbose_name=_("Xodim (Staff)"))
    device_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Qurilma ID"))

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone})"
