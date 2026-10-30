"""Логика варианта 7.

Дана вещественная матрица размерности n * m. По матрице получить логический
вектор, k-му элементу которого присваивается True, если выполнено условие,
и False иначе:

    1) все элементы k-го столбца нулевые;
    2) элементы k-й строки упорядочены по убыванию;
    3) k-я строка матрицы симметрична.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

Matrix = Sequence[Sequence[float]]

# Допуск для сравнения вещественных чисел (ошибки округления).
EPS = 1e-9

def validate_matrix(matrix: Matrix) -> Tuple[int, int]:
    """Проверить, что матрица непустая и прямоугольная. Вернуть (n, m).

    :raises ValueError: матрица пустая или строки разной длины.
    """
    if len(matrix) == 0:
        raise ValueError("Матрица не должна быть пустой (n >= 1).")
    m = len(matrix[0])
    if m == 0:
        raise ValueError("Матрица не должна быть пустой (m >= 1).")
    for i, row in enumerate(matrix, start=1):
        if len(row) != m:
            raise ValueError(
                f"Строка {i} содержит {len(row)} элементов, ожидалось {m}."
            )
    return len(matrix), m

def _is_zero(x: float, eps: float = EPS) -> bool:
    return abs(x) <= eps
    
def column_all_zero(matrix: Matrix, eps: float = EPS) -> List[bool]:
    """Уровень 1. Вектор длины m: True, если все элементы k-го столбца нулевые."""
    n, m = validate_matrix(matrix)
    return [all(_is_zero(matrix[i][k], eps) for i in range(n)) for k in range(m)]

def row_descending(matrix: Matrix, eps: float = EPS) -> List[bool]:
    """Уровень 2. Вектор длины n: True, если элементы k-й строки упорядочены
    по убыванию (нестрого: a[j] >= a[j+1]). Строка из одного элемента — True.
    """
    n, m = validate_matrix(matrix)
    return [
        all(matrix[k][j] + eps >= matrix[k][j + 1] for j in range(m - 1))
        for k in range(n)
    ]
    
def row_symmetric(matrix: Matrix, eps: float = EPS) -> List[bool]:
    """Уровень 3. Вектор длины n: True, если k-я строка симметрична
    (читается одинаково слева направо и справа налево, a[j] == a[m-1-j]).
    """
    n, m = validate_matrix(matrix)
    return [
        all(
            math.isclose(matrix[k][j], matrix[k][m - 1 - j], rel_tol=0.0, abs_tol=eps)
            for j in range(m // 2)
        )
        for k in range(n)
    ]