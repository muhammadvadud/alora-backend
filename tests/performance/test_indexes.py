"""14.9 — DB indekslarini `EXPLAIN` bilan tekshirish.

Nega `enable_seqscan = off` ishlatiladi: test bazasida jadvallar bo'sh yoki juda
kichik bo'ladi, shuning uchun PostgreSQL rejalashtiruvchisi indeks mavjud bo'lsa
ham `Seq Scan` ni tanlaydi — bu 0 qatorli jadvalda haqiqatan arzonroq. Natijada
"Seq Scan bor" degan tekshiruv indeks yo'qligini emas, jadval kichikligini
ko'rsatadi (va bir xil kodda ham o'tadi, ham yiqiladi).

`enable_seqscan = off` rejalashtiruvchini indeksdan foydalanishga majbur qiladi:
indeks bor bo'lsa — `Index Scan` tanlanadi; indeks YO'Q bo'lsa — boshqa yo'l
qolmagani uchun `Seq Scan` qaytadi. Shunda tekshiruv aynan indeks mavjudligini
o'lchaydi. Qo'shimcha kafolat sifatida `pg_indexes` ham tekshiriladi.
"""

from __future__ import annotations

import uuid

import pytest
from django.db import connection

from apps.catalog.models import ProductVariant
from apps.chat.models import Conversation, Message
from apps.orders.models import Order
from apps.usage.models import UsageDaily

#: Indeksdan foydalanilganini bildiruvchi reja tugunlari.
INDEX_NODES = ("Index Scan", "Index Only Scan", "Bitmap Index Scan", "Bitmap Heap Scan")


def explain(queryset) -> str:
    """Queryset uchun `EXPLAIN` rejasini bitta satr ko'rinishida qaytaradi."""

    compiler = queryset.query.get_compiler(using=queryset.db)
    sql, params = compiler.as_sql()
    with connection.cursor() as cursor:
        # Faqat shu tranzaksiya uchun — test tugagach o'z holiga qaytadi.
        cursor.execute("SET LOCAL enable_seqscan = off")
        cursor.execute(f"EXPLAIN {sql}", params)
        return " ".join(row[0] for row in cursor.fetchall())


def table_indexes(table_name: str) -> list[str]:
    """Jadval uchun `pg_indexes` dan indeks ta'riflarini qaytaradi."""

    with connection.cursor() as cursor:
        cursor.execute("SELECT indexdef FROM pg_indexes WHERE tablename = %s", [table_name])
        return [row[0] for row in cursor.fetchall()]


@pytest.mark.django_db
class TestDatabaseIndexes:
    """Muhim qidiruv maydonlari indeks orqali o'qilishini tekshiradi."""

    def _assert_uses_index(self, queryset, column_hint: str) -> None:
        """Reja indeksdan foydalanayotganini tasdiqlaydi."""

        plan = explain(queryset)
        assert any(node in plan for node in INDEX_NODES), (
            f"{column_hint} indeks orqali o'qilmayapti. EXPLAIN rejasi: {plan}"
        )

    def test_order_number_index(self):
        """`Order.number` — buyurtmani raqami bo'yicha topish."""

        self._assert_uses_index(Order.objects.filter(number="ALR-2026-000123"), "Order.number")
        assert any("number" in definition for definition in table_indexes("orders_order")), (
            "orders_order jadvalida number ustuni uchun indeks yo'q"
        )

    def test_message_conversation_created_at_index(self):
        """`Message(conversation, created_at)` — suhbat xabarlarini tartib bilan o'qish."""

        queryset = Message.objects.filter(conversation_id=uuid.uuid4()).order_by("created_at")
        self._assert_uses_index(queryset, "Message.conversation + created_at")

    def test_conversation_session_id_index(self):
        """`Conversation.session_id` — sessiya bo'yicha suhbat topish."""

        self._assert_uses_index(
            Conversation.objects.filter(session_id="dummy-session"), "Conversation.session_id"
        )

    def test_product_variant_sku_index(self):
        """`ProductVariant.sku` — SKU bo'yicha variant topish."""

        self._assert_uses_index(ProductVariant.objects.filter(sku="SKU-123"), "ProductVariant.sku")

    def test_usage_daily_user_date_index(self):
        """`UsageDaily(user, date)` — kunlik yig'mani o'qish."""

        queryset = UsageDaily.objects.filter(user_id=uuid.uuid4(), date="2026-01-01")
        self._assert_uses_index(queryset, "UsageDaily.user + date")
