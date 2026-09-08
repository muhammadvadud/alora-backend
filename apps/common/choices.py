"""Loyiha bo'ylab ishlatiladigan TextChoices to'plamlari."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    """Foydalanuvchi rollari."""

    EMPLOYEE = "employee", _("Xodim")
    MANAGER = "manager", _("Boshqaruvchi")
    ADMIN = "admin", _("Administrator")


class PriceUnit(models.TextChoices):
    """Narx o'lchov birliklari."""

    PER_SQM = "per_sqm", _("m² bo'yicha")
    PER_PIECE = "per_piece", _("dona bo'yicha")
    PER_METER = "per_meter", _("metr bo'yicha")


class CurtainPartRole(models.TextChoices):
    """Parda bo'laklari rollari."""

    PORTYERA = "portyera", _("Portyera")
    TUL = "tul", _("Tul")
    LAMBREKAN = "lambrekan", _("Lambrekan")
    KANT = "kant", _("Kant")
    DEKOR = "dekor", _("Dekor")
    ASTAR = "astar", _("Astar")


class OrderStatus(models.TextChoices):
    """Buyurtma holatlari."""

    DRAFT = "draft", _("Qoralama")
    CONFIRMED = "confirmed", _("Tasdiqlangan")
    MEASURING = "measuring", _("O'lchov olinmoqda")
    PRODUCTION = "production", _("Ishlab chiqarish")
    READY = "ready", _("Tayyor")
    INSTALLING = "installing", _("O'rnatilmoqda")
    COMPLETED = "completed", _("Yakunlangan")
    CANCELLED = "cancelled", _("Bekor qilingan")


class PaymentStatus(models.TextChoices):
    """To'lov holatlari."""

    UNPAID = "unpaid", _("To'lanmagan")
    PREPAID = "prepaid", _("Avans berilgan")
    PAID = "paid", _("To'langan")


class ConversationStage(models.TextChoices):
    """Suhbat bosqichlari."""

    NEED = "need", _("Ehtiyoj")
    RECOMMEND = "recommend", _("Tavsiya")
    MEASURE = "measure", _("O'lchov")
    CALC = "calc", _("Hisob")
    VARIANTS = "variants", _("Variantlar")
    ORDER = "order", _("Buyurtma")


class ConversationMode(models.TextChoices):
    """Suhbat rejimlari."""

    SELLER = "seller", _("Sotuvchi")
    CUSTOMER = "customer", _("Mijoz")


class MessageRole(models.TextChoices):
    """Xabar rollari."""

    USER = "user", _("Foydalanuvchi")
    ASSISTANT = "assistant", _("Yordamchi")
    TOOL = "tool", _("Asbob")
    SYSTEM = "system", _("Tizim")


class UsagePeriod(models.TextChoices):
    """Statistika davrlari."""

    DAILY = "daily", _("Kunlik")
    MONTHLY = "monthly", _("Oylik")


class OnExceed(models.TextChoices):
    """Limit oshgandagi xatti-harakatlar."""

    WARN = "warn", _("Ogohlantirish")
    BLOCK = "block", _("Bloklash")


class ProductSegment(models.TextChoices):
    """Mahsulot segmentlari."""

    ECONOMY = "economy", _("Ekonom")
    STANDARD = "standard", _("Standart")
    PREMIUM = "premium", _("Premium")


