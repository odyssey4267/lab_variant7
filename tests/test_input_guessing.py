"""Тесты ввода: предположение об ошибке."""

import pytest

from tests.cases import check_case
from tests.cases_io_guess import GROUPS

pytestmark = pytest.mark.blackbox

CASES = [case for _, group in GROUPS for case in group]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_input_guessing(case):
    check_case(case)
