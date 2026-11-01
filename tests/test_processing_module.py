import os
import unittest

from matrix_lab import input_module, processing_module
from matrix_lab.errors import InvalidDataError

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")


class TestProcessingModule(unittest.TestCase):
    def test_all_three_vectors(self):
        result = processing_module.process([[0, 5, 0], [3, 2, 1], [1, 2, 1]])
        self.assertEqual(result.zero_columns, [False, False, False])
        self.assertEqual(result.descending_rows, [False, True, False])
        self.assertEqual(result.symmetric_rows, [True, False, True])

    def test_one_by_one_matrix(self):
        result = processing_module.process([[0]])
        self.assertEqual(result.zero_columns, [True])
        self.assertEqual(result.descending_rows, [True])
        self.assertEqual(result.symmetric_rows, [True])

    def test_ragged_matrix_is_invalid_data(self):
        with self.assertRaises(InvalidDataError):
            processing_module.process([[1, 2], [3]])

    def test_empty_matrix_is_invalid_data(self):
        with self.assertRaises(InvalidDataError):
            processing_module.process([])


class TestInputToProcessingIntegration(unittest.TestCase):
    """Интеграция двух модулей: данные из модуля ввода передаются в модуль обработки."""

    def test_example_1(self):
        matrix = input_module.read_matrix(os.path.join(EXAMPLES, "input1.txt"))
        result = processing_module.process(matrix)
        self.assertEqual(result.zero_columns, [True, False, True, False])

    def test_example_2(self):
        matrix = input_module.read_matrix(os.path.join(EXAMPLES, "input2.txt"))
        result = processing_module.process(matrix)
        self.assertEqual(result.descending_rows, [True, False, True, False])
        self.assertEqual(result.symmetric_rows, [False, True, True, True])

    def test_example_3_decimal_comma(self):
        matrix = input_module.read_matrix(os.path.join(EXAMPLES, "input3.txt"))
        result = processing_module.process(matrix)
        self.assertEqual(result.symmetric_rows, [True, False])


if __name__ == "__main__":
    unittest.main()
