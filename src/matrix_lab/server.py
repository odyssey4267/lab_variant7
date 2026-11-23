"""Модуль обработки как REST-сервис (HTTP + JSON). Только стандартная библиотека.

Конечные точки:
    GET  /api/v1/health   -> {"status": "ok", "api_version": "1.0"}
    POST /api/v1/process  -> тело: JSON с матрицей, ответ: JSON с тремя векторами
"""

from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import mapping
from .errors import InvalidDataError, VersionConflictError
from .processing_module import process

API_PREFIX = "/api/v1"
MAX_BODY = 1024 * 1024  # предельный размер тела запроса, байт

class _PayloadTooLarge(Exception):
    """Заявленный размер тела запроса превышает MAX_BODY."""

class ProcessingHandler(BaseHTTPRequestHandler):
    server_version = "MatrixService/1.0"

    def log_message(self, format, *args):  # noqa: A002 - сигнатура задана базовым классом
        """Не засорять консоль строками журнала доступа."""

    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # клиент уже закрыл соединение

    def _read_body(self) -> bytes:
        """Прочитать тело запроса, предварительно проверив заголовок Content-Length."""
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            raise InvalidDataError("Некорректный заголовок Content-Length.") from None
        if length < 0:
            raise InvalidDataError("Content-Length не может быть отрицательным.")
        if length > MAX_BODY:
            raise _PayloadTooLarge(f"Тело запроса больше {MAX_BODY} байт.")
        return self.rfile.read(length)

    def do_GET(self):
        if self.path == f"{API_PREFIX}/health":
            self._send(200, {"status": "ok", "api_version": mapping.API_VERSION})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != f"{API_PREFIX}/process":
            self._send(404, {"error": "not_found"})
            return
        time.sleep(self.server.delay)  # имитация медленного модуля (для проверки таймаута)
        try:
            payload = json.loads(self._read_body().decode("utf-8"))
            mapping.check_version(payload)
            matrix = mapping.dto_to_matrix(payload)
            result = process(matrix)
        except _PayloadTooLarge as err:
            self._send(413, {"error": "payload_too_large", "message": str(err)})
            return
        except VersionConflictError as err:
            self._send(409, {"error": "version_conflict", "message": str(err)})
            return
        except (ValueError, InvalidDataError) as err:  # ValueError включает ошибки JSON
            self._send(400, {"error": "invalid_data", "message": str(err)})
            return
        self._send(200, mapping.result_to_dto(result))

def make_server(host: str = "127.0.0.1", port: int = 8080,
                delay: float = 0.0) -> ThreadingHTTPServer:
    """Создать (но не запускать) HTTP-сервер модуля обработки.

    delay — искусственная задержка ответа в секундах (для проверки таймаута).
    """
    server = ThreadingHTTPServer((host, port), ProcessingHandler)
    server.daemon_threads = True
    server.delay = delay
    return server
