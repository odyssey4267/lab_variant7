"""Тесты REST-сервиса: предположение об ошибке и граничные значения заголовка."""

import pytest

from tests.cases import check_case
from tests.cases_server import GROUPS

pytestmark = pytest.mark.blackbox

CASES = [case for _, group in GROUPS for case in group]

@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_server_request_cases(case):
    check_case(case)
