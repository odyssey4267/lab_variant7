"""Заглушки (stubs) нижних модулей для нисходящей интеграции.

Верхний модуль (app) отлаживается раньше, чем готовы настоящие модули ввода,
обработки и вывода: заглушки возвращают фиксированные данные.
"""

from __future__ import annotations

from .models import Matrix, ProcessingResult, Report


def read_input_stub() -> Matrix:
    return [[0.0, 1.0], [0.0, 2.0]]


def process_stub(matrix: Matrix) -> ProcessingResult:
    n, m = len(matrix), len(matrix[0])
    return ProcessingResult([False] * m, [False] * n, [False] * n)


def render_stub(report: Report) -> str:
    return f"[заглушка] вывод для матрицы {len(report.matrix)}x{len(report.matrix[0])}"
