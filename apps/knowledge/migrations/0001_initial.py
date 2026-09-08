from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="KnowledgeRule",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Yaratildi")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilandi")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Faol")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("room_style", "Xona va uslub"),
                            ("light", "Yorug'lik"),
                            ("color", "Rang"),
                            ("construction", "Konstruktsiya"),
                            ("objection", "E'tiroz"),
                            ("general", "Umumiy"),
                        ],
                        db_index=True,
                        max_length=32,
                        verbose_name="Turi",
                    ),
                ),
                ("condition", models.JSONField(blank=True, default=dict, verbose_name="Shart")),
                ("recommendation", models.TextField(verbose_name="Tavsiya")),
                ("priority", models.PositiveIntegerField(db_index=True, default=0, verbose_name="Ustuvorlik")),
            ],
            options={
                "verbose_name": "Bilim qoidasi",
                "verbose_name_plural": "Bilim qoidalari",
                "ordering": ("-priority", "-created_at"),
            },
        ),
    ]
