"""Тесты слоя доступа к данным: чтение, запись, ограничения, каскады, настройки."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from matrix_lab.db import repository as repo
from matrix_lab.db.models import Analysis, MatrixCell, VectorResult
from matrix_lab.db.session import make_engine
from matrix_lab.errors import InvalidDataError

SAMPLE = [[3, 2, 0], [0, 5, 0]]


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


# ------------------------------------------------------------ создание и чтение
def test_create_and_read_roundtrip(session):
    record = repo.create_matrix(session, "a", [[1, 2], [3, 4.5]], ["B", "a"])
    again = repo.get_matrix(session, record.id)
    assert repo.matrix_data(again) == [[1.0, 2.0], [3.0, 4.5]]
    assert (again.n_rows, again.n_cols) == (2, 2)
    assert sorted(t.name for t in again.tags) == ["a", "b"]


def test_create_strips_name_and_deduplicates_tags(session):
    record = repo.create_matrix(session, "  m  ", SAMPLE, ["x", "X", " x "])
    assert record.name == "m"
    assert [t.name for t in record.tags] == ["x"]


def test_tag_is_shared_between_matrices(session):
    repo.create_matrix(session, "a", SAMPLE, ["demo"])
    repo.create_matrix(session, "b", SAMPLE, ["demo"])
    items, total = repo.list_matrices(session, tag="demo")
    assert total == 2 and len(items) == 2


def test_duplicate_name_is_rejected(session):
    repo.create_matrix(session, "a", SAMPLE)
    with pytest.raises(repo.DuplicateError):
        repo.create_matrix(session, "a", SAMPLE)


@pytest.mark.parametrize("data", [
    [], [[]], [[1], [1, 2]], [[float("nan")]], [[float("inf")]], [[1, float("-inf")]],
])
def test_invalid_matrix_is_rejected(session, data):
    with pytest.raises(InvalidDataError):
        repo.create_matrix(session, "bad", data)


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_invalid_name_is_rejected(session, name):
    with pytest.raises(InvalidDataError):
        repo.create_matrix(session, name, SAMPLE)


@pytest.mark.parametrize("tag", ["", "  ", "t" * 51])
def test_invalid_tag_is_rejected(session, tag):
    with pytest.raises(InvalidDataError):
        repo.create_matrix(session, "m", SAMPLE, [tag])


def test_name_of_100_chars_is_accepted(session):
    assert repo.create_matrix(session, "n" * 100, SAMPLE).id > 0


def test_single_cell_matrix(session):
    record = repo.create_matrix(session, "one", [[7]])
    assert repo.matrix_data(record) == [[7.0]]


def test_get_missing_matrix(session):
    with pytest.raises(repo.NotFoundError):
        repo.get_matrix(session, 999)


# ------------------------------------------------------------ изменение и удаление
def test_update_name_and_tags(session):
    record = repo.create_matrix(session, "a", SAMPLE, ["x"])
    repo.update_matrix(session, record.id, name="b", tags=["y", "z"])
    again = repo.get_matrix(session, record.id)
    assert again.name == "b" and sorted(t.name for t in again.tags) == ["y", "z"]


def test_update_data_same_shape_replaces_cells(session):
    record = repo.create_matrix(session, "a", SAMPLE)
    repo.update_matrix(session, record.id, data=[[9, 8, 7], [6, 5, 4]])
    assert repo.matrix_data(repo.get_matrix(session, record.id)) == [[9, 8, 7], [6, 5, 4]]
    assert count(session, MatrixCell) == 6


def test_update_data_changes_shape(session):
    record = repo.create_matrix(session, "a", SAMPLE)
    repo.update_matrix(session, record.id, data=[[1], [2], [3]])
    again = repo.get_matrix(session, record.id)
    assert (again.n_rows, again.n_cols) == (3, 1)
    assert count(session, MatrixCell) == 3


def test_update_keeps_fields_that_are_none(session):
    record = repo.create_matrix(session, "a", SAMPLE, ["x"])
    repo.update_matrix(session, record.id)
    again = repo.get_matrix(session, record.id)
    assert again.name == "a" and [t.name for t in again.tags] == ["x"]


def test_update_to_own_name_is_allowed(session):
    record = repo.create_matrix(session, "a", SAMPLE)
    assert repo.update_matrix(session, record.id, name="a").name == "a"


def test_update_to_taken_name_is_rejected(session):
    repo.create_matrix(session, "a", SAMPLE)
    other = repo.create_matrix(session, "b", SAMPLE)
    with pytest.raises(repo.DuplicateError):
        repo.update_matrix(session, other.id, name="a")


def test_update_with_invalid_data_is_rejected(session):
    record = repo.create_matrix(session, "a", SAMPLE)
    with pytest.raises(InvalidDataError):
        repo.update_matrix(session, record.id, data=[[1], [1, 2]])


def test_update_missing_matrix(session):
    with pytest.raises(repo.NotFoundError):
        repo.update_matrix(session, 5, name="x")


def test_delete_removes_cells_analyses_and_results(session):
    record = repo.create_matrix(session, "a", SAMPLE, ["x"])
    repo.run_analysis(session, record.id)
    repo.delete_matrix(session, record.id)
    assert count(session, MatrixCell) == 0
    assert count(session, Analysis) == 0
    assert count(session, VectorResult) == 0
    with pytest.raises(repo.NotFoundError):
        repo.get_matrix(session, record.id)


def test_delete_missing_matrix(session):
    with pytest.raises(repo.NotFoundError):
        repo.delete_matrix(session, 1)


def test_foreign_keys_are_enforced(session):
    session.add(MatrixCell(matrix_id=999, row_idx=0, col_idx=0, value=1.0))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# ------------------------------------------------------------ список, фильтры, сортировка
@pytest.fixture
def five(session):
    for name, tags in (("delta", ["x"]), ("alpha", ["x", "y"]), ("charlie", []),
                       ("bravo", ["y"]), ("echo-demo", ["x"])):
        repo.create_matrix(session, name, SAMPLE, tags)
    return session


def names(items):
    return [r.name for r in items]


def test_list_default_order_is_by_id(five):
    items, total = repo.list_matrices(five)
    assert total == 5 and names(items)[0] == "delta"


def test_list_filter_by_tag(five):
    items, total = repo.list_matrices(five, tag="X")
    assert total == 3 and set(names(items)) == {"delta", "alpha", "echo-demo"}


def test_list_filter_by_unknown_tag(five):
    assert repo.list_matrices(five, tag="nope") == ([], 0)


def test_list_filter_by_name_part(five):
    items, total = repo.list_matrices(five, query="DEMO")
    assert names(items) == ["echo-demo"] and total == 1


def test_list_filters_combine(five):
    items, _ = repo.list_matrices(five, tag="x", query="a")
    assert set(names(items)) == {"delta", "alpha"}


@pytest.mark.parametrize("order,expected", [
    ("asc", ["alpha", "bravo", "charlie", "delta", "echo-demo"]),
    ("desc", ["echo-demo", "delta", "charlie", "bravo", "alpha"]),
])
def test_list_sort_by_name(five, order, expected):
    items, _ = repo.list_matrices(five, sort_by="name", order=order)
    assert names(items) == expected


def test_list_pagination(five):
    page1, total = repo.list_matrices(five, sort_by="name", limit=2, offset=0)
    page3, _ = repo.list_matrices(five, sort_by="name", limit=2, offset=4)
    assert total == 5 and names(page1) == ["alpha", "bravo"] and names(page3) == ["echo-demo"]


@pytest.mark.parametrize("kwargs", [
    {"sort_by": "password"}, {"order": "up"}, {"limit": 0}, {"offset": -1},
])
def test_list_invalid_arguments(five, kwargs):
    with pytest.raises(InvalidDataError):
        repo.list_matrices(five, **kwargs)


# ------------------------------------------------------------ анализ
def test_analysis_of_sample_matrix(session):
    record = repo.create_matrix(session, "a", SAMPLE)
    analysis = repo.run_analysis(session, record.id)
    assert repo.analysis_vectors(analysis) == {
        "zero_columns": [False, False, True],
        "descending_rows": [True, False],
        "symmetric_rows": [False, True],
    }
    assert analysis.eps == pytest.approx(1e-9)


def test_analysis_with_custom_eps(session):
    record = repo.create_matrix(session, "a", [[0.001, 1.0]])
    strict = repo.run_analysis(session, record.id)
    loose = repo.run_analysis(session, record.id, eps=0.01)
    assert repo.analysis_vectors(strict)["zero_columns"] == [False, False]
    assert repo.analysis_vectors(loose)["zero_columns"] == [True, False]


def test_analysis_uses_eps_from_settings(session):
    record = repo.create_matrix(session, "a", [[0.001, 1.0]])
    repo.set_setting(session, "eps", 0.01)
    assert repo.analysis_vectors(repo.run_analysis(session, record.id))["zero_columns"][0]


@pytest.mark.parametrize("eps", [-1.0, float("nan"), float("inf")])
def test_analysis_invalid_eps(session, eps):
    record = repo.create_matrix(session, "a", SAMPLE)
    with pytest.raises(InvalidDataError):
        repo.run_analysis(session, record.id, eps=eps)


def test_analysis_of_missing_matrix(session):
    with pytest.raises(repo.NotFoundError):
        repo.run_analysis(session, 42)


def test_analysis_history_and_lookup(session):
    record = repo.create_matrix(session, "a", SAMPLE)
    first = repo.run_analysis(session, record.id)
    second = repo.run_analysis(session, record.id)
    assert [a.id for a in repo.list_analyses(session, record.id)] == [first.id, second.id]
    assert repo.get_analysis(session, second.id).matrix_id == record.id
    assert repo.count_analyses(session) == 2


def test_missing_analysis(session):
    with pytest.raises(repo.NotFoundError):
        repo.get_analysis(session, 1)


def test_all_vector_values(session):
    assert repo.all_vector_values(session) == []
    repo.run_analysis(session, repo.create_matrix(session, "a", [[0, 1]]).id)
    values = repo.all_vector_values(session)
    assert len(values) == 2 + 1 + 1  # zero_columns (m) + descending (n) + symmetric (n)
    assert {v["kind"] for v in values} == {"zero_columns", "descending_rows", "symmetric_rows"}


# ------------------------------------------------------------ настройки
def test_default_settings(session):
    assert repo.get_settings(session) == repo.DEFAULT_SETTINGS


def test_set_and_overwrite_setting(session):
    repo.set_setting(session, "page_size", 5)
    assert repo.get_settings(session)["page_size"] == "5"
    repo.set_setting(session, "page_size", 7)
    assert repo.get_settings(session)["page_size"] == "7"


@pytest.mark.parametrize("key,value", [
    ("unknown", "1"), ("page_size", "0"), ("page_size", "101"), ("page_size", "abc"),
    ("eps", "-1"), ("eps", "abc"), ("eps", "nan"), ("sort_by", "zzz"), ("order", "up"),
])
def test_invalid_settings_are_rejected(session, key, value):
    with pytest.raises(InvalidDataError):
        repo.set_setting(session, key, value)


# ------------------------------------------------------------ подключение
def test_engine_uses_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    assert str(make_engine().url) == "sqlite://"


def test_engine_default_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert make_engine().url.database == "matrix_lab.db"


# ------------------------------------------------------------ примечание (миграция 0002)
def test_note_create_update_and_clear(session):
    record = repo.create_matrix(session, "a", SAMPLE, note="  первая  ")
    assert record.note == "первая"
    repo.update_matrix(session, record.id, note="вторая")
    assert repo.get_matrix(session, record.id).note == "вторая"
    repo.update_matrix(session, record.id, note="")
    assert repo.get_matrix(session, record.id).note is None


def test_note_without_value_is_none(session):
    assert repo.create_matrix(session, "a", SAMPLE).note is None


def test_note_length_limit(session):
    assert repo.create_matrix(session, "ok", SAMPLE, note="n" * 200).note == "n" * 200
    with pytest.raises(InvalidDataError):
        repo.create_matrix(session, "bad", SAMPLE, note="n" * 201)


# ------------------------------------------------------------ защита и поиск
def test_too_large_matrix_is_rejected(session):
    huge = [[0.0] * 400 for _ in range(300)]  # 120 000 элементов > MAX_CELLS
    with pytest.raises(InvalidDataError):
        repo.create_matrix(session, "huge", huge)


def test_size_limit_boundary(session, monkeypatch):
    monkeypatch.setattr(repo, "MAX_CELLS", 6)
    assert repo.create_matrix(session, "ok", [[1, 2, 3], [4, 5, 6]]).n_cols == 3
    with pytest.raises(InvalidDataError):
        repo.create_matrix(session, "bad", [[1, 2, 3, 4], [5, 6, 7, 8]])


@pytest.mark.parametrize("name,query,expected", [
    ("100%_done", "%", ["100%_done"]),
    ("100%_done", "_d", ["100%_done"]),
    ("abc", "%", []),
    ("abc", "_", []),
    ("a\\b", "\\", ["a\\b"]),
])
def test_search_treats_wildcards_literally(session, name, query, expected):
    repo.create_matrix(session, name, SAMPLE)
    items, _ = repo.list_matrices(session, query=query)
    assert [r.name for r in items] == expected
