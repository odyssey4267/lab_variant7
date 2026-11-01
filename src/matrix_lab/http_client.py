"""Клиент модуля обработки: вызов REST-сервиса из управляющего модуля.

Исключительные ситуации преобразуются в типизированные ошибки интеграции:
    недоступность модуля -> ModuleUnavailableError
    таймаут              -> ModuleTimeoutError
    HTTP 400 / мусор     -> InvalidDataError
    HTTP 409 / версия    -> VersionConflictError
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from . import mapping
from .errors import (
    IntegrationError,
    InvalidDataError,
    ModuleTimeoutError,
    ModuleUnavailableError,
    VersionConflictError,
)
from .models import Matrix, ProcessingResult

DEFAULT_URL = "http://127.0.0.1:8080"
DEFAULT_TIMEOUT = 5.0
TIMEOUT_ERRORS = (socket.timeout, TimeoutError)
NETWORK_ERRORS = (urllib.error.URLError, ConnectionError) + TIMEOUT_ERRORS


def _server_message(err: urllib.error.HTTPError) -> str:
    """Достать текст ошибки из JSON-ответа сервиса (если он есть)."""
    try:
        return str(json.loads(err.read().decode("utf-8")).get("message", err.reason))
    except (ValueError, OSError):
        return str(err.reason)


def _http_error(err: urllib.error.HTTPError) -> IntegrationError:
    """HTTP-статус ошибки -> исключение интеграции."""
    message = _server_message(err)
    if err.code == 400:
        return InvalidDataError(message)
    if err.code == 409:
        return VersionConflictError(message)
    return IntegrationError(f"Сервис вернул HTTP {err.code}: {message}")


def _network_error(err: Exception, timeout: float) -> IntegrationError:
    """Сетевой сбой -> таймаут или недоступность модуля."""
    reason = err.reason if isinstance(err, urllib.error.URLError) else err
    if isinstance(reason, TIMEOUT_ERRORS):
        return ModuleTimeoutError(f"Сервис не ответил за {timeout} с.")
    if isinstance(err, urllib.error.URLError):
        return ModuleUnavailableError(f"Сервис недоступен: {err.reason}")
    return ModuleUnavailableError(f"Соединение разорвано: {err}")


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
        raise _http_error(err) from err
    except NETWORK_ERRORS as err:
        raise _network_error(err, timeout) from err
    except ValueError as err:
        raise InvalidDataError(f"Некорректный ответ сервиса: {err}") from err
    mapping.check_version(body)
    return mapping.dto_to_result(body)
