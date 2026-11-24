"""Тестовые случаи для http_client.py: аргументы адреса и таймаута."""

from matrix_lab.errors import InvalidDataError, ModuleUnavailableError
from tests.cases import Case

CLIENT = "matrix_lab.http_client:process_remote"
M = [[1.0]]
OK_URL = "http://127.0.0.1:1"

GROUPS = [
    ("http_client.process_remote: адрес и таймаут", [
        Case("TC-C-01", "адрес без схемы: localhost:8080", CLIENT, (M, "localhost:8080"),
             InvalidDataError, "адрес"),
        Case("TC-C-02", "пустой адрес", CLIENT, (M, ""), InvalidDataError, "адрес"),
        Case("TC-C-03", "адрес без хоста: http://", CLIENT, (M, "http://"),
             InvalidDataError, "адрес"),
        Case("TC-C-04", "неподдерживаемая схема ftp", CLIENT, (M, "ftp://127.0.0.1:8080"),
             InvalidDataError, "адрес"),
        Case("TC-C-05", "таймаут = -1 (меньше нуля)", CLIENT, (M, OK_URL, -1),
             InvalidDataError, "Таймаут"),
        Case("TC-C-06", "таймаут = 0 (граница)", CLIENT, (M, OK_URL, 0),
             InvalidDataError, "Таймаут"),
        Case("TC-C-07", "таймаут = nan", CLIENT, (M, OK_URL, float("nan")),
             InvalidDataError, "Таймаут"),
        Case("TC-C-08", "корректные аргументы, порт закрыт", CLIENT, (M, OK_URL, 5.0),
             ModuleUnavailableError, "недоступен"),
    ]),
]
