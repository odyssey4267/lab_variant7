"""Показать структуру и данные базы SQLite в терминале (вместо DB Browser).

Запуск: python tools/db_dump.py [файл_базы] [таблица]
Без аргументов берётся matrix_lab.db в текущей папке и показываются все таблицы.
"""

import sqlite3
import sys
from pathlib import Path

LIMIT = 5  # сколько строк каждой таблицы показывать


def show_table(conn: sqlite3.Connection, name: str) -> None:
    columns = conn.execute(f"PRAGMA table_info({name})").fetchall()
    keys = {row[3]: row[2] for row in conn.execute(f"PRAGMA foreign_key_list({name})")}
    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"\n=== {name}  (строк: {count}) ===")
    for _cid, col, ctype, notnull, _default, pk in columns:
        marks = []
        if pk:
            marks.append("PK")
        if col in keys:
            marks.append(f"FK -> {keys[col]}")
        if notnull and not pk:
            marks.append("NOT NULL")
        print(f"  {col:<12} {ctype:<14} {' '.join(marks)}")
    rows = conn.execute(f"SELECT * FROM {name} LIMIT {LIMIT}").fetchall()
    if rows:
        print("  данные:", [c[1] for c in columns])
        for row in rows:
            print("   ", row)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "matrix_lab.db")
    if not path.exists():
        sys.exit(f"Файл {path} не найден. Создайте базу: python src/db_init.py")
    conn = sqlite3.connect(path)
    only = sys.argv[2] if len(sys.argv) > 2 else None
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name")]
    print("База:", path, "| таблицы:", ", ".join(names))
    for name in names:
        if only is None or only == name:
            show_table(conn, name)


if __name__ == "__main__":
    main()
