import unittest

from matrix_lab import mapping
from matrix_lab.errors import InvalidDataError
from matrix_lab.models import ProcessingResult


class TestMatrixMapping(unittest.TestCase):
    def test_roundtrip(self):
        matrix = [[1.0, 2.0], [3.0, 4.5]]
        dto = mapping.matrix_to_dto(matrix)
        self.assertEqual(dto["matrix"]["rows"], 2)
        self.assertEqual(dto["matrix"]["cols"], 2)
        self.assertEqual(mapping.dto_to_matrix(dto), matrix)

    def test_ints_are_converted_to_float(self):
        dto = {"matrix": {"rows": 1, "cols": 2, "data": [[1, 2]]}}
        self.assertEqual(mapping.dto_to_matrix(dto), [[1.0, 2.0]])

    def test_bad_structures(self):
        bad = [
            None,
            [],
            {},
            {"matrix": []},
            {"matrix": {"rows": 0, "cols": 1, "data": []}},
            {"matrix": {"rows": True, "cols": 1, "data": [[1]]}},
            {"matrix": {"rows": 2, "cols": 1, "data": [[1]]}},
            {"matrix": {"rows": 1, "cols": 2, "data": [[1]]}},
            {"matrix": {"rows": 1, "cols": 1, "data": [["a"]]}},
            {"matrix": {"rows": 1, "cols": 1, "data": [[True]]}},
            {"matrix": {"rows": 1, "cols": 1, "data": [[float("nan")]]}},
            {"matrix": {"rows": 1, "cols": 1, "data": "x"}},
            {"matrix": {"rows": 1, "cols": 1, "data": [5]}},
        ]
        for dto in bad:
            with self.subTest(dto=dto):
                with self.assertRaises(InvalidDataError):
                    mapping.dto_to_matrix(dto)


class TestResultMapping(unittest.TestCase):
    def test_roundtrip_and_camel_case(self):
        result = ProcessingResult([True, False], [False], [True])
        dto = mapping.result_to_dto(result)
        self.assertEqual(dto["result"]["zeroColumns"], [True, False])
        self.assertEqual(dto["result"]["descendingRows"], [False])
        self.assertEqual(mapping.dto_to_result(dto), result)

    def test_zero_one_are_converted_to_bool(self):
        dto = {"result": {"zeroColumns": [1, 0], "descendingRows": [0], "symmetricRows": [1]}}
        result = mapping.dto_to_result(dto)
        self.assertEqual(result.zero_columns, [True, False])
        self.assertEqual(result.symmetric_rows, [True])

    def test_bad_results(self):
        bad = [
            None,
            {},
            {"result": {}},
            {"result": {"zeroColumns": "x", "descendingRows": [], "symmetricRows": []}},
            {"result": {"zeroColumns": [2], "descendingRows": [], "symmetricRows": []}},
            {"result": {"zeroColumns": ["a"], "descendingRows": [], "symmetricRows": []}},
        ]
        for dto in bad:
            with self.subTest(dto=dto):
                with self.assertRaises(InvalidDataError):
                    mapping.dto_to_result(dto)


if __name__ == "__main__":
    unittest.main()
