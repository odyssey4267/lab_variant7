"""Маршруты интеллектуального анализа (уровень 3): статистика, прогноз, сводка."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .analytics import forecast_row, matrix_statistics, vector_summary
from .db import repository as repo
from .errors import InvalidDataError

PREFIX = "/api/v1"


def build_router(get_session) -> APIRouter:
    """Создать маршрутизатор; get_session — зависимость, выдающая сессию БД."""
    router = APIRouter(prefix=PREFIX, tags=["analytics"])

    @router.get("/matrices/{matrix_id}/statistics", summary="Статистика матрицы")
    def statistics(matrix_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
        record = repo.get_matrix(session, matrix_id)
        return matrix_statistics(repo.matrix_data(record))

    @router.get("/matrices/{matrix_id}/forecast", summary="Прогноз продолжения строки")
    def forecast(
        matrix_id: int,
        row: int = Query(0, ge=0),
        steps: int = Query(3, ge=1, le=20),
        session: Session = Depends(get_session),
    ) -> Dict[str, Any]:
        record = repo.get_matrix(session, matrix_id)
        try:
            return forecast_row(repo.matrix_data(record), row, steps)
        except ValueError as err:
            raise InvalidDataError(str(err)) from err

    @router.get("/analytics/summary", summary="Сводка по всем сохранённым анализам")
    def summary(session: Session = Depends(get_session)) -> Dict[str, Any]:
        return {
            "analyses": repo.count_analyses(session),
            "vectors": vector_summary(repo.all_vector_values(session)),
        }

    return router
