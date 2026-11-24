"""Тесты «чёрного ящика» для io_utils.py: анализ граничных значений."""

import math

import pytest

from matrix_lab.io_utils import (
    format_matrix,
    parse_matrix,
    read_matrix_console,
    read_matrix_file,
)
from tests.cases import FORMAT, PARSE, check_case

pytestmark = pytest.mark.blackbox


@pytest.mark.parametrize("case", PARSE + FORMAT, ids=lambda c: c.id)
def test_io_boundaries(case):
    check_case(case)


@pytest.mark.parametrize("value", [0.1234567891, 1234567.0, 123456789.0, 1e-7, 1e21, -2.5e-300])
def test_format_does_not_change_value(value):
    """Предположение об ошибке: вывод не должен искажать число (круговое преобразование)."""
    text = format_matrix([[value]])
    assert math.isclose(parse_matrix(["1 1", text])[0][0], value, rel_tol=0.0, abs_tol=0.0)


def test_console_reprompts_on_boundary_values(monkeypatch, capsys):
    """Ввод с клавиатуры: n = 0, m = 0 и нечисловая строка вызывают повторный запрос."""
    answers = iter(["0 1", "1 0", "1 1", "abc", "5"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert read_matrix_console() == [[5.0]]
    assert capsys.readouterr().out.count("Ошибка") == 3


def test_read_matrix_file(tmp_path):
    path = tmp_path / "m.txt"
    path.write_text("1 2\n1,5 2\n", encoding="utf-8")
    assert read_matrix_file(str(path)) == [[1.5, 2.0]]
