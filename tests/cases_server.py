"""Тестовые случаи для REST-сервиса: заголовок Content-Length и тело запроса."""

from tests.cases import Case

PROBE = "tests.server_probe:status_for"

GROUPS = [
    ("server: размер и формат тела запроса", [
        Case("TC-R-01", "корректный запрос", PROBE, ("valid",), 200),
        Case("TC-R-02", "тело — не JSON", PROBE, ("invalid_json",), 400),
        Case("TC-R-03", "заголовок Content-Length отсутствует", PROBE,
             ("missing_length",), 400),
        Case("TC-R-04", "Content-Length не число", PROBE, ("non_int_length",), 400),
        Case("TC-R-05", "Content-Length = -1 (граница ниже 0)", PROBE,
             ("negative_length",), 400),
        Case("TC-R-06", "тело ровно 1 МиБ (верхняя граница включена)", PROBE,
             ("length_at_limit",), 400, "", "Content-Length = 1048576"),
        Case("TC-R-07", "Content-Length = 1 МиБ + 1", PROBE, ("length_over_limit",), 413),
        Case("TC-R-08", "целое число из 400 цифр в JSON", PROBE, ("huge_int_json",), 400),
    ]),
]
