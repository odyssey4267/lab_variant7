"""Выгрузка описания API в docs/openapi.json (можно импортировать в Postman).

Запуск: python tools/export_openapi.py
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from matrix_lab.api import create_app  # noqa: E402
from matrix_lab.db.session import make_engine  # noqa: E402


def main() -> None:
    os.environ.setdefault("DATABASE_URL", "sqlite://")
    app = create_app(make_engine("sqlite://"))
    target = ROOT / "docs" / "openapi.json"
    target.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print("Записано:", target)


if __name__ == "__main__":
    main()
