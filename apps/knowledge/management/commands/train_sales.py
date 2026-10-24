from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.knowledge.services import (
    apply_sales_pack,
    load_sales_pack,
    preview_sales_pack,
    rollback_sales_pack,
)


class Command(BaseCommand):
    help = "Parda sotuv bilimlarini tekshiradi; --apply va snapshot bilan joriy qiladi"

    def add_arguments(self, parser: Any) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--apply", action="store_true")
        group.add_argument("--rollback", type=Path)
        parser.add_argument("--snapshot", type=Path)
        parser.add_argument("--author-id")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            if not options["apply"] and not options["rollback"]:
                summary = preview_sales_pack(load_sales_pack())
                summary["dry_run"] = True
            else:
                authors = User.objects.filter(role="admin", is_active=True)
                if options["author_id"]:
                    authors = authors.filter(pk=options["author_id"])
                author = authors.order_by("pk").first()
                if author is None:
                    raise CommandError("Joriy qilish uchun faol admin muallif kerak")
                if options["rollback"]:
                    summary = rollback_sales_pack(options["rollback"], author=author)
                else:
                    if options["snapshot"] is None:
                        raise CommandError("--apply uchun --snapshot yo'li kerak")
                    summary = apply_sales_pack(
                        load_sales_pack(), author=author, snapshot_path=options["snapshot"]
                    )
        except (ValidationError, OSError, ValueError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(summary, ensure_ascii=False))
