"""Sotuvchi yordamchisini haqiqiy API orqali takrorlanadigan suhbatlarda tekshiradi."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", nargs="*")
    options = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.accounts.models import User

    user = User.objects.get(pk=options.user_id)
    if user.role != "employee":
        parser.error("Baholash oddiy employee hisobida bajarilishi kerak")
    token = str(RefreshToken.for_user(user).access_token)
    source = Path("docs/sales-training/behavior-v2/scenarios.json")
    scenarios = json.loads(source.read_text())
    existing = (
        [json.loads(line) for line in options.output.read_text().splitlines()]
        if options.output.exists()
        else []
    )

    def request(path: str, payload: dict[str, Any]) -> Any:
        return urllib.request.urlopen(
            urllib.request.Request(
                "http://127.0.0.1:8000/api/v1/" + path,
                data=json.dumps(payload).encode(),
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            ),
            timeout=150,
        )

    for scenario in scenarios:
        if options.only and scenario["id"] not in options.only:
            continue
        previous = [row for row in existing if row["scenario"] == scenario["id"]]
        if len(previous) >= len(scenario["messages"]):
            continue
        if previous:
            cid = previous[-1]["conversation_id"]
        else:
            with request(
                "conversations/", {"mode": "seller", "title": "BEHAVIOR-V2 " + scenario["id"]}
            ) as response:
                cid = json.load(response)["id"]
        for turn, message in enumerate(scenario["messages"], 1):
            if turn <= len(previous):
                continue
            row: dict[str, Any] = {
                "scenario": scenario["id"],
                "group": scenario["group"],
                "turn": turn,
                "conversation_id": cid,
                "input": message,
                "events": [],
                "answer": "",
            }
            started = time.monotonic()
            try:
                with request(f"conversations/{cid}/messages/", {"content": message}) as response:
                    for raw in response:
                        line = raw.decode().strip()
                        if not line.startswith("data:"):
                            continue
                        event = json.loads(line[5:].strip())
                        if event.get("kind") == "content":
                            row["answer"] += event.get("content", "")
                        else:
                            row["events"].append(event)
            except (OSError, ValueError) as error:
                row["exception"] = str(error)
            row["seconds"] = round(time.monotonic() - started, 2)
            with options.output.open("a") as output:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
            progress = {k: row[k] for k in ("scenario", "turn", "answer")}
            sys.stdout.write(json.dumps(progress, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            if not row["answer"]:
                raise SystemExit("Bo'sh javob: texnik holatni tekshirib keyin davom eting")


if __name__ == "__main__":
    main()
