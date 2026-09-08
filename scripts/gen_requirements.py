"""requirements.txt va requirements-dev.txt ni pyproject.toml dan generatsiya qiladi.

Ishlatilishi:
    .venv/bin/python scripts/gen_requirements.py

Versiyalar joriy virtualenv'da o'rnatilgan holatga qadaladi (pin qilinadi).
Bog'liqlik qo'shish yoki o'chirish FAQAT pyproject.toml orqali bo'ladi —
requirements fayllari qo'lda tahrirlanmaydi.
"""

from __future__ import annotations

import importlib.metadata as md
import re
import tomllib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

HEADER = (
    "# Bu fayl pyproject.toml dan generatsiya qilinadi — QO'LDA TAHRIRLANMAYDI.\n"
    "# Yangilash: .venv/bin/python scripts/gen_requirements.py\n"
    "# Manba (source of truth): pyproject.toml\n\n"
)


def pin(spec: str) -> str:
    """Bog'liqlikni o'rnatilgan versiyaga qadaydi."""

    name = re.split(r"[<>=!\[; ]", spec.strip(), maxsplit=1)[0]
    try:
        return f"{name}=={md.version(name)}"
    except md.PackageNotFoundError:
        # Muhitda o'rnatilmagan bo'lsa pyproject'dagi holicha qoldiriladi
        return spec.strip()


def main() -> None:
    """Ikkala requirements faylini yozadi."""

    data = tomllib.loads((BASE_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    runtime = project.get("dependencies", [])
    dev = project.get("optional-dependencies", {}).get("dev", [])

    (BASE_DIR / "requirements.txt").write_text(
        HEADER + "\n".join(pin(item) for item in runtime) + "\n", encoding="utf-8"
    )
    (BASE_DIR / "requirements-dev.txt").write_text(
        HEADER + "-r requirements.txt\n\n" + "\n".join(pin(item) for item in dev) + "\n",
        encoding="utf-8",
    )
    print(f"requirements.txt: {len(runtime)} ta, requirements-dev.txt: {len(dev)} ta")


if __name__ == "__main__":
    main()
