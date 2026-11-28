"""Тесты модуля анализа данных (pandas, numpy, scikit-learn)."""

import pytest

from matrix_lab.analytics import forecast_row, matrix_statistics, vector_summary

DATA = [[1, 2, 3], [4, 4, 4], [0, -1, -2]]


def test_statistics_values():
    stats = matrix_statistics(DATA)
    assert stats["mean"] == pytest.approx(15 / 9)
    assert stats["median"] == 2 and stats["min"] == -2 and stats["max"] == 4
    assert stats["column_means"] == pytest.approx([5 / 3] * 3)
    assert stats["row_sums"] == [6, 12, -3]


def test_statistics_of_single_value():
    stats = matrix_statistics([[5]])
    assert stats["std"] == 0 and stats["mean"] == 5


@pytest.mark.parametrize("data", [[], [[]]])
def test_statistics_of_empty_matrix(data):
    with pytest.raises(ValueError):
        matrix_statistics(data)


def test_forecast_increasing_row():
    result = forecast_row(DATA, 0, 2)
    assert result["slope"] == pytest.approx(1.0)
    assert result["forecast"] == pytest.approx([4.0, 5.0])


def test_forecast_constant_row():
    assert forecast_row(DATA, 1, 1)["forecast"] == pytest.approx([4.0])


def test_forecast_decreasing_row():
    assert forecast_row(DATA, 2, 1)["forecast"] == pytest.approx([-3.0])


@pytest.mark.parametrize("row,steps", [(-1, 3), (3, 3), (0, 0), (0, 21)])
def test_forecast_invalid_arguments(row, steps):
    with pytest.raises(ValueError):
        forecast_row(DATA, row, steps)


def test_forecast_needs_two_points():
    with pytest.raises(ValueError):
        forecast_row([[1]], 0, 1)


def test_vector_summary():
    records = [{"kind": "a", "value": True}, {"kind": "a", "value": False},
               {"kind": "a", "value": False}, {"kind": "b", "value": True}]
    assert vector_summary(records) == {
        "a": {"total": 3, "true_share": 0.3333}, "b": {"total": 1, "true_share": 1.0}}


def test_vector_summary_empty():
    assert vector_summary([]) == {}
