"""Тесты «белого ящика»: покрытие решений, условий и комбинаций условий.

Для каждого составного условия приведена таблица истинности. Условия вычисляются слева
направо с прерыванием (оператор or), поэтому часть комбинаций недостижима как отдельные
пути — это отмечено в комментариях. Покрытие решений дополнительно измеряется
coverage.py в режиме ветвей (`--cov-branch`).
"""

import pytest

from matrix_lab import http_client, mapping
from matrix_lab.errors import InvalidDataError, VersionConflictError
from matrix_lab.io_utils import parse_matrix

pytestmark = pytest.mark.whitebox

# --- Решение D1: parse_matrix, проверка заголовка --------------------------------
#     D1 = A or B,  A = (len(head) != 2),  B = not all(токен — ASCII-цифры)
#     B вычисляется только при A = False (прерывание).
D1_TABLE = [
    # id             строки ввода    A      B      D1
    ("A=T,B=T",      ["a"],          True,  True,  True),   # B не вычисляется
    ("A=T,B=F",      ["3"],          True,  False, True),   # B не вычисляется
    ("A=F,B=T",      ["a b"],        False, True,  True),
    ("A=F,B=F",      ["1 1", "5"],   False, False, False),
]


@pytest.mark.parametrize("name, lines, a, b, decision", D1_TABLE, ids=[r[0] for r in D1_TABLE])
def test_d1_header_condition(name, lines, a, b, decision):
    if decision:
        with pytest.raises(ValueError, match="Первая строка"):
            parse_matrix(lines)
    else:
        assert parse_matrix(lines) == [[5.0]]


# --- Решение D2: parse_matrix, проверка размеров ---------------------------------
#     D2 = (n < 1) or (m < 1)
D2_TABLE = [
    ("n<1,m>=1", ["0 1"],        True),
    ("n>=1,m<1", ["1 0", "x"],   True),
    ("n>=1,m>=1", ["1 1", "5"],  False),
]


@pytest.mark.parametrize("name, lines, decision", D2_TABLE, ids=[r[0] for r in D2_TABLE])
def test_d2_size_condition(name, lines, decision):
    if decision:
        with pytest.raises(ValueError, match=">= 1"):
            parse_matrix(lines)
    else:
        assert parse_matrix(lines) == [[5.0]]


# --- Решение D3: dto_to_matrix, верхний уровень ----------------------------------
#     D3 = (not isinstance(dto, dict)) or (not isinstance(dto["matrix"], dict))
D3_TABLE = [
    ("C1=T",        [1, 2],                              True),    # C2 не вычисляется
    ("C1=F,C2=T",   {"matrix": [1]},                     True),
    ("C1=F,C2=T'",  {},                                  True),    # поля matrix нет
    ("C1=F,C2=F",   {"matrix": {"rows": 1, "cols": 1, "data": [[0]]}}, False),
]


@pytest.mark.parametrize("name, payload, decision", D3_TABLE, ids=[r[0] for r in D3_TABLE])
def test_d3_top_level(name, payload, decision):
    if decision:
        with pytest.raises(InvalidDataError, match="matrix"):
            mapping.dto_to_matrix(payload)
    else:
        assert mapping.dto_to_matrix(payload) == [[0.0]]


# --- Решение D4: dto_to_matrix, размеры -----------------------------------------
#     D4 = c1 or c2 or c3 or c4,  c1 = rows не целое, c2 = cols не целое,
#     c3 = rows < 1, c4 = cols < 1. Цепочка из четырёх условий даёт 5 достижимых путей
#     (для каждого условия «первое истинное» + путь «все ложны»); для MC/DC этого
#     достаточно: каждое условие по отдельности меняет результат решения.
D4_TABLE = [
    # id     rows   cols   c1     c2     c3     c4     D4
    ("none", 1,     1,     False, False, False, False, False),
    ("c1",   "1",   1,     True,  None,  None,  None,  True),
    ("c2",   1,     1.5,   False, True,  None,  None,  True),
    ("c3",   0,     1,     False, False, True,  None,  True),
    ("c4",   1,     0,     False, False, False, True,  True),
]


@pytest.mark.parametrize("name, rows, cols, c1, c2, c3, c4, decision", D4_TABLE,
                         ids=[r[0] for r in D4_TABLE])
def test_d4_dimensions(name, rows, cols, c1, c2, c3, c4, decision):
    data = [[0] * cols] * rows if isinstance(rows, int) and isinstance(cols, int) \
        and rows > 0 and cols > 0 else [[0]]
    payload = {"matrix": {"rows": rows, "cols": cols, "data": data}}
    if decision:
        with pytest.raises(InvalidDataError, match="rows. и .cols"):
            mapping.dto_to_matrix(payload)
    else:
        assert mapping.dto_to_matrix(payload) == [[0.0]]


# --- Решение D5: _to_float, первая проверка --------------------------------------
#     D5 = isinstance(v, bool) or (not isinstance(v, (int, float)))
D5_TABLE = [
    ("bool=T",         True,   True),    # вторая часть не вычисляется
    ("bool=F,num=F",   "x",    True),
    ("bool=F,num=T",   2,      False),
]


@pytest.mark.parametrize("name, value, decision", D5_TABLE, ids=[r[0] for r in D5_TABLE])
def test_d5_element_type(name, value, decision):
    if decision:
        with pytest.raises(InvalidDataError, match="конечными"):
            mapping._to_float(value, 1)
    else:
        assert mapping._to_float(value, 1) == 2.0


@pytest.mark.parametrize("value, message", [
    (10 ** 400, "слишком велико"),      # ветка except OverflowError
    (float("inf"), "конечными"),        # ветка not isfinite = True
])
def test_d5_numeric_branches(value, message):
    with pytest.raises(InvalidDataError, match=message):
        mapping._to_float(value, 1)


# --- Решение D6: check_version ----------------------------------------------------
#     D6 = (not isinstance(version, str)) or (major(version) != "1")
D6_TABLE = [
    ("E1=T",       {"api_version": 1},      True),    # E2 не вычисляется
    ("E1=F,E2=T",  {"api_version": "2.0"},  True),
    ("E1=F,E2=F",  {"api_version": "1.5"},  False),
]


@pytest.mark.parametrize("name, payload, decision", D6_TABLE, ids=[r[0] for r in D6_TABLE])
def test_d6_version(name, payload, decision):
    if decision:
        with pytest.raises(VersionConflictError):
            mapping.check_version(payload)
    else:
        mapping.check_version(payload)


# --- Решение D7: http_client._check_arguments ------------------------------------
#     D7 = (схема не http/https) or (нет хоста);  D8 = not (timeout > 0)
D7_TABLE = [
    ("scheme=T",       "ftp://host:1",  True),    # хост не проверяется
    ("scheme=F,host=T", "http://",      True),
    ("scheme=F,host=F", "http://h:1",   False),
]


@pytest.mark.parametrize("name, url, decision", D7_TABLE, ids=[r[0] for r in D7_TABLE])
def test_d7_url(name, url, decision):
    if decision:
        with pytest.raises(InvalidDataError, match="адрес"):
            http_client._check_arguments(url, 1.0)
    else:
        http_client._check_arguments(url, 1.0)


TIMEOUTS = [(-1.0, True), (0.0, True), (float("nan"), True), (0.001, False)]


@pytest.mark.parametrize("timeout, decision", TIMEOUTS)
def test_d8_timeout(timeout, decision):
    if decision:
        with pytest.raises(InvalidDataError, match="Таймаут"):
            http_client._check_arguments("http://h:1", timeout)
    else:
        http_client._check_arguments("http://h:1", timeout)
