"""REST API хранилища (FastAPI). Документация Swagger UI открывается по адресу /docs."""

from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from fastapi import APIRouter, Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .db import repository as repo
from .db.models import Analysis, MatrixRecord
from .db.session import init_db, make_engine, make_session_factory
from .errors import InvalidDataError
from .web_page import INDEX_HTML

API_PREFIX = "/api/v1"
DESCRIPTION = (
    "Хранилище матриц и результатов обработки (вариант 7: логические векторы по "
    "вещественной матрице n × m). Матрицы, теги, запуски анализа и настройки пользователя "
    "хранятся в SQLite через SQLAlchemy."
)


# ----------------------------------------------------------------- схемы
class MatrixIn(BaseModel):
    """Тело запроса: новая матрица."""

    name: str = Field(..., min_length=1, max_length=100, examples=["example1"])
    data: List[List[float]] = Field(..., examples=[[[3, 2, 0], [0, 5, 0]]])
    tags: List[str] = Field(default_factory=list, examples=[["demo"]])
    note: Optional[str] = Field(None, max_length=200)


class MatrixPatch(BaseModel):
    """Тело запроса: изменение матрицы (переданные поля заменяются)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    data: Optional[List[List[float]]] = None
    tags: Optional[List[str]] = None
    note: Optional[str] = Field(None, max_length=200)


class MatrixOut(BaseModel):
    """Матрица в ответе."""

    id: int
    name: str
    rows: int
    cols: int
    tags: List[str]
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    data: Optional[List[List[float]]] = None


class MatrixList(BaseModel):
    """Страница списка матриц."""

    total: int
    limit: int
    offset: int
    items: List[MatrixOut]


class AnalysisIn(BaseModel):
    """Параметры запуска анализа; eps не задан — берётся из настроек."""

    eps: Optional[float] = Field(None, ge=0, examples=[1e-9])


class AnalysisOut(BaseModel):
    """Результат анализа: три логических вектора."""

    id: int
    matrix_id: int
    eps: float
    created_at: Optional[datetime] = None
    zero_columns: List[bool]
    descending_rows: List[bool]
    symmetric_rows: List[bool]


class SettingsIO(BaseModel):
    """Настройки пользователя (интерфейс подстраивается под них)."""

    eps: Optional[float] = Field(None, ge=0)
    page_size: Optional[int] = Field(None, ge=1, le=100)
    sort_by: Optional[str] = None
    order: Optional[str] = None


# ----------------------------------------------------------------- преобразование
def matrix_dict(record: MatrixRecord, with_data: bool = True) -> Dict[str, Any]:
    """ORM-запись -> словарь для MatrixOut."""
    out: Dict[str, Any] = {
        "id": record.id,
        "name": record.name,
        "rows": record.n_rows,
        "cols": record.n_cols,
        "tags": sorted(tag.name for tag in record.tags),
        "note": record.note,
        "created_at": record.created_at,
    }
    if with_data:
        out["data"] = repo.matrix_data(record)
    return out


def analysis_dict(analysis: Analysis) -> Dict[str, Any]:
    """ORM-запись анализа -> словарь для AnalysisOut."""
    return {
        "id": analysis.id,
        "matrix_id": analysis.matrix_id,
        "eps": analysis.eps,
        "created_at": analysis.created_at,
        **repo.analysis_vectors(analysis),
    }


def _settings_out(session: Session) -> Dict[str, Any]:
    raw = repo.get_settings(session)
    return {
        "eps": float(raw["eps"]),
        "page_size": int(raw["page_size"]),
        "sort_by": raw["sort_by"],
        "order": raw["order"],
    }


# ----------------------------------------------------------------- приложение
def create_app(engine: Optional[Engine] = None, create_tables: bool = False) -> FastAPI:
    """Собрать приложение. create_tables=True создаёт таблицы без миграций (для тестов)."""
    engine = engine or make_engine()
    if create_tables:
        init_db(engine)
    factory = make_session_factory(engine)
    app = FastAPI(title="Matrix Vectors API", version="1.2.0", description=DESCRIPTION)

    def get_session() -> Iterator[Session]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    _add_error_handlers(app)
    app.include_router(_matrix_router(get_session))
    app.include_router(_analysis_router(get_session))
    app.include_router(_settings_router(get_session))

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> str:
        return INDEX_HTML

    @app.get(API_PREFIX + "/health", tags=["service"])
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    return app


def _add_error_handlers(app: FastAPI) -> None:
    def reply(status: int):
        def handler(_request: Request, exc: Exception) -> JSONResponse:
            return JSONResponse(status_code=status, content={"detail": str(exc)})
        return handler

    app.add_exception_handler(repo.NotFoundError, reply(404))
    app.add_exception_handler(repo.DuplicateError, reply(409))
    app.add_exception_handler(InvalidDataError, reply(422))


def _matrix_router(get_session) -> APIRouter:
    router = APIRouter(prefix=API_PREFIX + "/matrices", tags=["matrices"])

    @router.post("", response_model=MatrixOut, status_code=201, summary="Добавить матрицу")
    def create(body: MatrixIn, session: Session = Depends(get_session)):
        return matrix_dict(repo.create_matrix(
            session, body.name, body.data, body.tags, body.note))

    @router.get("", response_model=MatrixList, summary="Список матриц (фильтры и сортировка)")
    def list_all(
        tag: Optional[str] = Query(None, description="Фильтр по тегу"),
        q: Optional[str] = Query(None, description="Часть имени матрицы"),
        sort_by: Optional[str] = Query(None, description="id, name, created_at, n_rows, n_cols"),
        order: Optional[str] = Query(None, description="asc или desc"),
        limit: Optional[int] = Query(None, ge=1, le=100),
        offset: int = Query(0, ge=0),
        session: Session = Depends(get_session),
    ):
        prefs = _settings_out(session)  # значения по умолчанию берутся из настроек пользователя
        size = limit or prefs["page_size"]
        items, total = repo.list_matrices(
            session, tag, q, sort_by or prefs["sort_by"], order or prefs["order"], size, offset)
        return {"total": total, "limit": size, "offset": offset,
                "items": [matrix_dict(item, with_data=False) for item in items]}

    @router.get("/{matrix_id}", response_model=MatrixOut, summary="Получить матрицу")
    def read(matrix_id: int, session: Session = Depends(get_session)):
        return matrix_dict(repo.get_matrix(session, matrix_id))

    @router.put("/{matrix_id}", response_model=MatrixOut, summary="Изменить матрицу")
    def update(matrix_id: int, body: MatrixPatch, session: Session = Depends(get_session)):
        record = repo.update_matrix(
            session, matrix_id, body.name, body.data, body.tags, body.note)
        return matrix_dict(record)

    @router.delete("/{matrix_id}", status_code=204, summary="Удалить матрицу")
    def delete(matrix_id: int, session: Session = Depends(get_session)) -> None:
        repo.delete_matrix(session, matrix_id)

    return router


def _analysis_router(get_session) -> APIRouter:
    router = APIRouter(prefix=API_PREFIX, tags=["analysis"])

    @router.post("/matrices/{matrix_id}/analyses", response_model=AnalysisOut, status_code=201,
                 summary="Запустить обработку матрицы")
    def run(matrix_id: int, body: Optional[AnalysisIn] = None,
            session: Session = Depends(get_session)):
        eps = body.eps if body is not None else None
        return analysis_dict(repo.run_analysis(session, matrix_id, eps))

    @router.get("/matrices/{matrix_id}/analyses", response_model=List[AnalysisOut],
                summary="История запусков по матрице")
    def history(matrix_id: int, session: Session = Depends(get_session)):
        return [analysis_dict(item) for item in repo.list_analyses(session, matrix_id)]

    @router.get("/analyses/{analysis_id}", response_model=AnalysisOut,
                summary="Результат одного запуска")
    def one(analysis_id: int, session: Session = Depends(get_session)):
        return analysis_dict(repo.get_analysis(session, analysis_id))

    return router


def _settings_router(get_session) -> APIRouter:
    router = APIRouter(prefix=API_PREFIX + "/settings", tags=["settings"])

    @router.get("", response_model=SettingsIO, summary="Настройки пользователя")
    def read(session: Session = Depends(get_session)):
        return _settings_out(session)

    @router.put("", response_model=SettingsIO, summary="Сохранить настройки")
    def save(body: SettingsIO, session: Session = Depends(get_session)):
        for key, value in body.model_dump(exclude_none=True).items():
            repo.set_setting(session, key, value)
        return _settings_out(session)

    return router
