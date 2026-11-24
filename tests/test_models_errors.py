"""Тесты контрактов между модулями: models.py, errors.py, stubs.py."""

import dataclasses

import pytest

from matrix_lab import errors, stubs
from matrix_lab.models import ProcessingResult, Report

pytestmark = pytest.mark.blackbox

def test_processing_result_is_immutable():
    result = ProcessingResult([True], [True], [True])
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.zero_columns = []

def test_report_is_immutable():
    report = Report([[1.0]], [True], [True], [True])
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.matrix = []

@pytest.mark.parametrize("cls, code", [
    (errors.InvalidDataError, 1),
    (errors.ModuleUnavailableError, 2),
    (errors.ModuleTimeoutError, 3),
    (errors.VersionConflictError, 4),
])
def test_error_exit_codes(cls, code):
    assert cls.exit_code == code
    assert issubclass(cls, errors.IntegrationError)

def test_integration_error_default_code():
    assert errors.IntegrationError.exit_code == 1

def test_stubs_follow_the_contract():
    matrix = stubs.read_input_stub()
    result = stubs.process_stub(matrix)
    assert len(result.zero_columns) == len(matrix[0])
    assert len(result.descending_rows) == len(matrix)
    assert len(result.symmetric_rows) == len(matrix)
    assert "заглушка" in stubs.render_stub(Report(matrix, [], [], []))
