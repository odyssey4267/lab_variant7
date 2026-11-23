"""Низкоуровневые запросы к REST-сервису через сокет: крайние случаи протокола."""

import socket

from tests.http_helpers import running_server

TIMEOUT = 1.5
MAX_BODY = 1024 * 1024  # граница из спецификации: 1 МиБ

VALID = (b'{"api_version": "1.0", "matrix": {"rows": 1, "cols": 1, "data": [[0.0]]}}')
HUGE_INT = (b'{"api_version": "1.0", "matrix": {"rows": 1, "cols": 1, "data": [[' + b"9" * 400
            + b']]}}')

def _scenario(kind):
    """Вернуть (заголовки, тело) для вида запроса."""
    if kind == "valid":
        return [("Content-Length", len(VALID))], VALID
    if kind == "invalid_json":
        return [("Content-Length", 5)], b"{oops"
    if kind == "missing_length":
        return [], b"{}"
    if kind == "non_int_length":
        return [("Content-Length", "abc")], b""
    if kind == "negative_length":
        return [("Content-Length", -1)], b""
    if kind == "length_at_limit":
        head, tail = b'{"api_version": "1.0", "matrix": 1', b"}"
        body = head + b" " * (MAX_BODY - len(head) - len(tail)) + tail
        return [("Content-Length", len(body))], body
    if kind == "length_over_limit":
        return [("Content-Length", MAX_BODY + 1)], b"{}"
    if kind == "huge_int_json":
        return [("Content-Length", len(HUGE_INT))], HUGE_INT
    raise ValueError(kind)

def status_for(kind):
    """Отправить запрос вида kind и вернуть HTTP-статус, 'timeout' или 'no-response'."""
    headers, body = _scenario(kind)
    head = "POST /api/v1/process HTTP/1.1\r\nHost: test\r\n"
    head += "".join(f"{k}: {v}\r\n" for k, v in headers) + "\r\n"
    with running_server() as url:
        host, port = url.replace("http://", "").split(":")
        with socket.create_connection((host, int(port)), timeout=TIMEOUT) as sock:
            sock.sendall(head.encode("ascii") + body)
            try:
                data = sock.recv(4096)
            except socket.timeout:
                return "timeout"
    return int(data.split()[1]) if data else "no-response"
