"""Тесты «чёрного ящика» для output_module.py."""

import pytest

from matrix_lab.models import Report
from matrix_lab.output_module import render
from tests.cases_output import GROUPS
from tests.cases import check_case

pytestmark = pytest.mark.blackbox

CASES = [case for _, group in GROUPS for case in group]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_numbers_boundaries(case):
    check_case(case)


def test_render_single_cell_report():
    report = Report([[0.0]], [True], [True], [True])
    text = render(report)
    assert text.splitlines()[0] == "Матрица:"
    assert text.count("-> столбцы: 1") == 1
    assert text.count("-> строки: 1") == 2


def test_render_does_not_round_values():
    report = Report([[1234567.0, 0.1234567891]], [False, False], [False], [False])
    assert "1234567  0.1234567891" in render(report)
