"""Интеллектуальный анализ данных: статистика матрицы, прогноз и сводка по векторам.

Используются pandas, numpy и scikit-learn.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

Data = Sequence[Sequence[float]]


def matrix_statistics(data: Data) -> Dict[str, Any]:
    """Описательная статистика матрицы: общая, по столбцам и суммы по строкам."""
    values = np.asarray(data, dtype=float)
    if values.ndim != 2 or values.size == 0:
        raise ValueError("Ожидалась непустая двумерная матрица.")
    frame = pd.DataFrame(values)
    return {
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "std": float(values.std()),
        "min": float(values.min()),
        "max": float(values.max()),
        "column_means": [float(x) for x in frame.mean(axis=0)],
        "row_sums": [float(x) for x in frame.sum(axis=1)],
    }


def forecast_row(data: Data, row: int, steps: int = 3) -> Dict[str, Any]:
    """Прогноз продолжения строки матрицы линейной регрессией по номеру столбца."""
    if not 0 <= row < len(data):
        raise ValueError(f"Строки {row} нет в матрице.")
    if not 1 <= steps <= 20:
        raise ValueError("Число шагов прогноза: от 1 до 20.")
    y = np.asarray(data[row], dtype=float)
    if y.size < 2:
        raise ValueError("Для прогноза нужно не менее 2 элементов в строке.")
    x = np.arange(y.size).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    future = np.arange(y.size, y.size + steps).reshape(-1, 1)
    return {
        "row": row,
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "forecast": [float(v) for v in model.predict(future)],
    }


def vector_summary(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Сводка по всем сохранённым анализам: сколько элементов и какая доля True по видам."""
    if not records:
        return {}
    frame = pd.DataFrame(records)
    grouped = frame.groupby("kind")["value"].agg(["count", "mean"])
    return {
        str(kind): {"total": int(row["count"]), "true_share": round(float(row["mean"]), 4)}
        for kind, row in grouped.iterrows()
    }
