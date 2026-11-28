"""Тесты миграций Alembic: применение, откат и работа репозитория на мигрированной базе."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from matrix_lab.db import repository as repo
from matrix_lab.db.session import make_engine, make_session_factory

ROOT = Path(__file__).resolve().parents[2]
TABLES = {"matrix", "matrix_cell", "tag", "matrix_tag", "analysis", "vector_result", "setting"}


@pytest.fixture
def db(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    return cfg, url


def tables(url):
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def matrix_columns(url):
    engine = create_engine(url)
    try:
        return {c["name"] for c in inspect(engine).get_columns("matrix")}
    finally:
        engine.dispose()


def test_upgrade_head_creates_schema(db):
    cfg, url = db
    command.upgrade(cfg, "head")
    assert TABLES | {"alembic_version"} <= tables(url)
    assert "note" in matrix_columns(url)


def test_upgrade_to_first_revision_has_no_note(db):
    cfg, url = db
    command.upgrade(cfg, "0001")
    assert "note" not in matrix_columns(url)


def test_downgrade_one_step_removes_note(db):
    cfg, url = db
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")
    cols = matrix_columns(url)
    assert "note" not in cols and "name" in cols


def test_downgrade_to_base_removes_tables(db):
    cfg, url = db
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    assert not (TABLES & tables(url))


def test_upgrade_is_repeatable(db):
    cfg, url = db
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")  # повторный запуск ничего не меняет
    assert TABLES <= tables(url)


def test_repository_works_on_migrated_database(db):
    cfg, url = db
    command.upgrade(cfg, "head")
    engine = make_engine(url)
    try:
        with make_session_factory(engine)() as session:
            record = repo.create_matrix(session, "m", [[1, 2], [3, 4]], ["t"], note="after")
            analysis = repo.run_analysis(session, record.id)
            assert repo.analysis_vectors(analysis)["zero_columns"] == [False, False]
            repo.delete_matrix(session, record.id)
            assert repo.count_analyses(session) == 0
    finally:
        engine.dispose()
