"""Общие фикстуры тестов хранилища: база в памяти, сессия и HTTP-клиент."""

import pytest
from fastapi.testclient import TestClient

from matrix_lab.api import create_app
from matrix_lab.db.session import init_db, make_engine, make_session_factory


@pytest.fixture
def engine():
    eng = make_engine("sqlite://")  # база в памяти, у каждого теста своя
    init_db(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with make_session_factory(engine)() as sess:
        yield sess


@pytest.fixture
def client(engine):
    return TestClient(create_app(engine))
