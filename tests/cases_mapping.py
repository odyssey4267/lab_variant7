"""Тестовые случаи для mapping.py: граничные значения и предположение об ошибке."""

from matrix_lab.errors import InvalidDataError, VersionConflictError
from matrix_lab.models import ProcessingResult
from tests.cases import Case

MAP = "matrix_lab.mapping"


def dto(rows=1, cols=1, data=((0,),)):
    return {"matrix": {"rows": rows, "cols": cols, "data": [list(r) for r in data]}}


BIG_INT = 10 ** 400

TO_MATRIX = [
    Case("TC-M-01", "минимальная матрица 1 × 1", f"{MAP}:dto_to_matrix", (dto(),), [[0.0]]),
    Case("TC-M-02", "rows = 0 (граница rows-1)", f"{MAP}:dto_to_matrix",
         (dto(rows=0, data=()),), InvalidDataError, "rows"),
    Case("TC-M-03", "cols = 0 (граница cols-1)", f"{MAP}:dto_to_matrix",
         (dto(cols=0, data=((),)),), InvalidDataError, "cols"),
    Case("TC-M-04", "rows = true (булево вместо целого)", f"{MAP}:dto_to_matrix",
         (dto(rows=True),), InvalidDataError, "rows"),
    Case("TC-M-05", "строк в data на одну меньше", f"{MAP}:dto_to_matrix",
         (dto(rows=2, data=((0,),)),), InvalidDataError, "2 строк"),
    Case("TC-M-06", "строк в data на одну больше", f"{MAP}:dto_to_matrix",
         (dto(rows=1, data=((0,), (0,))),), InvalidDataError, "1 строк"),
    Case("TC-M-07", "в строке на одно число меньше", f"{MAP}:dto_to_matrix",
         (dto(cols=2, data=((0,),)),), InvalidDataError, "Строка 1"),
    Case("TC-M-08", "в строке на одно число больше", f"{MAP}:dto_to_matrix",
         (dto(cols=1, data=((0, 0),)),), InvalidDataError, "Строка 1"),
    Case("TC-M-09", "наибольшее конечное float", f"{MAP}:dto_to_matrix",
         (dto(data=((1.7976931348623157e308,),)),), [[1.7976931348623157e308]]),
    Case("TC-M-10", "целое число 10**400 (больше float)", f"{MAP}:dto_to_matrix",
         (dto(data=((BIG_INT,),)),), InvalidDataError, "слишком велико",
         "dto с элементом 10**400"),
    Case("TC-M-11", "целое число 10**309 (первое степенное за границей float)",
         f"{MAP}:dto_to_matrix", (dto(data=((10 ** 309,),)),), InvalidDataError,
         "слишком велико", "dto с элементом 10**309"),
    Case("TC-M-12", "значение nan", f"{MAP}:dto_to_matrix",
         (dto(data=((float("nan"),),)),), InvalidDataError, "конечными"),
    Case("TC-M-13", "значение inf", f"{MAP}:dto_to_matrix",
         (dto(data=((float("inf"),),)),), InvalidDataError, "конечными"),
    Case("TC-M-14", "значение — строка", f"{MAP}:dto_to_matrix",
         (dto(data=(("1",),)),), InvalidDataError, "конечными"),
    Case("TC-M-15", "значение — null", f"{MAP}:dto_to_matrix",
         (dto(data=((None,),)),), InvalidDataError, "конечными"),
]

VERSION = [
    Case("TC-M-16", "версия 1.0 (совпадает)", f"{MAP}:check_version",
         ({"api_version": "1.0"},), None),
    Case("TC-M-17", "версия 1.99 (та же старшая)", f"{MAP}:check_version",
         ({"api_version": "1.99"},), None),
    Case("TC-M-18", "версия 2.0 (старшая +1)", f"{MAP}:check_version",
         ({"api_version": "2.0"},), VersionConflictError, "несовместима"),
    Case("TC-M-19", "версия 0.9 (старшая -1)", f"{MAP}:check_version",
         ({"api_version": "0.9"},), VersionConflictError, "несовместима"),
    Case("TC-M-20", "версия не указана", f"{MAP}:check_version", ({},),
         VersionConflictError, "несовместима"),
]

TO_RESULT = [
    Case("TC-M-21", "0 и 1 приводятся к bool", f"{MAP}:dto_to_result",
         ({"result": {"zeroColumns": [0, 1], "descendingRows": [1], "symmetricRows": [0]}},),
         ProcessingResult([False, True], [True], [False])),
    Case("TC-M-22", "значение 2 (граница выше 1)", f"{MAP}:dto_to_result",
         ({"result": {"zeroColumns": [2], "descendingRows": [], "symmetricRows": []}},),
         InvalidDataError, "true/false"),
    Case("TC-M-23", "значение -1 (граница ниже 0)", f"{MAP}:dto_to_result",
         ({"result": {"zeroColumns": [-1], "descendingRows": [], "symmetricRows": []}},),
         InvalidDataError, "true/false"),
    Case("TC-M-24", "нет одного из полей", f"{MAP}:dto_to_result",
         ({"result": {"zeroColumns": []}},), InvalidDataError, "descendingRows"),
]

GROUPS = [
    ("mapping.dto_to_matrix", TO_MATRIX),
    ("mapping.check_version", VERSION),
    ("mapping.dto_to_result", TO_RESULT),
]
