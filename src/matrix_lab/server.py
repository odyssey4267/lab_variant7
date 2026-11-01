"""Модуль обработки как REST-сервис (HTTP + JSON). Только стандартная библиотека.

Конечные точки:
    GET  /api/v1/health   -> {"status": "ok", "api_version": "1.0"}
    POST /api/v1/process  -> тело: JSON с матрицей, ответ: JSON с тремя векторами
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import mapping
from .errors import InvalidDataError
from .processing_module import process

API_PREFIX = "/api/v1"


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

    def do_GET(self):
        if self.path == f"{API_PREFIX}/health":
            self._send(200, {"status": "ok", "api_version": mapping.API_VERSION})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != f"{API_PREFIX}/process":
            self._send(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            matrix = mapping.dto_to_matrix(payload)
            result = process(matrix)
        except (ValueError, InvalidDataError) as err:  # ValueError включает ошибки JSON
            self._send(400, {"error": "invalid_data", "message": str(err)})
            return
        self._send(200, mapping.result_to_dto(result))


def make_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Создать (но не запускать) HTTP-сервер модуля обработки."""
    server = ThreadingHTTPServer((host, port), ProcessingHandler)
    server.daemon_threads = True
    return server
