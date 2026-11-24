"""Тесты «чёрного ящика» для logic.py: анализ граничных значений."""

import pytest

from tests.cases import DESCENDING, SYMMETRIC, VALIDATE, ZERO_COLUMNS, check_case

pytestmark = pytest.mark.blackbox

ALL = VALIDATE + ZERO_COLUMNS + DESCENDING + SYMMETRIC


@pytest.mark.parametrize("case", ALL, ids=lambda c: c.id)
def test_logic_boundaries(case):
    check_case(case)
