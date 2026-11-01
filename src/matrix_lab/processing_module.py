"""Модуль обработки: строит три логических вектора по матрице."""

from __future__ import annotations

from .errors import InvalidDataError
from .logic import column_all_zero, row_descending, row_symmetric
from .models import Matrix, ProcessingResult


def process(matrix: Matrix) -> ProcessingResult:
    """Применить три условия варианта 7.

    :raises InvalidDataError: матрица пустая или непрямоугольная.
    """
    try:
        return ProcessingResult(
            zero_columns=column_all_zero(matrix),
            descending_rows=row_descending(matrix),
            symmetric_rows=row_symmetric(matrix),
        )
    except ValueError as err:
        raise InvalidDataError(str(err)) from err
