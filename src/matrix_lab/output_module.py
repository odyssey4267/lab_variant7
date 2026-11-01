"""Модуль вывода: формирует текстовый отчёт."""

from __future__ import annotations

from typing import Sequence

from .io_utils import format_matrix, format_vector
from .models import Report


def _numbers(vector: Sequence[bool]) -> str:
    """Номера (с 1) позиций, где стоит True."""
    found = [str(k) for k, flag in enumerate(vector, start=1) if flag]
    return ", ".join(found) if found else "нет"


def _block(title: str, vector: Sequence[bool], what: str) -> str:
    return f"{title}\n    {format_vector(vector)}  -> {what}: {_numbers(vector)}"


def render(report: Report) -> str:
    """Собрать текст отчёта по матрице и трём векторам."""
    parts = [
        "Матрица:",
        format_matrix(report.matrix),
        "",
        _block("1) Все элементы k-го столбца нулевые (k = 1..m):",
               report.zero_columns, "столбцы"),
        _block("2) Элементы k-й строки упорядочены по убыванию (k = 1..n):",
               report.descending_rows, "строки"),
        _block("3) k-я строка симметрична (k = 1..n):",
               report.symmetric_rows, "строки"),
    ]
    return "\n".join(parts)
