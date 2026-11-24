"""Тесты «чёрного ящика» для mapping.py: границы и предположение об ошибке."""

import pytest

from tests.cases_mapping import TO_MATRIX, TO_RESULT, VERSION
from tests.cases import check_case

pytestmark = pytest.mark.blackbox


@pytest.mark.parametrize("case", TO_MATRIX + VERSION + TO_RESULT, ids=lambda c: c.id)
def test_mapping_cases(case):
    check_case(case)
