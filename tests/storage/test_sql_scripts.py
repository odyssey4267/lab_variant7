"""Тесты SQL-скриптов sql/schema.sql и sql/seed.sql (стандартный модуль sqlite3)."""

import sqlite3
from pathlib import Path

import pytest

SQL = Path(__file__).resolve().parents[2] / "sql"


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript((SQL / "schema.sql").read_text(encoding="utf-8"))
    yield connection
    connection.close()


def seed(conn):
    conn.executescript((SQL / "seed.sql").read_text(encoding="utf-8"))


def scalar(conn, query):
    return conn.execute(query).fetchone()[0]


def test_schema_creates_all_tables(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"matrix", "matrix_cell", "tag", "matrix_tag", "analysis", "vector_result",
            "setting"} <= names


def test_seed_fills_tables(conn):
    seed(conn)
    assert scalar(conn, "SELECT COUNT(*) FROM matrix") == 2
    assert scalar(conn, "SELECT COUNT(*) FROM matrix_cell") == 12


def test_cascade_delete(conn):
    seed(conn)
    conn.execute("DELETE FROM matrix WHERE id = 1")
    assert scalar(conn, "SELECT COUNT(*) FROM matrix_cell WHERE matrix_id = 1") == 0
    assert scalar(conn, "SELECT COUNT(*) FROM vector_result") == 0


@pytest.mark.parametrize("statement", [
    "INSERT INTO matrix (name, n_rows, n_cols) VALUES ('x', 0, 1)",          # n_rows >= 1
    "INSERT INTO matrix (name, n_rows, n_cols) VALUES ('x', 1, 0)",          # n_cols >= 1
    "INSERT INTO matrix (name, n_rows, n_cols) VALUES (NULL, 1, 1)",         # NOT NULL
    "INSERT INTO matrix_cell (matrix_id, row_idx, col_idx, value) VALUES (99, 0, 0, 1)",
    "INSERT INTO matrix (name, n_rows, n_cols) VALUES ('example1', 1, 1)",   # UNIQUE (после seed)
    "INSERT INTO vector_result (analysis_id, kind, position, value) VALUES (1, 'bad', 0, 1)",
])
def test_constraints_reject_bad_rows(conn, statement):
    seed(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(statement)


def test_cell_position_is_unique(conn):
    seed(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO matrix_cell (matrix_id, row_idx, col_idx, value) "
                     "VALUES (1, 0, 0, 5)")
