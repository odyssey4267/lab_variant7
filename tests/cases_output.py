"""Тестовые случаи для output_module.py и format_vector: граничные длины списков."""

from tests.cases import Case

OUT = "matrix_lab.output_module"

GROUPS = [
    ("output_module._numbers", [
        Case("TC-O-01", "пустой вектор (длина 0)", f"{OUT}:_numbers", ([],), "нет"),
        Case("TC-O-02", "один элемент True (длина 1)", f"{OUT}:_numbers", ([True],), "1"),
        Case("TC-O-03", "один элемент False", f"{OUT}:_numbers", ([False],), "нет"),
        Case("TC-O-04", "True только в конце", f"{OUT}:_numbers",
             ([False, False, True],), "3"),
        Case("TC-O-05", "все True: номера через запятую", f"{OUT}:_numbers",
             ([True, True, True],), "1, 2, 3"),
    ]),
]
