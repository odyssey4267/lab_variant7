"""Ввод матрицы (с клавиатуры или из файла) и форматированный вывод."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence


def parse_matrix(lines: Iterable[str]) -> List[List[float]]:
    """Разобрать текст: первая строка «n m», далее n строк по m чисел.

    Разделитель — пробелы; десятичная запятая допускается.
    :raises ValueError: при неверном формате.
    """
    rows = [ln.strip() for ln in lines if ln.strip()]
    if not rows:
        raise ValueError("Пустой ввод.")
    head = rows[0].split()
    if len(head) != 2 or not all(t.isdigit() for t in head):
        raise ValueError("Первая строка должна содержать два целых числа: n m.")
    n, m = int(head[0]), int(head[1])
    if n < 1 or m < 1:
        raise ValueError("Должно быть n >= 1 и m >= 1.")
    if len(rows) - 1 != n:
        raise ValueError(f"Ожидалось {n} строк матрицы, получено {len(rows) - 1}.")
    matrix: List[List[float]] = []
    for i, line in enumerate(rows[1:], start=1):
        try:
            values = [float(t.replace(",", ".")) for t in line.split()]
        except ValueError:
            raise ValueError(f"Строка {i}: не удалось прочитать число.") from None
        if len(values) != m:
            raise ValueError(f"Строка {i}: ожидалось {m} чисел, получено {len(values)}.")
        if not all(math.isfinite(v) for v in values):
            raise ValueError(f"Строка {i}: значения должны быть конечными числами.")
        matrix.append(values)
    return matrix


def read_matrix_file(path: str) -> List[List[float]]:
    with open(path, encoding="utf-8") as f:
        return parse_matrix(f)


def read_matrix_console() -> List[List[float]]:
    """Интерактивный ввод: n и m, затем построчно матрица."""
    while True:
        try:
            n, m = (int(t) for t in input("Введите n и m (через пробел): ").split())
            if n < 1 or m < 1:
                raise ValueError
            break
        except ValueError:
            print("Ошибка: нужны два целых положительных числа.")
    matrix: List[List[float]] = []
    for i in range(1, n + 1):
        while True:
            try:
                row = [float(t.replace(",", ".")) for t in input(f"Строка {i}: ").split()]
                if len(row) != m or not all(math.isfinite(v) for v in row):
                    raise ValueError
                matrix.append(row)
                break
            except ValueError:
                print(f"Ошибка: нужно ввести ровно {m} вещественных чисел.")
    return matrix


def format_matrix(matrix: Sequence[Sequence[float]]) -> str:
    return "\n".join("  ".join(f"{x:g}" for x in row) for row in matrix)


def format_vector(vector: Sequence[bool]) -> str:
    return "[" + ", ".join("True" if v else "False" for v in vector) + "]"
