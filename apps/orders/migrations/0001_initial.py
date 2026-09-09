from __future__ import annotations

import uuid

import django.db.models.expressions
from django.db import migrations, models

import apps.common.choices


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        # Buyurtma raqami DB sequence'idan olinadi — parallel yozuvlarda ham
        # takrorlanmaydi (TZ 8.2, poyga holatisiz).
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS orders_order_number_seq AS bigint START WITH 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS orders_order_number_seq;",
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Yaratildi")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilandi")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Faol")),
                ("number", models.CharField(db_index=True, max_length=20, unique=True, verbose_name="Raqam")),
                (
                    "number_seq",
                    models.PositiveBigIntegerField(
                        db_default=django.db.models.expressions.Func(
                            django.db.models.expressions.Value("orders_order_number_seq"),
                            function="nextval",
                            output_field=models.PositiveBigIntegerField(),
                        ),
                        db_index=True,
                        editable=False,
                        unique=True,
                        verbose_name="Tartib raqami",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="orders",
                        to="accounts.user",
                        verbose_name="Sotuvchi",
                    ),
                ),
                ("customer_name", models.CharField(max_length=255, verbose_name="Mijoz ismi")),
                ("customer_phone", models.CharField(max_length=20, verbose_name="Mijoz telefoni")),
                ("address", models.TextField(blank=True, verbose_name="Manzil")),
                (
                    "status",
                    models.CharField(
                        choices=apps.common.choices.OrderStatus.choices,
                        db_index=True,
                        default="draft",
                        max_length=20,
                        verbose_name="Holat",
                    ),
                ),
                ("subtotal", models.DecimalField(decimal_places=2, default="0.00", max_digits=14, verbose_name="Yakuniy summa")),
                ("discount_percent", models.DecimalField(decimal_places=2, default="0.00", max_digits=5, verbose_name="Chegirma foizi")),
                ("discount_amount", models.DecimalField(decimal_places=2, default="0.00", max_digits=14, verbose_name="Chegirma summasi")),
                (
                    "discount_source",
                    models.CharField(
                        choices=[("tier", "Bosqich bo'yicha"), ("manual", "Qo'lda")],
                        default="tier",
                        max_length=10,
                        verbose_name="Chegirma manbai",
                    ),
                ),
                ("delivery_amount", models.DecimalField(decimal_places=2, default="0.00", max_digits=14, verbose_name="Yetkazish narxi")),
                ("total", models.DecimalField(decimal_places=2, default="0.00", max_digits=14, verbose_name="Jami")),
                ("prepayment_percent", models.DecimalField(decimal_places=2, default="0.00", max_digits=5, verbose_name="Avans foizi")),
                ("prepayment", models.DecimalField(decimal_places=2, default="0.00", max_digits=14, verbose_name="Avans summasi")),
                ("balance", models.DecimalField(decimal_places=2, default="0.00", max_digits=14, verbose_name="Qoldiq")),
                (
                    "payment_status",
                    models.CharField(
                        choices=apps.common.choices.PaymentStatus.choices,
                        db_index=True,
                        default="unpaid",
                        max_length=20,
                        verbose_name="To'lov holati",
                    ),
                ),
                ("deadline_date", models.DateField(blank=True, null=True, verbose_name="Muddat")),
                ("note", models.TextField(blank=True, verbose_name="Izoh")),
                (
                    "confirmed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="confirmed_orders",
                        to="accounts.user",
                        verbose_name="Tasdiqlagan",
                    ),
                ),
                ("confirmed_at", models.DateTimeField(blank=True, null=True, verbose_name="Tasdiqlangan vaqt")),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="%(class)s_set",
                        db_index=True,
                        to="accounts.tenant",
                        verbose_name="Ijarachi",
                    ),
                ),
            ],
            options={
                "verbose_name": "Buyurtma",
                "verbose_name_plural": "Buyurtmalar",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="OrderMeasurement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Yaratildi")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilandi")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Faol")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="measurements",
                        to="orders.order",
                        verbose_name="Buyurtma",
                    ),
                ),
                ("room_name", models.CharField(max_length=255, verbose_name="Xona nomi")),
                ("cornice_length_m", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Karniz uzunligi (m)")),
                ("height_m", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Balandlik (m)")),
                ("layers", models.JSONField(blank=True, default=list, verbose_name="Qatlamlar")),
                ("coefficient", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Burma koeffitsienti")),
                ("note", models.TextField(blank=True, verbose_name="Izoh")),
            ],
            options={
                "verbose_name": "Buyurtma o'lchovi",
                "verbose_name_plural": "Buyurtma o'lchovlari",
            },
        ),
        migrations.CreateModel(
            name="OrderCurtainPart",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Yaratildi")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilandi")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Faol")),
                (
                    "measurement",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="parts",
                        to="orders.ordermeasurement",
                        verbose_name="O'lchov",
                    ),
                ),
                (
                    "variant",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="order_parts",
                        to="catalog.productvariant",
                        verbose_name="Variant",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=apps.common.choices.CurtainPartRole.choices,
                        max_length=20,
                        verbose_name="Rol",
                    ),
                ),
                ("width_m", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Kenglik (m)")),
                ("height_m", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Balandlik (m)")),
                ("coefficient", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Burma koeffitsienti")),
                ("area_sqm", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Yuza (m²)")),
                ("price_per_sqm", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="1 m² narxi")),
                ("total", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Summa")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Tartib")),
            ],
            options={
                "verbose_name": "Buyurtma parda bo'lagi",
                "verbose_name_plural": "Buyurtma parda bo'laklari",
                "ordering": ("sort_order",),
            },
        ),
        migrations.CreateModel(
            name="OrderAccessory",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Yaratildi")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilandi")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Faol")),
                (
                    "measurement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="accessories",
                        to="orders.ordermeasurement",
                        verbose_name="O'lchov",
                    ),
                ),
                (
                    "variant",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="order_accessories",
                        to="catalog.productvariant",
                        verbose_name="Variant",
                    ),
                ),
                ("qty", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Miqdor")),
                (
                    "unit",
                    models.CharField(
                        choices=apps.common.choices.PriceUnit.choices,
                        max_length=20,
                        verbose_name="Birlik",
                    ),
                ),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Bir birlik narxi")),
                ("total", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Summa")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Tartib")),
            ],
            options={
                "verbose_name": "Buyurtma aksessuari",
                "verbose_name_plural": "Buyurtma aksessuarlari",
                "ordering": ("sort_order",),
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Yaratildi")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilandi")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Faol")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="items",
                        to="orders.order",
                        verbose_name="Buyurtma",
                    ),
                ),
                (
                    "measurement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="service_items",
                        to="orders.ordermeasurement",
                        verbose_name="O'lchov",
                    ),
                ),
                ("service_key", models.CharField(max_length=64, verbose_name="Xizmat kaliti")),
                ("name_snapshot", models.CharField(max_length=255, verbose_name="Nomi (snapshot)")),
                ("qty", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Miqdor")),
                (
                    "unit",
                    models.CharField(
                        choices=apps.common.choices.PriceUnit.choices,
                        max_length=20,
                        verbose_name="Birlik",
                    ),
                ),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Bir birlik narxi")),
                ("total", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Summa")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Tartib")),
            ],
            options={
                "verbose_name": "Buyurtma xizmati",
                "verbose_name_plural": "Buyurtma xizmatlari",
                "ordering": ("sort_order",),
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["number"], name="orders_orde_number_idx"),
        ),
    ]