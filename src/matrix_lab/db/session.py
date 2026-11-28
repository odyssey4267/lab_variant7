"""Подключение к базе данных: движок, фабрика сессий, создание таблиц."""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

DEFAULT_URL = "sqlite:///matrix_lab.db"
MEMORY_URLS = ("sqlite://", "sqlite:///:memory:")


def make_engine(url: Optional[str] = None) -> Engine:
    """Создать движок. Адрес берётся из аргумента, переменной DATABASE_URL или по умолчанию."""
    url = url or os.environ.get("DATABASE_URL", DEFAULT_URL)
    options = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if url in MEMORY_URLS:
            options["poolclass"] = StaticPool  # одна и та же база на все соединения
    engine = create_engine(url, **options)
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _enable_foreign_keys(dbapi_connection, _record) -> None:
    """SQLite по умолчанию не проверяет внешние ключи — включаем."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_session_factory(engine: Engine) -> "sessionmaker[Session]":
    """Фабрика сессий для заданного движка."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    """Создать все таблицы (без миграций; на уровне 3 вместо этого используется Alembic)."""
    Base.metadata.create_all(engine)
