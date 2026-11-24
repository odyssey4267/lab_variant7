"""Интеграционные сценарии IT-01 … IT-09: взаимодействие модулей системы."""

import contextlib
import io
import json
import os
from unittest import mock

import pytest

import main as main_module
from matrix_lab import app, http_client, input_module, mapping, output_module, processing_module
from matrix_lab import stubs
from tests.http_helpers import running_server

pytestmark = pytest.mark.integration

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
FILES = [os.path.join(EXAMPLES, f"input{i}.txt") for i in (1, 2, 3)]


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main_module.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_it01_file_to_report_direct():
    """IT-01: файл -> ввод -> обработка -> вывод (прямые вызовы)."""
    code, out, _ = run_main([FILES[0]])
    assert code == 0
    assert "[True, False, True, False]  -> столбцы: 1, 3" in out


@pytest.mark.parametrize("path", FILES, ids=["input1", "input2", "input3"])
def test_it02_rest_equals_direct(path):
    """IT-02: результат через REST совпадает с прямым вызовом (все примеры)."""
    _, direct, _ = run_main([path])
    with running_server() as url:
        code, remote, _ = run_main([path, "--transport", "http", "--url", url])
    assert code == 0
    assert remote == direct


def test_it03_bad_file_gives_code_1(tmp_path):
    """IT-03: файл неверного формата -> InvalidDataError, код 1."""
    bad = tmp_path / "bad.txt"
    bad.write_text("2 2\n1 2\n3\n", encoding="utf-8")
    code, _, err = run_main([str(bad)])
    assert code == 1
    assert "InvalidDataError" in err


def test_it04_service_down_gives_code_2():
    """IT-04: сервис недоступен -> ModuleUnavailableError, код 2."""
    code, _, err = run_main([FILES[0], "--transport", "http", "--url", "http://nonexistent.invalid",
                             "--timeout", "5"])
    assert code == 2
    assert "ModuleUnavailableError" in err


def test_it05_slow_service_gives_code_3():
    """IT-05: сервис отвечает слишком медленно -> ModuleTimeoutError, код 3."""
    with running_server(delay=0.5) as url:
        code, _, err = run_main([FILES[0], "--transport", "http", "--url", url,
                                 "--timeout", "0.1"])
    assert code == 3
    assert "ModuleTimeoutError" in err


def test_it06_version_conflict_gives_code_4():
    """IT-06: несовместимая версия API -> VersionConflictError, код 4."""
    old = mapping.matrix_to_dto([[1.0]])
    old["api_version"] = "2.0"
    with running_server() as url:
        with mock.patch("matrix_lab.http_client.mapping.matrix_to_dto", return_value=old):
            code, _, err = run_main([FILES[0], "--transport", "http", "--url", url])
    assert code == 4
    assert "VersionConflictError" in err


@pytest.mark.parametrize("path", FILES, ids=["input1", "input2", "input3"])
def test_it07_mapping_roundtrip_through_json_text(path):
    """IT-07: матрица -> DTO -> текст JSON -> DTO -> матрица без потерь."""
    matrix = input_module.read_matrix(path)
    text = json.dumps(mapping.matrix_to_dto(matrix))
    assert mapping.dto_to_matrix(json.loads(text)) == matrix


def test_it08_stub_replaced_by_real_module():
    """IT-08: нисходящая интеграция: реальные ввод и обработка + заглушка вывода."""
    out = []
    code = app.run(lambda: input_module.read_matrix(FILES[0]), processing_module.process,
                   stubs.render_stub, write=out.append)
    assert code == 0
    assert out == ["[заглушка] вывод для матрицы 3x4"]


def test_it09_all_modules_with_real_http_client():
    """IT-09: app.run с настоящими модулями и удалённой обработкой."""
    out = []
    with running_server() as url:
        code = app.run(lambda: input_module.read_matrix(FILES[1]),
                       lambda m: http_client.process_remote(m, url, 2.0),
                       output_module.render, write=out.append)
    assert code == 0
    assert "[False, True, True, True]  -> строки: 2, 3, 4" in out[0]
