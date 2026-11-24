"""Тесты, добавленные по итогам мутационной проверки (docs/test_review.md).

Каждый тест закрывает место, где «выживал» мутант: тесты проходили, хотя код был изменён.
"""

import builtins
import inspect
import urllib.request

import pytest

from matrix_lab import http_client, io_utils, mapping, server, stubs
from matrix_lab.models import ProcessingResult, Report
from tests.http_helpers import running_server

def test_default_timeout_is_five_seconds():
    assert http_client.DEFAULT_TIMEOUT == 5.0

def test_parse_errors_name_the_row_and_the_counts():
    with pytest.raises(ValueError, match="получено 1"):
        io_utils.parse_matrix(["2 1", "1"])
    with pytest.raises(ValueError, match="Строка 1: ожидалось 2 чисел, получено 1"):
        io_utils.parse_matrix(["1 2", "1"])
    with pytest.raises(ValueError, match="Строка 2: не удалось"):
        io_utils.parse_matrix(["2 1", "1", "x"])

def test_console_input_repeats_until_row_is_valid(monkeypatch, capsys):
    answers = iter(["1 2", "1", "nan 1", "7 8"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
    assert io_utils.read_matrix_console() == [[7.0, 8.0]]
    assert "Ошибка" in capsys.readouterr().out

def test_empty_matrix_has_zero_columns_in_dto():
    assert mapping.matrix_to_dto([])["matrix"]["cols"] == 0

def test_health_endpoint_answers_200():
    with running_server() as url:
        with urllib.request.urlopen(url + "/api/v1/health", timeout=2) as response:
            assert response.status == 200

def test_server_defaults():
    params = inspect.signature(server.make_server).parameters
    assert params["port"].default == 8080
    assert params["delay"].default == 0.0

def test_stub_data_and_shape():
    assert stubs.read_input_stub() == [[0.0, 1.0], [0.0, 2.0]]
    assert stubs.process_stub([[1.0, 2.0, 3.0]]) == ProcessingResult(
        [False, False, False], [False], [False])
    assert "1x3" in stubs.render_stub(Report([[1.0, 2.0, 3.0]], [], [], []))
