from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    """Order'ni Conversation ga bog'lovchi migratsiya.

    Alohida migration qilindi — chat ilovasi 0001 migration'ida allaqachon
    orders.0001 ga bog'langan; aylana (circular dependency) oldini olish uchun
    Order.conversation FK alohida qo'shiladi (TZ 3.6, 7.1).
    """

    dependencies = [
        ("orders", "0001_initial"),
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="conversation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="orders",
                to="chat.conversation",
                verbose_name="Suhbat",
            ),
        ),
    ]