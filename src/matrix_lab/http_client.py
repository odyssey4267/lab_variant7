"""Клиент модуля обработки: вызов REST-сервиса из управляющего модуля."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from . import mapping
from .errors import IntegrationError, InvalidDataError
from .models import Matrix, ProcessingResult

DEFAULT_URL = "http://127.0.0.1:8080"
DEFAULT_TIMEOUT = 5.0


def process_remote(matrix: Matrix, base_url: str = DEFAULT_URL,
                   timeout: float = DEFAULT_TIMEOUT) -> ProcessingResult:
    """Отправить матрицу удалённому модулю обработки и получить результат."""
    try:
        payload = json.dumps(mapping.matrix_to_dto(matrix), allow_nan=False).encode("utf-8")
    except ValueError as err:
        raise InvalidDataError(f"Матрицу нельзя передать в JSON: {err}") from err
    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/v1/process",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:  # подкласс URLError — обрабатывается первым
        raise IntegrationError(f"Сервис вернул HTTP {err.code}.") from err
    except (urllib.error.URLError, OSError) as err:
        raise IntegrationError(f"Сервис недоступен: {err}") from err
    except ValueError as err:
        raise InvalidDataError(f"Некорректный ответ сервиса: {err}") from err
    return mapping.dto_to_result(body)
