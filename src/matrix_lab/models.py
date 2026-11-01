"""Общие структуры данных (контракты) между модулями системы."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

Matrix = List[List[float]]


@dataclass(frozen=True)
class ProcessingResult:
    """Результат модуля обработки: три логических вектора (позиции с 0)."""

    zero_columns: List[bool]     # длина m: столбец целиком нулевой
    descending_rows: List[bool]  # длина n: строка упорядочена по убыванию
    symmetric_rows: List[bool]   # длина n: строка симметрична


@dataclass(frozen=True)
class Report:
    """Данные для модуля вывода: исходная матрица и три вектора."""

    matrix: Matrix
    zero_columns: List[bool]
    descending_rows: List[bool]
    symmetric_rows: List[bool]
