"""Табличные тестовые случаи: единый источник для pytest и для протокола тестирования.

Случай — это вызов функции с аргументами и ожидаемый результат (значение или класс
исключения). pytest проверяет случаи функцией check_case, а tools/protocol.py выполняет
те же случаи и записывает фактические результаты в протокол.
"""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from typing import Any

from matrix_lab.errors import InvalidDataError  # noqa: F401  (используется в других таблицах)

EPS = 1e-9


@dataclass(frozen=True)
class Case:
    id: str
    desc: str
    call: str           # «пакет.модуль:функция»
    args: tuple
    expected: Any       # значение или класс исключения
    match: str = ""     # регулярное выражение для текста исключения
    shown: str = ""     # как показать входные данные в протоколе (по умолчанию repr аргументов)


@dataclass(frozen=True)
class Outcome:
    actual: str
    passed: bool


def _resolve(call):
    module_name, func_name = call.split(":")
    return getattr(importlib.import_module(module_name), func_name)


def _is_error(expected):
    return isinstance(expected, type) and issubclass(expected, BaseException)


def run_case(case):
    """Выполнить случай и вернуть фактический результат с вердиктом."""
    func = _resolve(case.call)
    try:
        value = func(*case.args)
    except Exception as err:  # любая ошибка — это тоже фактический результат
        text = f"{type(err).__name__}: {err}"
        ok = (_is_error(case.expected) and isinstance(err, case.expected)
              and re.search(case.match, str(err)) is not None)
        return Outcome(text, ok)
    if _is_error(case.expected):
        return Outcome(repr(value), False)
    return Outcome(repr(value), value == case.expected)


def expected_text(case):
    if _is_error(case.expected):
        extra = f" («{case.match}»)" if case.match else ""
        return f"{case.expected.__name__}{extra}"
    return repr(case.expected)


def input_text(case):
    return case.shown or ", ".join(repr(a) for a in case.args)


def check_case(case):
    outcome = run_case(case)
    assert outcome.passed, (f"{case.id}: ожидалось {expected_text(case)}, "
                            f"получено {outcome.actual}")


LOGIC = "matrix_lab.logic"
IO = "matrix_lab.io_utils"

VALIDATE = [
    Case("TC-V-01", "n = 0: пустая матрица (граница n-1)", f"{LOGIC}:validate_matrix",
         ([],), ValueError, "n >= 1"),
    Case("TC-V-02", "m = 0: пустая строка (граница m-1)", f"{LOGIC}:validate_matrix",
         ([[]],), ValueError, "m >= 1"),
    Case("TC-V-03", "n = 1, m = 1: минимальная матрица", f"{LOGIC}:validate_matrix",
         ([[5.0]],), (1, 1)),
    Case("TC-V-04", "вторая строка короче на 1 (m-1)", f"{LOGIC}:validate_matrix",
         ([[1, 2, 3], [1, 2]],), ValueError, "Строка 2"),
    Case("TC-V-05", "вторая строка длиннее на 1 (m+1)", f"{LOGIC}:validate_matrix",
         ([[1, 2], [1, 2, 3]],), ValueError, "Строка 2"),
    Case("TC-V-06", "n = 2, m = 3: номинальное значение", f"{LOGIC}:validate_matrix",
         ([[1, 2, 3], [4, 5, 6]],), (2, 3)),
]

ZERO_COLUMNS = [
    Case("TC-Z-01", "один нулевой элемент", f"{LOGIC}:column_all_zero", ([[0.0]],), [True]),
    Case("TC-Z-02", "значение равно допуску EPS (граница включена)",
         f"{LOGIC}:column_all_zero", ([[1e-9]],), [True]),
    Case("TC-Z-03", "значение чуть больше EPS (1.001e-9)",
         f"{LOGIC}:column_all_zero", ([[1.001e-9]],), [False]),
    Case("TC-Z-04", "значение равно -EPS", f"{LOGIC}:column_all_zero", ([[-1e-9]],), [True]),
    Case("TC-Z-05", "значение чуть меньше -EPS (-1.001e-9)",
         f"{LOGIC}:column_all_zero", ([[-1.001e-9]],), [False]),
    Case("TC-Z-06", "ненулевой элемент только в последней строке",
         f"{LOGIC}:column_all_zero", ([[0.0], [0.0], [1.0]],), [False]),
    Case("TC-Z-07", "отрицательный нуль -0.0", f"{LOGIC}:column_all_zero", ([[-0.0]],), [True]),
    Case("TC-Z-08", "первый столбец нулевой, последний нет",
         f"{LOGIC}:column_all_zero", ([[0.0, 1.0], [0.0, 0.0]],), [True, False]),
]

DESCENDING = [
    Case("TC-D-01", "m = 1: строка из одного элемента", f"{LOGIC}:row_descending",
         ([[7.0]],), [True]),
    Case("TC-D-02", "m = 2: равные элементы", f"{LOGIC}:row_descending", ([[3.0, 3.0]],), [True]),
    Case("TC-D-03", "m = 2: строгое убывание", f"{LOGIC}:row_descending", ([[3.0, 2.0]],), [True]),
    Case("TC-D-04", "m = 2: возрастание", f"{LOGIC}:row_descending", ([[2.0, 3.0]],), [False]),
    Case("TC-D-05", "рост ровно на EPS (граница допуска)", f"{LOGIC}:row_descending",
         ([[0.0, 1e-9]],), [True]),
    Case("TC-D-06", "рост на 1.001·EPS", f"{LOGIC}:row_descending", ([[0.0, 1.001e-9]],), [False]),
    Case("TC-D-07", "нарушение порядка только в последней паре", f"{LOGIC}:row_descending",
         ([[3.0, 2.0, 1.0, 5.0]],), [False]),
    Case("TC-D-08", "нарушение порядка только в первой паре", f"{LOGIC}:row_descending",
         ([[1.0, 2.0, 0.0, -1.0]],), [False]),
    Case("TC-D-09", "отрицательные числа", f"{LOGIC}:row_descending",
         ([[-1.0, -2.0], [-2.0, -1.0]],), [True, False]),
]

SYMMETRIC = [
    Case("TC-S-01", "m = 1: строка из одного элемента", f"{LOGIC}:row_symmetric",
         ([[5.0]],), [True]),
    Case("TC-S-02", "m = 2: равные элементы", f"{LOGIC}:row_symmetric", ([[1.0, 1.0]],), [True]),
    Case("TC-S-03", "m = 2: разные элементы", f"{LOGIC}:row_symmetric", ([[1.0, 2.0]],), [False]),
    Case("TC-S-04", "m = 2: разность ровно EPS", f"{LOGIC}:row_symmetric",
         ([[0.0, 1e-9]],), [True]),
    Case("TC-S-05", "m = 2: разность 2·EPS", f"{LOGIC}:row_symmetric", ([[0.0, 2e-9]],), [False]),
    Case("TC-S-06", "m = 3: средний элемент не влияет", f"{LOGIC}:row_symmetric",
         ([[1.0, 99.0, 1.0]],), [True]),
    Case("TC-S-07", "m = 3: крайние элементы различны", f"{LOGIC}:row_symmetric",
         ([[1.0, 2.0, 3.0]],), [False]),
    Case("TC-S-08", "m = 4: различна внутренняя пара", f"{LOGIC}:row_symmetric",
         ([[1.0, 2.0, 3.0, 1.0]],), [False]),
    Case("TC-S-09", "m = 4: симметричная строка", f"{LOGIC}:row_symmetric",
         ([[4.0, 5.0, 5.0, 4.0]],), [True]),
]

PARSE = [
    Case("TC-P-01", "минимальная матрица 1 × 1", f"{IO}:parse_matrix",
         (["1 1", "5"],), [[5.0]]),
    Case("TC-P-02", "n = 0 (граница n-1)", f"{IO}:parse_matrix", (["0 1"],), ValueError,
         "n >= 1"),
    Case("TC-P-03", "m = 0 (граница m-1)", f"{IO}:parse_matrix", (["1 0", "x"],), ValueError,
         "m >= 1"),
    Case("TC-P-04", "в заголовке один токен", f"{IO}:parse_matrix", (["3"],), ValueError,
         "Первая строка"),
    Case("TC-P-05", "в заголовке три токена", f"{IO}:parse_matrix", (["1 1 1", "5"],),
         ValueError, "Первая строка"),
    Case("TC-P-06", "отрицательное n", f"{IO}:parse_matrix", (["-1 1", "5"],), ValueError,
         "Первая строка"),
    Case("TC-P-07", "строк на одну меньше (n-1)", f"{IO}:parse_matrix", (["2 1", "5"],),
         ValueError, "Ожидалось 2 строк"),
    Case("TC-P-08", "строк на одну больше (n+1)", f"{IO}:parse_matrix",
         (["1 1", "5", "6"],), ValueError, "Ожидалось 1 строк"),
    Case("TC-P-09", "в строке на одно число меньше (m-1)", f"{IO}:parse_matrix",
         (["1 2", "5"],), ValueError, "ожидалось 2"),
    Case("TC-P-10", "в строке на одно число больше (m+1)", f"{IO}:parse_matrix",
         (["1 1", "5 6"],), ValueError, "ожидалось 1"),
    Case("TC-P-11", "пустой ввод", f"{IO}:parse_matrix", ([],), ValueError, "Пустой"),
    Case("TC-P-12", "только пустые строки", f"{IO}:parse_matrix", (["", "  "],), ValueError,
         "Пустой"),
    Case("TC-P-13", "десятичная запятая", f"{IO}:parse_matrix", (["1 1", "1,5"],), [[1.5]]),
    Case("TC-P-14", "экспоненциальная запись", f"{IO}:parse_matrix", (["1 1", "1e3"],),
         [[1000.0]]),
    Case("TC-P-15", "наибольшее конечное число типа float", f"{IO}:parse_matrix",
         (["1 1", "1.7976931348623157e308"],), [[1.7976931348623157e308]]),
    Case("TC-P-16", "переполнение float (1e309)", f"{IO}:parse_matrix", (["1 1", "1e309"],),
         ValueError, "конечными"),
    Case("TC-P-17", "значение nan", f"{IO}:parse_matrix", (["1 1", "nan"],), ValueError,
         "конечными"),
    Case("TC-P-18", "отрицательный нуль «-0»", f"{IO}:parse_matrix", (["1 1", "-0"],),
         [[0.0]]),
]

FORMAT = [
    Case("TC-F-01", "целые значения без дробной части", f"{IO}:format_matrix",
         ([[1.0, 2.0]],), "1  2"),
    Case("TC-F-02", "6 значащих цифр (число 123456)", f"{IO}:format_matrix",
         ([[123456.0]],), "123456"),
    Case("TC-F-03", "7 значащих цифр (число 1234567)", f"{IO}:format_matrix",
         ([[1234567.0]],), "1234567"),
    Case("TC-F-04", "10 значащих цифр после запятой", f"{IO}:format_matrix",
         ([[0.1234567891]],), "0.1234567891"),
    Case("TC-F-05", "9 цифр целой части", f"{IO}:format_matrix", ([[123456789.0]],),
         "123456789"),
    Case("TC-F-06", "отрицательный нуль выводится как 0", f"{IO}:format_matrix",
         ([[-0.0]],), "0"),
    Case("TC-F-07", "очень большое число", f"{IO}:format_matrix", ([[1e21]],), "1e+21"),
    Case("TC-F-08", "две строки, дробные и отрицательные", f"{IO}:format_matrix",
         ([[0.1, 0.25], [3.0, -4.5]],), "0.1  0.25\n3  -4.5"),
    Case("TC-F-09", "вектор из двух элементов", f"{IO}:format_vector",
         ([True, False],), "[True, False]"),
    Case("TC-F-10", "пустой вектор (граница длины 0)", f"{IO}:format_vector", ([],), "[]"),
]

GROUPS = [
    ("logic.validate_matrix", VALIDATE),
    ("logic.column_all_zero", ZERO_COLUMNS),
    ("logic.row_descending", DESCENDING),
    ("logic.row_symmetric", SYMMETRIC),
    ("io_utils.parse_matrix", PARSE),
    ("io_utils.format_matrix / format_vector", FORMAT),
]
