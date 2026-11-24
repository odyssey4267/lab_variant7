"""Регрессионный набор: по одному тесту на каждый найденный и исправленный дефект.

Запуск:  pytest -m regression
"""

import math

import pytest

from matrix_lab import http_client, mapping
from matrix_lab.errors import InvalidDataError
from matrix_lab.io_utils import format_matrix, parse_matrix, read_matrix_file
from tests.server_probe import status_for

pytestmark = pytest.mark.regression

def test_bug1_format_keeps_precision():
    text = format_matrix([[1234567.0, 0.1234567891, -0.0]])
    assert text == "1234567  0.1234567891  0"
    assert math.isclose(float(text.split()[1]), 0.1234567891, rel_tol=0, abs_tol=0)

def test_bug2_huge_integer_is_rejected_not_crashing():
    payload = {"matrix": {"rows": 1, "cols": 1, "data": [[10 ** 400]]}}
    with pytest.raises(InvalidDataError, match="слишком велико"):
        mapping.dto_to_matrix(payload)
    assert status_for("huge_int_json") == 400

def test_bug3_negative_content_length_gives_400():
    assert status_for("negative_length") == 400

def test_bug4_oversized_body_gives_413_and_limit_is_inclusive():
    assert status_for("length_over_limit") == 413
    assert status_for("length_at_limit") == 400

@pytest.mark.parametrize("url", ["localhost:8080", "", "http://", "ftp://h:1"])
def test_bug5_bad_service_address(url):
    with pytest.raises(InvalidDataError, match="адрес"):
        http_client.process_remote([[1.0]], url, 1.0)

@pytest.mark.parametrize("timeout", [-1, 0, float("nan")])
def test_bug6_bad_timeout(timeout):
    with pytest.raises(InvalidDataError, match="Таймаут"):
        http_client.process_remote([[1.0]], "http://127.0.0.1:1", timeout)

def test_bug7_underscore_in_number_is_rejected():
    with pytest.raises(ValueError, match="не удалось прочитать число"):
        parse_matrix(["1 2", "1_0 2"])

@pytest.mark.parametrize("header", ["² 1", "٣ ١"])
def test_bug8_non_ascii_digits_in_header(header):
    with pytest.raises(ValueError, match="Первая строка"):
        parse_matrix([header, "1"])

def test_bug9_utf8_bom_file_is_read(tmp_path):
    path = tmp_path / "bom.txt"
    path.write_bytes("\ufeff1 2\n5 6\n".encode("utf-8"))
    assert read_matrix_file(str(path)) == [[5.0, 6.0]]
