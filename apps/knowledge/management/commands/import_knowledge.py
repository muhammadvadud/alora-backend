"""JSON fayldan bilim qoidalarini import qiladi (idempotent).

Foydalanish: manage.py import_knowledge <fayl.json> [--replace]
Fayl: [{"kind","priority","condition","recommendation"}, ...]
Bir xil (kind, recommendation) juftligi qayta yaratilmaydi; --replace bo'lsa
condition/priority yangilanadi.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.knowledge.models import KnowledgeRule


class Command(BaseCommand):
    help = "JSON fayldan KnowledgeRule yozuvlarini import qiladi"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("path", help="JSON fayl yo'li")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Mavjud qoidaning condition/priority'sini yangilash",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Fayl topilmadi: {path}")
        rules = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rules, list):
            raise CommandError("JSON ro'yxat bo'lishi kerak")

        valid_kinds = {choice for choice, _ in KnowledgeRule.Kind.choices}
        created = updated = skipped = 0
        with transaction.atomic():
            for i, item in enumerate(rules):
                kind = item.get("kind")
                text = (item.get("recommendation") or "").strip()
                if kind not in valid_kinds or not text:
                    raise CommandError(f"#{i}: kind={kind!r} yoki recommendation noto'g'ri")
                condition = item.get("condition") or {}
                priority = int(item.get("priority", 0))
                rule = KnowledgeRule.objects.filter(kind=kind, recommendation=text).first()
                if rule is None:
                    KnowledgeRule.objects.create(
                        kind=kind, condition=condition, priority=priority, recommendation=text
                    )
                    created += 1
                elif options["replace"] and (
                    rule.condition != condition or rule.priority != priority
                ):
                    rule.condition = condition
                    rule.priority = priority
                    rule.save(update_fields=["condition", "priority", "updated_at"])
                    updated += 1
                else:
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"yaratildi={created} yangilandi={updated} o'tkazildi={skipped}")
        )
