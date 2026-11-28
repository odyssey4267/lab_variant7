"""Проверка SQL-скриптов: создаёт базу в памяти, заполняет её и показывает содержимое.

Запуск: python tools/db_check.py
"""

import sqlite3
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

QUERIES = (
    ("Матрицы и их теги",
     "SELECT m.id, m.name, m.n_rows, m.n_cols, group_concat(t.name, ', ') "
     "FROM matrix m LEFT JOIN matrix_tag mt ON mt.matrix_id = m.id "
     "LEFT JOIN tag t ON t.id = mt.tag_id GROUP BY m.id ORDER BY m.id"),
    ("Столбцы матрицы example1 (id=1): нули в столбце",
     "SELECT col_idx, SUM(value <> 0) AS ненулевых FROM matrix_cell "
     "WHERE matrix_id = 1 GROUP BY col_idx ORDER BY col_idx"),
    ("Сохранённый анализ матрицы 1: вектор zero_columns",
     "SELECT position, value FROM vector_result "
     "WHERE analysis_id = 1 AND kind = 'zero_columns' ORDER BY position"),
)


def main() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
    conn.executescript((SQL_DIR / "seed.sql").read_text(encoding="utf-8"))
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name")]
    print("Таблицы:", ", ".join(tables))
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} строк")
    for title, query in QUERIES:
        print(f"\n{title}")
        for row in conn.execute(query):
            print("  ", row)
    conn.execute("DELETE FROM matrix WHERE id = 1")
    left = conn.execute("SELECT COUNT(*) FROM matrix_cell WHERE matrix_id = 1").fetchone()[0]
    print(f"\nПосле удаления матрицы 1 осталось её ячеек: {left} (каскадное удаление)")


if __name__ == "__main__":
    main()
