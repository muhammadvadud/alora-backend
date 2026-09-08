from __future__ import annotations

import uuid

from django.db import migrations, models

import apps.common.choices


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="CalcRule",
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
                ("key", models.CharField(max_length=64, unique=True, verbose_name="Kalit")),
                ("value", models.DecimalField(decimal_places=3, max_digits=8, verbose_name="Qiymat")),
                ("unit", models.CharField(max_length=32, verbose_name="Birlik")),
                ("description", models.TextField(blank=True, verbose_name="Izoh")),
                ("applies_to", models.JSONField(blank=True, default=dict, verbose_name="Qo'llanish sharti")),
            ],
            options={
                "verbose_name": "Hisob qoidasi",
                "verbose_name_plural": "Hisob qoidalari",
                "ordering": ("key",),
            },
        ),
        migrations.CreateModel(
            name="DiscountPolicy",
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
                    "manual_max_percent_employee",
                    models.DecimalField(decimal_places=2, max_digits=5, verbose_name="Xodim uchun maksimal qo'lda chegirma"),
                ),
                (
                    "manual_max_percent_manager",
                    models.DecimalField(decimal_places=2, max_digits=5, verbose_name="Menejer uchun maksimal qo'lda chegirma"),
                ),
                (
                    "stack_with_tier",
                    models.BooleanField(default=True, verbose_name="Bosqichli chegirma bilan qo'shiladi"),
                ),
            ],
            options={
                "verbose_name": "Chegirma siyosati",
                "verbose_name_plural": "Chegirma siyosati",
            },
        ),
        migrations.CreateModel(
            name="DiscountTier",
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
                ("min_amount", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Minimal summa")),
                ("percent", models.DecimalField(decimal_places=2, max_digits=5, verbose_name="Foiz")),
            ],
            options={
                "verbose_name": "Chegirma bosqichi",
                "verbose_name_plural": "Chegirma bosqichlari",
                "ordering": ("min_amount",),
            },
        ),
        migrations.CreateModel(
            name="ModelPricing",
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
                ("provider", models.CharField(max_length=64, verbose_name="Provayder")),
                ("model", models.CharField(max_length=128, verbose_name="Model")),
                ("input_per_1m", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Kirish narxi / 1M")),
                ("output_per_1m", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Chiqish narxi / 1M")),
                (
                    "cached_input_per_1m",
                    models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Kesh kirish narxi / 1M"),
                ),
                ("stt_per_minute", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="STT narxi / daqiqa")),
                ("tts_per_1k_chars", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="TTS narxi / 1K belgi")),
                ("usd_to_uzs", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="USD/UZS kursi")),
            ],
            options={
                "verbose_name": "Model narxlari",
                "verbose_name_plural": "Model narxlari",
                "ordering": ("provider", "model"),
            },
        ),
        migrations.CreateModel(
            name="OrderDefaults",
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
                ("prepayment_percent", models.DecimalField(decimal_places=2, max_digits=5, verbose_name="Avans foizi")),
                ("delivery_amount", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Yetkazish narxi")),
                ("deadline_days", models.PositiveIntegerField(verbose_name="Muddat (kun)")),
            ],
            options={
                "verbose_name": "Buyurtma sozlamalari",
                "verbose_name_plural": "Buyurtma sozlamalari",
            },
        ),
        migrations.CreateModel(
            name="ServicePrice",
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
                ("key", models.CharField(max_length=64, unique=True, verbose_name="Kalit")),
                ("name", models.CharField(max_length=255, verbose_name="Nomi")),
                ("price", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Narx")),
                (
                    "unit",
                    models.CharField(
                        choices=apps.common.choices.PriceUnit.choices, max_length=20, verbose_name="Birlik"
                    ),
                ),
            ],
            options={
                "verbose_name": "Xizmat narxi",
                "verbose_name_plural": "Xizmat narxlari",
                "ordering": ("key",),
            },
        ),
        migrations.AddConstraint(
            model_name="modelpricing",
            constraint=models.UniqueConstraint(
                fields=("provider", "model"), name="pricing_modelpricing_provider_model_uniq"
            ),
        ),
    ]

