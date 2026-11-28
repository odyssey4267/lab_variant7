"""Создание таблиц в базе данных (уровни 1–2, без миграций): python src/db_init.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matrix_lab.db.session import init_db, make_engine  # noqa: E402


def main() -> None:
    engine = make_engine()
    init_db(engine)
    print("Таблицы созданы:", engine.url)


if __name__ == "__main__":
    main()
