"""Репозиторий: чтение и запись данных (CRUD) поверх ORM-моделей.

Функции принимают сессию SQLAlchemy первым аргументом и сами фиксируют изменения.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import InvalidDataError
from ..logic import EPS, column_all_zero, row_descending, row_symmetric, validate_matrix
from .models import Analysis, MatrixCell, MatrixRecord, Setting, Tag, VectorResult


class NotFoundError(LookupError):
    """Запись с указанным идентификатором не найдена."""


class DuplicateError(ValueError):
    """Запись с таким уникальным значением уже существует."""


SORT_FIELDS = {
    "id": MatrixRecord.id,
    "name": MatrixRecord.name,
    "created_at": MatrixRecord.created_at,
    "n_rows": MatrixRecord.n_rows,
    "n_cols": MatrixRecord.n_cols,
}
ORDERS = ("asc", "desc")
MAX_CELLS = 100_000  # защита от слишком больших матриц (каждая ячейка — строка в БД)

DEFAULT_SETTINGS = {"eps": "1e-9", "page_size": "10", "sort_by": "id", "order": "asc"}

Data = Sequence[Sequence[float]]


# ----------------------------------------------------------------- матрицы
def _check_data(data: Data) -> Tuple[int, int]:
    """Проверить форму матрицы (logic.validate_matrix) и конечность чисел."""
    try:
        size = validate_matrix(data)
    except ValueError as err:
        raise InvalidDataError(str(err)) from err
    if size[0] * size[1] > MAX_CELLS:
        raise InvalidDataError(f"Матрица слишком велика: не более {MAX_CELLS} элементов.")
    if not all(math.isfinite(x) for row in data for x in row):
        raise InvalidDataError("Значения матрицы должны быть конечными числами.")
    return size


def _clean_name(name: str) -> str:
    name = (name or "").strip()
    if not name or len(name) > 100:
        raise InvalidDataError("Имя матрицы: от 1 до 100 символов.")
    return name


def _get_tags(session: Session, names: Sequence[str]) -> List[Tag]:
    """Найти теги по именам, недостающие создать. Имена приводятся к нижнему регистру."""
    result: List[Tag] = []
    for raw in dict.fromkeys(n.strip().lower() for n in names):
        if not raw or len(raw) > 50:
            raise InvalidDataError("Имя тега: от 1 до 50 символов.")
        tag = session.scalar(select(Tag).where(Tag.name == raw))
        result.append(tag if tag is not None else Tag(name=raw))
    return result


def _make_cells(data: Data) -> List[MatrixCell]:
    return [
        MatrixCell(row_idx=i, col_idx=j, value=float(x))
        for i, row in enumerate(data)
        for j, x in enumerate(row)
    ]


def _escape_like(text: str) -> str:
    """Экранировать символы %, _ и \\, чтобы поиск по имени был буквальным."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _clean_note(note: Optional[str]) -> Optional[str]:
    note = (note or "").strip()
    if len(note) > 200:
        raise InvalidDataError("Примечание: не более 200 символов.")
    return note or None


def _name_taken(session: Session, name: str, except_id: Optional[int] = None) -> bool:
    stmt = select(MatrixRecord.id).where(MatrixRecord.name == name)
    found = session.scalar(stmt)
    return found is not None and found != except_id


def create_matrix(
    session: Session, name: str, data: Data, tags: Sequence[str] = (), note: Optional[str] = None
) -> MatrixRecord:
    """Сохранить матрицу. Ошибки: InvalidDataError, DuplicateError."""
    name = _clean_name(name)
    n, m = _check_data(data)
    if _name_taken(session, name):
        raise DuplicateError(f"Матрица с именем «{name}» уже существует.")
    record = MatrixRecord(
        name=name, n_rows=n, n_cols=m, cells=_make_cells(data), note=_clean_note(note))
    record.tags = _get_tags(session, tags)
    session.add(record)
    session.commit()
    return record


def get_matrix(session: Session, matrix_id: int) -> MatrixRecord:
    """Получить матрицу по id. Ошибка: NotFoundError."""
    record = session.get(MatrixRecord, matrix_id)
    if record is None:
        raise NotFoundError(f"Матрица {matrix_id} не найдена.")
    return record


def matrix_data(record: MatrixRecord) -> List[List[float]]:
    """Собрать матрицу (список строк) из ячеек записи."""
    rows: List[List[float]] = [[0.0] * record.n_cols for _ in range(record.n_rows)]
    for cell in record.cells:
        rows[cell.row_idx][cell.col_idx] = cell.value
    return rows


def update_matrix(
    session: Session,
    matrix_id: int,
    name: Optional[str] = None,
    data: Optional[Data] = None,
    tags: Optional[Sequence[str]] = None,
    note: Optional[str] = None,
) -> MatrixRecord:
    """Изменить имя, данные, теги и/или примечание матрицы (None — не менять)."""
    record = get_matrix(session, matrix_id)
    if name is not None:
        name = _clean_name(name)
        if _name_taken(session, name, except_id=matrix_id):
            raise DuplicateError(f"Матрица с именем «{name}» уже существует.")
        record.name = name
    if data is not None:
        record.n_rows, record.n_cols = _check_data(data)
        record.cells.clear()
        session.flush()  # сначала удалить старые ячейки (уникальный ключ позиции)
        record.cells = _make_cells(data)
    if tags is not None:
        record.tags = _get_tags(session, tags)
    if note is not None:
        record.note = _clean_note(note)
    session.commit()
    return record


def delete_matrix(session: Session, matrix_id: int) -> None:
    """Удалить матрицу вместе с ячейками и анализами. Ошибка: NotFoundError."""
    session.delete(get_matrix(session, matrix_id))
    session.commit()


def list_matrices(
    session: Session,
    tag: Optional[str] = None,
    query: Optional[str] = None,
    sort_by: str = "id",
    order: str = "asc",
    limit: int = 10,
    offset: int = 0,
) -> Tuple[List[MatrixRecord], int]:
    """Список матриц с фильтром по тегу и части имени, сортировкой и страницами.

    Возвращает (записи страницы, общее число записей по фильтру).
    """
    if sort_by not in SORT_FIELDS or order not in ORDERS:
        raise InvalidDataError("Недопустимое поле или направление сортировки.")
    if limit < 1 or offset < 0:
        raise InvalidDataError("limit должен быть >= 1, offset >= 0.")
    stmt = select(MatrixRecord)
    if tag:
        stmt = stmt.join(MatrixRecord.tags).where(Tag.name == tag.strip().lower())
    if query:
        stmt = stmt.where(MatrixRecord.name.ilike(f"%{_escape_like(query)}%", escape="\\"))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    column = SORT_FIELDS[sort_by]
    stmt = stmt.order_by(column.desc() if order == "desc" else column.asc(), MatrixRecord.id)
    items = list(session.scalars(stmt.limit(limit).offset(offset)))
    return items, total


# ----------------------------------------------------------------- анализ
def run_analysis(session: Session, matrix_id: int, eps: Optional[float] = None) -> Analysis:
    """Выполнить три условия варианта 7 над сохранённой матрицей и сохранить результат.

    Если eps не задан, берётся значение из настроек пользователя.
    """
    record = get_matrix(session, matrix_id)
    if eps is None:
        eps = float(get_settings(session)["eps"])
    if not math.isfinite(eps) or eps < 0:
        raise InvalidDataError("eps должен быть конечным числом >= 0.")
    data = matrix_data(record)
    vectors = {
        "zero_columns": column_all_zero(data, eps),
        "descending_rows": row_descending(data, eps),
        "symmetric_rows": row_symmetric(data, eps),
    }
    analysis = Analysis(matrix_id=matrix_id, eps=eps)
    analysis.results = [
        VectorResult(kind=kind, position=pos, value=bool(val))
        for kind, values in vectors.items()
        for pos, val in enumerate(values)
    ]
    session.add(analysis)
    session.commit()
    return analysis


def analysis_vectors(analysis: Analysis) -> Dict[str, List[bool]]:
    """Собрать три вектора из сохранённых элементов результата."""
    out: Dict[str, List[bool]] = {
        "zero_columns": [], "descending_rows": [], "symmetric_rows": []}
    for item in analysis.results:
        out[item.kind].append(item.value)
    return out


def get_analysis(session: Session, analysis_id: int) -> Analysis:
    """Получить анализ по id. Ошибка: NotFoundError."""
    analysis = session.get(Analysis, analysis_id)
    if analysis is None:
        raise NotFoundError(f"Анализ {analysis_id} не найден.")
    return analysis


def list_analyses(session: Session, matrix_id: int) -> List[Analysis]:
    """Все анализы матрицы (от старых к новым)."""
    return list(get_matrix(session, matrix_id).analyses)


def count_analyses(session: Session) -> int:
    """Сколько анализов сохранено всего."""
    return session.scalar(select(func.count(Analysis.id))) or 0


def all_vector_values(session: Session) -> List[Dict[str, Any]]:
    """Все сохранённые элементы векторов (для аналитики): [{kind, value}, ...]."""
    rows = session.execute(select(VectorResult.kind, VectorResult.value))
    return [{"kind": kind, "value": bool(value)} for kind, value in rows]


# ----------------------------------------------------------------- настройки
def get_settings(session: Session) -> Dict[str, str]:
    """Настройки пользователя: значения по умолчанию, переопределённые сохранёнными."""
    stored = {row.key: row.value for row in session.scalars(select(Setting))}
    return {**DEFAULT_SETTINGS, **stored}


def _check_setting(key: str, value: str) -> None:
    if key not in DEFAULT_SETTINGS:
        raise InvalidDataError(f"Неизвестная настройка: {key}.")
    if key == "eps":
        number = float(value)
        if not math.isfinite(number) or number < 0:
            raise InvalidDataError("eps должен быть конечным числом >= 0.")
    elif key == "page_size":
        if not 1 <= int(value) <= 100:
            raise InvalidDataError("page_size: целое число от 1 до 100.")
    elif key == "sort_by" and value not in SORT_FIELDS:
        raise InvalidDataError("sort_by: " + ", ".join(SORT_FIELDS) + ".")
    elif key == "order" and value not in ORDERS:
        raise InvalidDataError("order: asc или desc.")


def set_setting(session: Session, key: str, value: Any) -> None:
    """Сохранить одну настройку (с проверкой допустимых значений)."""
    text = str(value)
    try:
        _check_setting(key, text)
    except ValueError as err:
        raise InvalidDataError(f"Недопустимое значение настройки {key}: {text}.") from err
    row = session.get(Setting, key)
    if row is None:
        session.add(Setting(key=key, value=text))
    else:
        row.value = text
    session.commit()


__all__ = [
    "DEFAULT_SETTINGS", "DuplicateError", "EPS", "MAX_CELLS", "NotFoundError", "SORT_FIELDS",
    "all_vector_values", "analysis_vectors", "count_analyses", "create_matrix",
    "delete_matrix", "get_analysis", "get_matrix", "get_settings", "list_analyses",
    "list_matrices", "matrix_data", "run_analysis", "set_setting", "update_matrix",
]
