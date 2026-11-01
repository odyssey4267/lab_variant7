"""Сопоставление объектов данных (mapping) между модулями и JSON-форматом обмена.

Внутреннее представление          JSON (транспорт)
Matrix (список строк)        <->  {"matrix": {"rows", "cols", "data"}}
ProcessingResult.zero_columns <-> "zeroColumns"   (snake_case -> camelCase)
bool                          <-> true/false      (0/1 при чтении приводятся к bool)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from .errors import InvalidDataError, VersionConflictError
from .models import Matrix, ProcessingResult

API_VERSION = "1.0"

RESULT_FIELDS = (
    ("zero_columns", "zeroColumns"),
    ("descending_rows", "descendingRows"),
    ("symmetric_rows", "symmetricRows"),
)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def matrix_to_dto(matrix: Matrix) -> Dict[str, Any]:
    """Matrix -> JSON-объект запроса (rows и cols вычисляются по данным)."""
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    return {
        "api_version": API_VERSION,
        "matrix": {"rows": rows, "cols": cols, "data": [[float(x) for x in r] for r in matrix]},
    }


def dto_to_matrix(dto: Any) -> Matrix:
    """JSON-объект запроса -> Matrix с полной проверкой структуры и значений."""
    if not isinstance(dto, dict) or not isinstance(dto.get("matrix"), dict):
        raise InvalidDataError("Ожидался объект с полем 'matrix'.")
    body = dto["matrix"]
    rows, cols, data = body.get("rows"), body.get("cols"), body.get("data")
    if not _is_int(rows) or not _is_int(cols) or rows < 1 or cols < 1:
        raise InvalidDataError("Поля 'rows' и 'cols' должны быть целыми числами >= 1.")
    if not isinstance(data, list) or len(data) != rows:
        raise InvalidDataError(f"Поле 'data' должно содержать {rows} строк.")
    matrix: Matrix = []
    for i, row in enumerate(data, start=1):
        if not isinstance(row, list) or len(row) != cols:
            raise InvalidDataError(f"Строка {i}: ожидалось {cols} чисел.")
        for x in row:
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
                raise InvalidDataError(f"Строка {i}: значения должны быть конечными числами.")
        matrix.append([float(x) for x in row])
    return matrix


def result_to_dto(result: ProcessingResult) -> Dict[str, Any]:
    """ProcessingResult -> JSON-объект ответа."""
    return {
        "api_version": API_VERSION,
        "result": {json_name: list(getattr(result, name)) for name, json_name in RESULT_FIELDS},
    }


def _to_bool_list(value: Any, name: str) -> List[bool]:
    if not isinstance(value, list):
        raise InvalidDataError(f"Поле '{name}' должно быть массивом.")
    out: List[bool] = []
    for item in value:
        if isinstance(item, bool):
            out.append(item)
        elif item in (0, 1) and _is_int(item):
            out.append(bool(item))  # преобразование типов: 0/1 -> False/True
        else:
            raise InvalidDataError(f"Поле '{name}': допустимы только true/false (или 0/1).")
    return out


def dto_to_result(dto: Any) -> ProcessingResult:
    """JSON-объект ответа -> ProcessingResult."""
    if not isinstance(dto, dict) or not isinstance(dto.get("result"), dict):
        raise InvalidDataError("Ожидался объект с полем 'result'.")
    body = dto["result"]
    values = {}
    for name, json_name in RESULT_FIELDS:
        if json_name not in body:
            raise InvalidDataError(f"В ответе нет поля '{json_name}'.")
        values[name] = _to_bool_list(body[json_name], json_name)
    return ProcessingResult(**values)


def check_version(dto: Any) -> None:
    """Проверить совместимость версии API (совпадение старшей версии).

    :raises VersionConflictError: версия отсутствует или несовместима.
    """
    version = dto.get("api_version") if isinstance(dto, dict) else None
    if not isinstance(version, str) or version.split(".")[0] != API_VERSION.split(".")[0]:
        raise VersionConflictError(
            f"Версия API {version!r} несовместима с поддерживаемой {API_VERSION}."
        )
