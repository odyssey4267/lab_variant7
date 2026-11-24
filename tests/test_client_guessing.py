"""Тесты http_client.py: предположение об ошибке в аргументах вызова."""

import pytest

from tests.cases import check_case
from tests.cases_client import GROUPS

pytestmark = pytest.mark.blackbox

CASES = [case for _, group in GROUPS for case in group]

@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_client_argument_cases(case):
    check_case(case)
